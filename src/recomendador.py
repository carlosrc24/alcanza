"""Motor de recomendación: perfil → tres tarjetas (trabajo directo, salto corto, salto con
formación), cada una con su puntuación desglosada (contribuciones w·z) y su «por qué».

La puntuación es una suma ponderada de indicadores normalizados en [0, 1]; los pesos los
elige la persona. Ninguna IA interviene en la puntuación.
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .config import PROCESSED, REF, UMBRALES_T

PESOS_DEFECTO = {"competencia": 3, "volumen": 2, "tendencia": 1, "salario": 1, "conciliacion": 1, "esfuerzo": 1}
ETIQUETAS = {
    "competencia": "Puestos por demandante",
    "volumen": "Puestos alcanzables",
    "tendencia": "Tendencia del sector",
    "salario": "Salario esperado",
    "conciliacion": "Conciliación (escuela infantil)",
    "esfuerzo": "Poco esfuerzo formativo",
}
TIPOS_FORMACION = ["fp", "fp_ies", "formacion_empleo", "adultos"]


def cargar(carpeta=PROCESSED) -> dict:
    s = {"ine": str, "origen": str, "destino": str}
    D = {
        "mun": pd.read_csv(carpeta / "municipios.csv", dtype=s),
        "ind": pd.read_csv(carpeta / "indicadores_municipio_sector.csv", dtype=s),
        "dest": pd.read_csv(carpeta / "oportunidad_destino.csv", dtype=s),
        "tt": pd.read_csv(carpeta / "tiempos_tp.csv", dtype=s),
        "rec": pd.read_csv(carpeta / "recursos.csv", dtype=s),
        "sec": pd.read_csv(carpeta / "sectores.csv"),
        "bal": pd.read_csv(carpeta / "balance_empleo.csv", dtype=s),
        "par": pd.read_csv(carpeta / "parados_municipio_sector.csv", dtype=s),
        "ocu": pd.read_csv(REF / "ocupaciones.csv"),
    }
    D["sal"] = pd.read_csv(carpeta / "salario_ocupacion.csv").set_index("gran_grupo_cno")
    D["nom"] = D["mun"].set_index("ine")["nombre"].to_dict()
    D["nom_sec"] = D["sec"].set_index("sector")["nombre_sector"].to_dict()
    # rango percentil de puestos_por_competidor y puestos_alcanzables por (T, modo), entre todos
    # los municipios y sectores: hace comparables sectores y orígenes
    ind = D["ind"][D["ind"]["sector"] != "TOT"].copy()
    g = ind.groupby(["T", "modo"])
    ind["z_competencia"] = g["puestos_por_competidor"].rank(pct=True)
    ind["z_volumen"] = g["puestos_alcanzables"].rank(pct=True)
    D["indz"] = ind.set_index(["ine", "sector", "T", "modo"])
    D["ei_mun"] = D["rec"][D["rec"]["tipo"] == "escuela_infantil"].groupby("ine").size()
    return D


def nombre_municipio(nombre: str) -> str:
    """«Rozas de Madrid (Las)» → «Las Rozas de Madrid»."""
    if nombre.endswith(")") and "(" in nombre:
        base, art = nombre[:-1].split(" (", 1)
        return f"{art} {base}"
    return nombre


def snap_T(T: int) -> int:
    return min(UMBRALES_T, key=lambda u: abs(u - T))


@dataclass
class Tarjeta:
    tipo: str
    ocupacion_id: str
    ocupacion: str
    sector: str
    nombre_sector: str
    puntuacion: float
    contribuciones: dict
    indicadores: dict
    destinos: pd.DataFrame
    por_que: str
    formacion: str = ""
    centros_formacion: pd.DataFrame = field(default_factory=pd.DataFrame)


def tiempos_desde(D, ine: str, modo: str) -> pd.Series:
    col = "min_tp" if modo == "tp" else "min_coche"
    t = D["tt"][D["tt"]["origen"] == ine].set_index("destino")[col]
    return t


def mejores_destinos(D, ine, sector, T, modo, n=3) -> pd.DataFrame:
    t = tiempos_desde(D, ine, modo)
    d = D["dest"][(D["dest"]["sector"] == sector) & (D["dest"]["T"] == T)].set_index("ine")
    d = d.join(t.rename("minutos"), how="inner")
    d = d[(d["minutos"] <= T) & (d["puestos"] >= 50)].copy()
    if d.empty:
        return d.reset_index()
    # equilibrio entre poca competencia en destino y volumen de puestos
    d["orden"] = 0.6 * d["puestos_por_competidor_destino"].rank(pct=True) + 0.4 * d["puestos"].rank(pct=True)
    d = d.sort_values("orden", ascending=False).head(n).reset_index()
    d["nombre"] = d["ine"].map(D["nom"]).map(nombre_municipio)
    d["ei"] = d["ine"].map(D["ei_mun"]).fillna(0).astype(int)
    return d


def centros_cercanos(D, ine, modo, tipos, max_min=30, n=5) -> pd.DataFrame:
    t = tiempos_desde(D, ine, modo)
    r = D["rec"][D["rec"]["tipo"].isin(tipos)].copy()
    r["minutos"] = r["ine"].map(t)
    r = r[r["minutos"] <= max_min]
    r["municipio"] = r["ine"].map(D["nom"]).map(nombre_municipio)
    prioridad = {"fp": 0, "formacion_empleo": 1, "fp_ies": 2, "adultos": 3, "escuela_infantil": 0}
    r["p"] = r["tipo"].map(prioridad)
    return r.sort_values(["minutos", "p"]).head(n)


def _z_tendencia(var):
    return float(np.clip((0 if pd.isna(var) else var) / 0.10 * 0.5 + 0.5, 0, 1))


def salario(D, cno11) -> float | None:
    g = int(str(cno11)[0])
    return float(D["sal"].loc[g, "salario_medio"]) if g in D["sal"].index else None


def _z_salario(D, cno11):
    """Salario del gran grupo CNO escalado entre 14.000 € (0) y 40.000 € (1)."""
    v = salario(D, cno11)
    return 0.5 if v is None else float(np.clip((v - 14000) / 26000, 0, 1))


def _fmt(x, dec=0):
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def puntuar(D, ocu_row, ine, T, modo, hijo, pesos, tipo):
    s = ocu_row["sector"]
    fila = D["indz"].loc[(ine, s, T, modo)]
    dest = mejores_destinos(D, ine, s, T, modo)
    ei_origen = int(D["ei_mun"].get(ine, 0))
    ei_dest = int(dest["ei"].sum()) if len(dest) else 0
    z = {
        "competencia": float(fila["z_competencia"]),
        "volumen": float(fila["z_volumen"]),
        "tendencia": _z_tendencia(fila["var_interanual"]),
        "salario": _z_salario(D, ocu_row["cno11"]),
        "conciliacion": float(min(1.0, (ei_origen + ei_dest) / 15)) if hijo else 0.0,
        "esfuerzo": {"directo": 1.0, "salto_corto": 0.8, "salto_formacion": 0.2}[tipo],
    }
    w = {k: (pesos.get(k, 0) if (k != "conciliacion" or hijo) else 0) for k in z}
    tw = sum(w.values()) or 1
    contrib = {k: w[k] * z[k] / tw for k in z}
    return sum(contrib.values()), contrib, fila, dest


def explicar(D, tipo, ocu_row, ine, T, modo, fila, dest, hijo):
    origen = nombre_municipio(D["nom"][ine])
    sec = D["nom_sec"][ocu_row["sector"]].split(" (")[0].lower()
    medio = "en transporte público" if modo == "tp" else "en coche"
    ppc = fila["puestos_por_competidor"]
    rel = fila["indice_relativo"]
    comp = "más" if rel >= 1 else "menos"
    partes = [
        f"Desde {origen} llegas {medio} en ≤{T} min a unos {_fmt(fila['puestos_alcanzables'])} puestos de "
        f"{sec} en {int(fila['municipios_alcanzables'])} municipios. "
        f"Por cada parado del sector que también llega hay {_fmt(ppc, 1)} puestos "
        f"({_fmt(abs(rel), 1)} veces la media regional: {comp} oportunidades que la media)."
    ]
    if not pd.isna(fila["var_interanual"]):
        v = fila["var_interanual"] * 100
        partes.append(f"El empleo del sector a tu alcance {'creció' if v >= 0 else 'cayó'} un {_fmt(abs(v), 1)} % "
                      f"en el último año.")
    if len(dest):
        d0 = dest.iloc[0]
        partes.append(f"El mejor destino es {d0['nombre']} ({int(d0['minutos'])} min).")
    if tipo == "salto_corto":
        partes.append("Es una ocupación cercana a la tuya: compartes buena parte de las competencias y no necesitas "
                      "formación previa.")
    if tipo == "salto_formacion":
        partes.append(f"Requiere: {ocu_row['formacion_requerida_origen']} ({ocu_row['duracion_origen']}).")
    if hijo and len(dest):
        partes.append(f"Hay {int(D['ei_mun'].get(ine, 0))} escuelas infantiles en {origen} y "
                      f"{int(dest['ei'].sum())} en los destinos propuestos.")
    return " ".join(partes)


def recomendar(D, ocupacion_id, ine, coche=False, hijo=False, formacion=True, T=45, pesos=None):
    pesos = {**PESOS_DEFECTO, **(pesos or {})}
    T = snap_T(T)
    modo = "coche" if coche else "tp"
    ocu = D["ocu"].set_index("id")
    yo = ocu.loc[ocupacion_id]
    tarjetas = []

    def hacer(tipo, oid, extra=None):
        r = ocu.loc[oid].copy()
        r["formacion_requerida_origen"] = yo["formacion_requerida"]
        r["duracion_origen"] = yo["duracion_formacion"]
        p, c, fila, dest = puntuar(D, r, ine, T, modo, hijo, pesos, tipo)
        t = Tarjeta(tipo=tipo, ocupacion_id=oid, ocupacion=r["ocupacion"], sector=r["sector"],
                    nombre_sector=D["nom_sec"][r["sector"]], puntuacion=p, contribuciones=c,
                    indicadores=fila.to_dict(), destinos=dest,
                    por_que=explicar(D, tipo, r, ine, T, modo, fila, dest, hijo))
        return t

    tarjetas.append(hacer("directo", ocupacion_id))
    cortos = [hacer("salto_corto", o) for o in str(yo["saltos_cortos"]).split("|") if o in ocu.index]
    if cortos:
        tarjetas.append(max(cortos, key=lambda t: t.puntuacion))
    if isinstance(yo["salto_formacion"], str) and yo["salto_formacion"] in ocu.index:
        t = hacer("salto_formacion", yo["salto_formacion"])
        t.formacion = yo["formacion_requerida"]
        t.centros_formacion = centros_cercanos(D, ine, modo, TIPOS_FORMACION)
        tarjetas.append(t)
    return {"T": T, "modo": modo, "tarjetas": tarjetas, "alternativas_cortas": cortos,
            "formacion_activa": formacion}


if __name__ == "__main__":
    D = cargar()
    r = recomendar(D, "aux_admin", "28106", coche=False, hijo=True, T=45)
    for t in r["tarjetas"]:
        print(f"[{t.tipo}] {t.ocupacion} · {t.nombre_sector} · {t.puntuacion:.2f}")
        print("   ", t.por_que)
        print("   ", t.destinos[["nombre", "minutos", "puestos", "puestos_por_competidor_destino"]].to_dict("records"))
