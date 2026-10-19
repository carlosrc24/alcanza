"""Ejemplos de origen por código postal dentro de Madrid capital (solo unos pocos, preestablecidos).

El origen de Madrid es el punto central de todas sus paradas; para estos ejemplos el viaje sale de una
estación de Metro del barrio (GTFS de Metro del Consorcio). Los tiempos se calculan con r5py igual que
los municipales (mismos GTFS, OSM, día y franja 7-9 h, mediana).

A = Σ_j R_j · [t_cp,j ≤ T], con los R_j = puestos_j / parados que llegan del modelo municipal, salvo en un
caso: si el barrio llega a j y el núcleo de Madrid no, los parados de Madrid se suman a los competidores de j
(sus vecinos también llegarían). Sin esto, un destino al que «no llega nadie de Madrid» (Pozuelo desde el
núcleo, 56 min) repartiría sus puestos entre muy pocos y el indicador se inflaría (×5 en Moncloa a 45 min).
Es la opción prudente: la competencia puede quedar algo sobrestimada, nunca infravalorada.

Convenciones:
- Madrid como destino: 10 min, como cualquier viaje dentro del propio municipio (Madrid es un único
  destino en su núcleo; con r5py hasta ese punto, alguien de Vallecas «no llegaría» a Madrid).
- Destinos con horarios incompletos en la fuente: el tiempo de la fila municipal de Madrid (estimado).

    python -m src.cp            # r5py (~8 GB de memoria) + indicadores → data/processed/
    python -m src.cp --solo-indicadores
"""
import argparse
import zipfile

import numpy as np
import pandas as pd

from . import datos, tiempos
from .config import FACTOR_RODEO, PROCESSED, SECTORES, T_INTRA_MIN, UMBRALES_T, VEL_COCHE_KMH
from .gtfs import INTERIM
from .indicadores import MODOS

MADRID = "28079"
# código postal → (barrio, stop_id de la estación de referencia en el GTFS de Metro del Consorcio)
EJEMPLOS = {
    "28013": ("Sol", "par_4_12"),
    "28010": ("Chamberí", "par_4_8"),
    "28008": ("Moncloa-Argüelles", "par_4_54"),
    "28018": ("Puente de Vallecas", "par_4_19"),
    "28031": ("Villa de Vallecas", "par_4_26"),
}


def puntos() -> pd.DataFrame:
    import geopandas as gpd

    with zipfile.ZipFile(INTERIM / "gtfs_metro.zip") as z:
        s = pd.read_csv(z.open("stops.txt"), dtype=str, encoding_errors="replace").set_index("stop_id")
    filas = [{"ine": f"CP{cp}", "cp": cp, "barrio": b, "estacion": s.loc[sid, "stop_name"].title(),
              "lat": float(s.loc[sid, "stop_lat"]), "lon": float(s.loc[sid, "stop_lon"])}
             for cp, (b, sid) in EJEMPLOS.items()]
    p = pd.DataFrame(filas)
    xy = gpd.GeoSeries(gpd.points_from_xy(p.lon, p.lat), crs=4326).to_crs(25830)
    p["x"], p["y"] = xy.x.round(0), xy.y.round(0)
    return p


def calcular_tiempos(p: pd.DataFrame, max_memory="8G") -> pd.DataFrame:
    m = pd.read_csv(PROCESSED / "municipios.csv", dtype={"ine": str})
    ext = pd.concat([m, p[["ine", "lat", "lon", "x", "y"]]], ignore_index=True)
    tp = tiempos.tiempos_r5py(ext, origenes=list(p["ine"]), max_memory=max_memory)
    coche = tiempos.tiempos_coche(ext)
    df = coche.merge(tp, on=["origen", "destino"], how="left")
    df = df[df["origen"].isin(p["ine"]) & df["destino"].isin(m["ine"])].copy()
    df["metodo_tp"] = "r5py_gtfs_osm_p50_7a9h"
    # destinos con horarios incompletos en la fuente: tiempo de la fila municipal de Madrid
    mad = pd.read_csv(PROCESSED / "tiempos_tp.csv", dtype={"origen": str, "destino": str})
    mad = mad[mad["origen"] == MADRID].set_index("destino")
    h = pd.read_csv(PROCESSED / "huecos_gtfs.csv", dtype={"ine": str})
    hueco = df["destino"].isin(set(h.loc[h["hueco_gtfs"], "ine"]))
    df.loc[hueco, "min_tp"] = df.loc[hueco, "destino"].map(mad["min_tp"])
    df.loc[hueco, "metodo_tp"] = df.loc[hueco, "destino"].map(mad["metodo_tp"])
    a_madrid = df["destino"] == MADRID
    df.loc[a_madrid, ["min_tp", "min_coche"]] = T_INTRA_MIN  # convención: dentro del propio municipio
    df["accesible_tp"] = df["min_tp"].notna()
    df["min_tp"] = df["min_tp"].fillna(tiempos.MAX_MIN + 1)
    df["cp"] = df["origen"].str[2:]
    return df[["cp", "origen", "destino", "min_coche", "min_tp", "metodo_tp", "accesible_tp"]]


