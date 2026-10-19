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
    _cargar_cp(D, carpeta, ind)
    return D


RADIO_EI_CP_KM = 2.0  # escuelas infantiles «cerca de casa» en los ejemplos por código postal


def _cargar_cp(D, carpeta, ind):
    """Ejemplos de origen por código postal en Madrid capital (src/cp.py), en tablas aparte: no se
    mezclan con las municipales (desiertos, simulador y conservación del 2SFCA no cambian)."""
    D["cp"] = pd.DataFrame()
    if not all((carpeta / f).exists() for f in ("cp_ejemplos.csv", "tiempos_cp.csv", "indicadores_cp_sector.csv")):
        return
    s = {"cp": str, "ine": str, "origen": str, "destino": str}
    D["cp"] = pd.read_csv(carpeta / "cp_ejemplos.csv", dtype=s).set_index("ine")
    D["tt_cp"] = pd.read_csv(carpeta / "tiempos_cp.csv", dtype=s)
    icp = pd.read_csv(carpeta / "indicadores_cp_sector.csv", dtype=s)
    icp = icp[icp["sector"] != "TOT"].copy()
    # mismo rango percentil que los municipios, frente a la distribución municipal (sin re-ordenarla)
    for col, z in (("puestos_por_competidor", "z_competencia"), ("puestos_alcanzables", "z_volumen")):
        ref = {k: np.sort(g[col].to_numpy()) for k, g in ind.groupby(["T", "modo"])}
        icp[z] = [np.searchsorted(ref[(T, m)], v, side="right") / len(ref[(T, m)])
                  for T, m, v in zip(icp["T"], icp["modo"], icp[col])]
    D["indz_cp"] = icp.set_index(["origen", "sector", "T", "modo"])
    ei = D["rec"][D["rec"]["tipo"] == "escuela_infantil"]
    D["ei_cp"] = {o: int((_km(r["lat"], r["lon"], ei["lat"].astype(float), ei["lon"].astype(float))
                          <= RADIO_EI_CP_KM).sum()) for o, r in D["cp"].iterrows()}


def _km(lat, lon, lats, lons):
    dy = (lats - lat) * 111.2
    dx = (lons - lon) * 111.2 * np.cos(np.radians(lat))
    return np.sqrt(dx ** 2 + dy ** 2)


def es_cp(D, o) -> bool:
    return len(D["cp"]) > 0 and o in D["cp"].index


def origen_de(D, ine, cp=None) -> str:
    """Origen del cálculo: el ejemplo de código postal si existe y vives en Madrid; si no, el municipio."""
    o = f"CP{cp}" if cp else None
    return o if (o and ine == "28079" and es_cp(D, o)) else ine


def nombre_origen(D, o) -> str:
    if es_cp(D, o):
        r = D["cp"].loc[o]
        return f"{r['barrio']} ({r['cp']})"
    return nombre_municipio(D["nom"][o])


def ei_origen(D, o) -> int:
    return D["ei_cp"][o] if es_cp(D, o) else int(D["ei_mun"].get(o, 0))


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
    resumen: str = ""
    centros_formacion: pd.DataFrame = field(default_factory=pd.DataFrame)


def tiempos_desde(D, ine: str, modo: str) -> pd.Series:
    col = "min_tp" if modo == "tp" else "min_coche"
    tt = D["tt_cp"] if es_cp(D, ine) else D["tt"]
    t = tt[tt["origen"] == ine].set_index("destino")[col]
    return t


def destinos(D, o, sector, T, modo) -> pd.DataFrame:
    """Oportunidad en cada destino (oportunidad_destino.csv). Con un barrio de ejemplo como origen, en los
    destinos a los que llega el barrio y no el núcleo de Madrid compiten también los parados de Madrid
    (la misma corrección que src/cp.py; si no, esos destinos repartirían sus puestos entre muy pocos)."""
    d = D["dest"][(D["dest"]["sector"] == sector) & (D["dest"]["T"] == T) & (D["dest"]["modo"] == modo)].set_index("ine")
    if es_cp(D, o):
        par = D["par"][D["par"]["ine"] == "28079"]
        u_mad = par["parados"].sum() if sector == "TOT" else par.loc[par["sector"] == sector, "parados"].sum()
        nuevo = (tiempos_desde(D, o, modo).reindex(d.index) <= T) & (tiempos_desde(D, "28079", modo).reindex(d.index) > T)
        d = d.copy()
        d.loc[nuevo, "puestos_por_competidor_destino"] = (
            d.loc[nuevo, "puestos"] / np.maximum(d.loc[nuevo, "competidores_que_llegan"] + u_mad, 1)).round(3)
    return d


def mejores_destinos(D, ine, sector, T, modo, n=3) -> pd.DataFrame:
    t = tiempos_desde(D, ine, modo)
    d = destinos(D, ine, sector, T, modo)
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
    fila = (D["indz_cp"] if es_cp(D, ine) else D["indz"]).loc[(ine, s, T, modo)]
    dest = mejores_destinos(D, ine, s, T, modo)
    ei_dest = int(dest["ei"].sum()) if len(dest) else 0
    z = {
        "competencia": float(fila["z_competencia"]),
        "volumen": float(fila["z_volumen"]),
        "tendencia": _z_tendencia(fila["var_interanual"]),
        "salario": _z_salario(D, ocu_row["cno11"]),
        "conciliacion": float(min(1.0, (ei_origen(D, ine) + ei_dest) / 15)) if hijo else 0.0,
        "esfuerzo": {"directo": 1.0, "salto_corto": 0.8, "salto_formacion": 0.2}[tipo],
    }
    w = {k: (pesos.get(k, 0) if (k != "conciliacion" or hijo) else 0) for k in z}
    tw = sum(w.values()) or 1
    contrib = {k: w[k] * z[k] / tw for k in z}
    return sum(contrib.values()), contrib, fila, dest


