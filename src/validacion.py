"""Validación externa de los tiempos y del indicador.

1. Tiempos: se comparan con los viajes reales casa → trabajo en transporte público de la
   Encuesta Domiciliaria de Movilidad 2018 (salida entre 6:00 y 9:59, entre municipios
   distintos). Duración declarada = hora de llegada − hora de salida; mediana ponderada por el
   elevador de la encuesta en cada par origen-destino con ≥ 5 viajes.
2. Indicador: correlación (Spearman) entre el acceso al empleo y la tasa de paro municipal.
   Parte de la relación con el índice relativo es mecánica (los parados del municipio cuentan
   como competidores), por eso se da también con los puestos alcanzables, que no usan el paro.
3. Robustez: el índice con umbral duro (t ≤ T) frente a un 2SFCA con decaimiento gaussiano.

    python -m src.validacion
"""
import json

import numpy as np
import pandas as pd
from scipy import stats

from .config import PROCESSED, RAW
from . import simulador as S

MODOS_TP = range(1, 7)   # Cercanías, bus interurbano, bus urbano, Metro, Metro Ligero, EMT
MIN_VIAJES = 5


def _hm(x):
    return (x // 100) * 60 + x % 100


def viajes_edm() -> pd.DataFrame:
    f = sorted(RAW.glob("edm2018_viajes__*.xlsx"))[-1]
    v = pd.read_excel(f, sheet_name="VIAJES", usecols=[
        "VORI", "VDES", "VORIHORAINI", "VDESHORAFIN", "VORIZT1259", "VDESZT1259", "MODO_PRIORITARIO", "ELE_G_POND_ESC2"])
    v = v[(v["VORI"] == 1) & (v["VDES"] == 2) & v["MODO_PRIORITARIO"].isin(MODOS_TP)
          & v["VORIHORAINI"].between(600, 959)].copy()
    v["min"] = _hm(v["VDESHORAFIN"]) - _hm(v["VORIHORAINI"])
    v = v[v["min"].between(1, 240)]
    # las zonas ZT1259 empiezan por el código INE de 3 dígitos del municipio
    v["origen"] = "28" + v["VORIZT1259"].astype(str).str[:3]
    v["destino"] = "28" + v["VDESZT1259"].astype(str).str[:3]
    return v[v["origen"] != v["destino"]]


def _mediana_ponderada(g):
    g = g.sort_values("min")
    c = g["ELE_G_POND_ESC2"].cumsum()
    return g["min"][c >= c.iloc[-1] / 2].iloc[0]


def validar_tiempos() -> tuple[pd.DataFrame, dict]:
    v = viajes_edm()
    a = (v.groupby(["origen", "destino"])
         .apply(lambda g: pd.Series({"min_edm": _mediana_ponderada(g), "viajes_edm": len(g)}), include_groups=False)
         .reset_index())
    a = a[a["viajes_edm"] >= MIN_VIAJES]
    t = pd.read_csv(PROCESSED / "tiempos_tp.csv", dtype={"origen": str, "destino": str})
    m = a.merge(t[["origen", "destino", "min_tp", "metodo_tp"]], on=["origen", "destino"])
    m["diferencia_min"] = m["min_tp"] - m["min_edm"]
    m["con_madrid"] = (m["origen"] == S.MADRID) | (m["destino"] == S.MADRID)
    x = m[m["metodo_tp"] == "r5py_gtfs_osm_p50_7a9h"]
    if len(x) < 3:  # tiempos del plan C: no hay nada que validar
        return m.round(1), {"pares": 0}
    e = x["diferencia_min"]
    res = {"pares": int(len(x)), "viajes": int(x["viajes_edm"].sum()),
           "sesgo_mediano_min": float(e.median()), "error_medio_abs_min": round(float(e.abs().mean()), 1),
           "pct_dentro_15min": round(float((e.abs() <= 15).mean()), 3),
           "spearman": round(float(stats.spearmanr(x["min_tp"], x["min_edm"])[0]), 3),
           "pct_dentro_15min_sin_madrid": round(float((x.loc[~x["con_madrid"], "diferencia_min"].abs() <= 15).mean()), 3),
           "pares_sin_madrid": int((~x["con_madrid"]).sum())}
    return m.round(1), res


def validar_indicador(D, hueco: set) -> dict:
    mun = D["mun"].set_index("ine")
    U = D["par"].groupby("ine")["parados"].sum()
    out = {}
    for T in (30, 45, 60, 75):
        x = D["ind"][(D["ind"]["sector"] == "TOT") & (D["ind"]["T"] == T) & (D["ind"]["modo"] == "tp")].set_index("ine")
        df = pd.DataFrame({"acc": x["indice_relativo"], "alc": x["puestos_alcanzables"],
                           "tasa": U / mun["poblacion"], "pob": mun["poblacion"]}).dropna()
        df = df[~df.index.isin(hueco) & (df["pob"] >= 2000)]
        out[str(T)] = {"municipios": int(len(df)),
                       "spearman_indice_paro": round(float(stats.spearmanr(df["acc"], df["tasa"])[0]), 3),
                       "spearman_puestos_paro": round(float(stats.spearmanr(df["alc"], df["tasa"])[0]), 3)}
    return out


def robustez(D, T: int = 60) -> dict:
    ids, tt, P, U, _ = S.datos_sector(D, "TOT", T)
    A = S.accesibilidad(tt <= T, P, U)
    ok = U >= 50
    out = {}
    for d0 in (45, 60, 75):
        W = np.where(tt <= d0, (np.exp(-0.5 * (tt / d0) ** 2) - np.exp(-0.5)) / (1 - np.exp(-0.5)), 0)
        Ag = W @ (P / np.maximum(U @ W, 1.0))
        out[f"gaussiano_d0_{d0}"] = round(float(stats.spearmanr(A[ok], Ag[ok])[0]), 3)
    return {"T_referencia": T, "spearman_umbral_vs_decaimiento": out}


def construir():
    from . import recomendador as R
    D = R.cargar()
    h = pd.read_csv(PROCESSED / "huecos_gtfs.csv", dtype={"ine": str})
    hueco = set(h.loc[h["hueco_gtfs"], "ine"])
    pares, res_t = validar_tiempos()
    nom = D["mun"].set_index("ine")["nombre"]
    pares.insert(2, "nombre_origen", pares["origen"].map(nom))
    pares.insert(3, "nombre_destino", pares["destino"].map(nom))
    pares.to_csv(PROCESSED / "validacion_tiempos_edm.csv", index=False)
    resumen = {"tiempos_vs_edm2018": res_t, "indicador_vs_tasa_paro": validar_indicador(D, hueco),
               "robustez": robustez(D)}
    (PROCESSED / "validacion.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    return resumen


if __name__ == "__main__":
    print(json.dumps(construir(), ensure_ascii=False, indent=2))