def calcular_indicadores(tt: pd.DataFrame) -> pd.DataFrame:
    """A = Σ_j R_j·[t ≤ T] con los R_j municipales (oportunidad_destino.csv), corregidos (ver arriba)."""
    dest = pd.read_csv(PROCESSED / "oportunidad_destino.csv", dtype={"ine": str})
    mad = pd.read_csv(PROCESSED / "tiempos_tp.csv", dtype={"origen": str, "destino": str})
    mad = mad[mad["origen"] == MADRID].set_index("destino")
    par = pd.read_csv(PROCESSED / "parados_municipio_sector.csv", dtype={"ine": str})
    u_mad = par[par["ine"] == MADRID].set_index("sector")["parados"].to_dict()
    u_mad["TOT"] = sum(u_mad.values())
    _, serie = datos.construir_puestos()
    anio = int(serie["anio"].max())
    prev = serie[serie["anio"] == anio - 1]
    p0 = {s: prev[prev["sector"] == s].set_index("ine")["puestos"] for s in SECTORES}
    p0["TOT"] = prev.groupby("ine")["puestos"].sum()
    # ratio regional (puestos / parados del sector) = A / índice relativo de cualquier fila municipal
    ind_m = pd.read_csv(PROCESSED / "indicadores_municipio_sector.csv", dtype={"ine": str})
    ind_m = ind_m[ind_m["indice_relativo"] > 0]
    ratio = (ind_m["puestos_por_competidor"] / ind_m["indice_relativo"]).groupby(ind_m["sector"]).median().to_dict()
    filas = []
    for (cp, origen), t in tt.groupby(["cp", "origen"]):
        t = t.set_index("destino")
        for (s, T, modo), d in dest.groupby(["sector", "T", "modo"]):
            d = d.set_index("ine")
            llega = t[MODOS[modo]].reindex(d.index) <= T
            # destinos a los que llega el barrio pero no el núcleo de Madrid: compiten también sus parados
            nuevo = llega & (mad[MODOS[modo]].reindex(d.index) > T)
            R_j = np.where(nuevo, d["puestos"] / np.maximum(d["competidores_que_llegan"] + u_mad[s], 1),
                           d["puestos_por_competidor_destino"])
            alc, A = d.loc[llega, "puestos"].sum(), R_j[llega.to_numpy()].sum()
            alc0 = p0[s].reindex(d.index[llega]).fillna(0).sum()
            var = alc / alc0 - 1 if alc0 > 0 else np.nan
            filas.append((origen, cp, s, T, modo, alc, alc / A if A > 0 else 0.0, A, A / ratio[s], var,
                          int(llega.sum())))
    ind = pd.DataFrame(filas, columns=["origen", "cp", "sector", "T", "modo", "puestos_alcanzables", "competidores",
                                       "puestos_por_competidor", "indice_relativo", "var_interanual",
                                       "municipios_alcanzables"])
    ind["tendencia"] = np.select([ind["var_interanual"] > 0.02, ind["var_interanual"] < -0.02],
                                 ["sube", "baja"], "estable")
    ind.loc[ind["var_interanual"].isna(), "tendencia"] = "sin datos"
    return ind.round({"puestos_alcanzables": 0, "competidores": 0, "puestos_por_competidor": 3,
                      "indice_relativo": 3, "var_interanual": 4})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo-indicadores", action="store_true")
    ap.add_argument("--max-memory", default="8G")
    a = ap.parse_args()
    p = puntos()
    p.to_csv(PROCESSED / "cp_ejemplos.csv", index=False)
    ft = PROCESSED / "tiempos_cp.csv"
    if not a.solo_indicadores:
        calcular_tiempos(p, a.max_memory).to_csv(ft, index=False)
    tt = pd.read_csv(ft, dtype={"cp": str, "origen": str, "destino": str})
    calcular_indicadores(tt).to_csv(PROCESSED / "indicadores_cp_sector.csv", index=False)
    print(p.to_string())