def explicar(D, tipo, ocu_row, ine, T, modo, fila, dest, hijo):
    origen = nombre_origen(D, ine)
    sec = D["nom_sec"][ocu_row["sector"]].split(" (")[0].lower()
    medio = "en transporte público" if modo == "tp" else "en coche"
    ppc = fila["puestos_por_competidor"]
    rel = fila["indice_relativo"]
    comp = "más" if rel >= 1 else "menos"
    partes = [
        f"Desde {origen} llegas {medio} en ≤{T} min a unos {_fmt(fila['puestos_alcanzables'])} puestos de "
        f"{sec} en {int(fila['municipios_alcanzables'])} "
        f"{'municipio' if int(fila['municipios_alcanzables']) == 1 else 'municipios'}. "
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
        cerca = f"a menos de {_fmt(RADIO_EI_CP_KM)} km de {origen}" if es_cp(D, ine) else f"en {origen}"
        partes.append(f"Hay {ei_origen(D, ine)} escuelas infantiles {cerca} y "
                      f"{int(dest['ei'].sum())} en los destinos propuestos.")
    return " ".join(partes)


def resumir(D, t, base, yo) -> str:
    """Frase corta y específica de cada camino, comparada con la ocupación actual."""
    i, b = t.indicadores, base.indicadores
    ppc = _fmt(i["puestos_por_competidor"], 1)
    d0 = t.destinos.iloc[0]["nombre"] if len(t.destinos) else None
    if t.tipo == "directo":
        rel = i["indice_relativo"]
        frente = ("la media regional" if 0.9 <= rel <= 1.1 else
                  f"{_fmt(rel, 1)} veces la media regional" if rel > 1.1 else
                  f"un {_fmt((1 - rel) * 100)} % menos que la media regional")
        txt = (f"{_fmt(i['puestos_alcanzables'])} puestos de tu sector a tu alcance, {ppc} por cada demandante "
               f"({frente}).")
        return txt + (f" Donde mejor: {d0}." if d0 else "")
    sal_t = salario(D, D["ocu"].set_index("id").loc[t.ocupacion_id, "cno11"])
    sal_b = salario(D, yo["cno11"])
    dif_sal = (sal_t - sal_b) if sal_t and sal_b else 0
    if t.tipo == "salto_corto":
        mejor = i["puestos_por_competidor"] / max(b["puestos_por_competidor"], 1e-9)
        txt = (f"Usa casi todo lo que ya sabes y no pide formación. {ppc} puestos por demandante"
               + (f" (×{_fmt(mejor, 1)} que en tu ocupación)." if t.sector != base.sector else "."))
        return txt + (f" Donde mejor: {d0}." if d0 else "")
    txt = f"Tras formarte ({t.formacion.split(' o ')[0]}, {yo['duracion_formacion']})"
    if dif_sal > 500:
        txt += f" el salario medio de referencia sube unos {_fmt(dif_sal / 1000, 1)} k€/año."
    else:
        txt += f" accedes a {_fmt(i['puestos_alcanzables'])} puestos con {ppc} por demandante."
    n = len(t.centros_formacion)
    if n:
        c0 = t.centros_formacion.iloc[0]
        txt += f" Centro de formación más cercano: {c0['municipio']} ({int(c0['minutos'])} min)."
    return txt


def recomendar(D, ocupacion_id, ine, coche=False, hijo=False, formacion=True, T=45, pesos=None, cp=None):
    pesos = {**PESOS_DEFECTO, **(pesos or {})}
    ine = origen_de(D, ine, cp)  # con código postal de ejemplo, los tiempos salen de su barrio
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
    base = tarjetas[0]
    cortos = [hacer("salto_corto", o) for o in str(yo["saltos_cortos"]).split("|") if o in ocu.index]
    if cortos:
        tarjetas.append(max(cortos, key=lambda t: t.puntuacion))
    if isinstance(yo["salto_formacion"], str) and yo["salto_formacion"] in ocu.index:
        t = hacer("salto_formacion", yo["salto_formacion"])
        t.formacion = yo["formacion_requerida"]
        t.centros_formacion = centros_cercanos(D, ine, modo, TIPOS_FORMACION)
        tarjetas.append(t)
    for t in tarjetas:
        t.resumen = resumir(D, t, base, yo)
    return {"T": T, "modo": modo, "origen": ine, "tarjetas": tarjetas, "alternativas_cortas": cortos,
            "formacion_activa": formacion}


if __name__ == "__main__":
    D = cargar()
    r = recomendar(D, "aux_admin", "28106", coche=False, hijo=True, T=45)
    for t in r["tarjetas"]:
        print(f"[{t.tipo}] {t.ocupacion} · {t.nombre_sector} · {t.puntuacion:.2f}")
        print("   ", t.por_que)
        print("   ", t.destinos[["nombre", "minutos", "puestos", "puestos_por_competidor_destino"]].to_dict("records"))
