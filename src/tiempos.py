"""Matrices de tiempo entre los núcleos de los 179 municipios.

- Transporte público (plan A): r5py con los GTFS normalizados (src/gtfs.py) + OSM.
  Salidas minuto a minuto entre 7:00 y 9:00 de un martes laborable; mediana (p50).
- Coche (aproximado): distancia en línea recta × factor de rodeo / velocidad media.
- Plan C (respaldo de TP si r5py falla): distancia × velocidad media, marcado aproximado.

    python -m src.tiempos            # transporte público con r5py + coche
    python -m src.tiempos --plan-c   # sin r5py
"""
import argparse
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from .config import FACTOR_RODEO, PROCESSED, RAW, T_INTRA_MIN, VEL_COCHE_KMH
from .gtfs import FECHA_OBJETIVO, INTERIM

MAX_MIN = 180


def _municipios():
    return pd.read_csv(PROCESSED / "municipios.csv", dtype={"ine": str})


def _distancias_km(m: pd.DataFrame) -> np.ndarray:
    xy = m[["x", "y"]].to_numpy()
    return np.sqrt(((xy[:, None, :] - xy[None, :, :]) ** 2).sum(-1)) / 1000


def _a_largo(mat: np.ndarray, ids, nombre: str) -> pd.DataFrame:
    o, d = np.meshgrid(ids, ids, indexing="ij")
    return pd.DataFrame({"origen": o.ravel(), "destino": d.ravel(), nombre: mat.ravel()})


def tiempos_coche(m: pd.DataFrame) -> pd.DataFrame:
    km = _distancias_km(m) * FACTOR_RODEO
    v = np.where(km < 10, VEL_COCHE_KMH["urbano"], VEL_COCHE_KMH["interurbano"])
    t = km / v * 60 + 5  # +5 min de aparcar/arrancar
    np.fill_diagonal(t, T_INTRA_MIN)
    return _a_largo(np.round(t, 1), m["ine"].to_numpy(), "min_coche")


def tiempos_plan_c(m: pd.DataFrame) -> pd.DataFrame:
    """Respaldo: TP ≈ 15 min de acceso/espera + distancia a 25 km/h (con red) o 15 km/h."""
    km = _distancias_km(m) * FACTOR_RODEO
    con_red = (m["n_paradas"].to_numpy() > 0)
    v = np.where(con_red[:, None] & con_red[None, :], 25, 15)
    t = 15 + km / v * 60
    np.fill_diagonal(t, T_INTRA_MIN)
    return _a_largo(np.round(t, 1), m["ine"].to_numpy(), "min_tp")


def tiempos_r5py(m: pd.DataFrame, origenes=None, max_memory="8G", tanda=20) -> pd.DataFrame:
    """Calcula por tandas de orígenes y guarda cada una en data/interim/tiempos_r5py/ para poder
    reanudar si el proceso se interrumpe (la red se construye una vez y r5py la cachea)."""
    sys.argv[1:] = ["--max-memory", max_memory]
    import geopandas as gpd
    import r5py

    feeds = sorted(str(p) for p in INTERIM.glob("gtfs_*.zip"))
    osm = str(next(RAW.glob("*.osm.pbf")))
    print("  r5py: construyendo red con", len(feeds), "GTFS…", flush=True)
    red = r5py.TransportNetwork(osm, feeds, allow_errors=True)
    pts = gpd.GeoDataFrame({"id": m["ine"]}, geometry=gpd.points_from_xy(m["lon"], m["lat"]), crs=4326)
    orig = pts if origenes is None else pts[pts["id"].isin(origenes)]
    # las tandas guardadas solo valen para estas mismas entradas (GTFS, OSM y orígenes)
    import hashlib
    firma = hashlib.md5("|".join([f"{p}:{Path(p).stat().st_size}:{Path(p).stat().st_mtime}" for p in feeds + [osm]]
                                 + list(orig["id"]) + [str(FECHA_OBJETIVO)]).encode()).hexdigest()[:10]
    carpeta = INTERIM / f"tiempos_r5py_{firma}"
    carpeta.mkdir(parents=True, exist_ok=True)
    partes = []
    for k in range(0, len(orig), tanda):
        f = carpeta / f"tanda_{k:03d}_{len(orig)}.csv"
        if not f.exists():
            print(f"  r5py [{dt.datetime.now():%H:%M:%S}]: orígenes {k + 1}-{min(k + tanda, len(orig))} "
                  f"de {len(orig)}", flush=True)
            _matriz_r5py(r5py, red, orig.iloc[k:k + tanda], pts).to_csv(f, index=False)
        partes.append(pd.read_csv(f, dtype={"origen": str, "destino": str}))
    return pd.concat(partes, ignore_index=True)


def _matriz_r5py(r5py, red, orig, pts) -> pd.DataFrame:
    ttm = r5py.TravelTimeMatrix(
        red, origins=orig, destinations=pts,
        departure=dt.datetime.combine(FECHA_OBJETIVO, dt.time(7, 0)),
        departure_time_window=dt.timedelta(hours=2),
        transport_modes=[r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK],
        max_time=dt.timedelta(minutes=MAX_MIN),
        percentiles=[50],
        snap_to_network=True,
    )
    df = pd.DataFrame(ttm)
    col = [c for c in df.columns if c.startswith("travel_time")][0]
    df = df.rename(columns={"from_id": "origen", "to_id": "destino", col: "min_tp"})
    return df[["origen", "destino", "min_tp"]]


def construir(plan_c=False) -> pd.DataFrame:
    m = _municipios()
    coche = tiempos_coche(m)
    if plan_c:
        tp, metodo = tiempos_plan_c(m), "plan_c_aproximado"
    else:
        tp, metodo = tiempos_r5py(m), "r5py_gtfs_osm_p50_7a9h"
    df = coche.merge(tp, on=["origen", "destino"], how="left")
    intra = df["origen"] == df["destino"]
    df.loc[intra, "min_tp"] = T_INTRA_MIN  # convención documentada
    df["accesible_tp"] = df["min_tp"].notna()
    df["min_tp"] = df["min_tp"].fillna(MAX_MIN + 1)
    df["metodo_tp"] = metodo
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan-c", action="store_true")
    ap.add_argument("--prueba", action="store_true", help="solo 3 orígenes")
    a = ap.parse_args()
    if a.prueba:
        m = _municipios()
        t0 = dt.datetime.now()
        r = tiempos_r5py(m, origenes=["28106", "28079", "28005"])
        print(dt.datetime.now() - t0)
        nom = m.set_index("ine")["nombre"]
        r["o"], r["d"] = r.origen.map(nom), r.destino.map(nom)
        print(r[r.destino.isin(["28079", "28106", "28058", "28074", "28092", "28005", "28148"])].to_string())
        print(r.min_tp.describe(), r.min_tp.isna().sum())
    else:
        df = construir(a.plan_c)
        df.to_csv(PROCESSED / "tiempos_tp.csv", index=False)
        print(df.describe())
