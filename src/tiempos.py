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
    import hashlib

    import geopandas as gpd

    feeds = sorted(str(p) for p in INTERIM.glob("gtfs_*.zip"))
    osm = str(next(RAW.glob("*.osm.pbf")))
    pts = gpd.GeoDataFrame({"id": m["ine"]}, geometry=gpd.points_from_xy(m["lon"], m["lat"]), crs=4326)
    orig = pts if origenes is None else pts[pts["id"].isin(origenes)]
    # las tandas guardadas solo valen para estas mismas entradas: GTFS en bruto, código que los
    # normaliza, OSM, puntos y fecha (los zips normalizados se reescriben en cada ejecución)
    entradas = sorted(RAW.glob("gtfs_*__*.zip")) + [Path(osm)]
    firma = hashlib.md5("|".join([f"{p.name}:{p.stat().st_size}" for p in entradas]
                                 + [Path(__file__).with_name("gtfs.py").read_text(encoding="utf-8")]
                                 + [f"{i}:{x:.6f}:{y:.6f}" for i, x, y in zip(m["ine"], m["lon"], m["lat"])
                                    if i in set(orig["id"])]
                                 + [str(FECHA_OBJETIVO)]).encode()).hexdigest()[:10]
    carpeta = INTERIM / f"tiempos_r5py_{firma}"
    carpeta.mkdir(parents=True, exist_ok=True)
    red = None
    partes = []
    for k in range(0, len(orig), tanda):
        f = carpeta / f"tanda_{k:03d}_{len(orig)}.csv"
        if not f.exists():
            if red is None:  # solo se construye la red si falta alguna tanda
                import r5py
                print("  r5py: construyendo red con", len(feeds), "GTFS…", flush=True)
                red = r5py.TransportNetwork(osm, feeds, allow_errors=True)
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


UMBRAL_HUECO = 0.65  # proporción de paradas de autobús del municipio sin horarios utilizables
REDES_BUS = {"interurbanos", "urbanos_resto"}
REDES_FERROCARRIL = {"renfe_cercanias", "cercanias", "metro", "metro_ligero"}


def _paradas_con_defecto() -> pd.DataFrame:
    """Paradas de los GTFS de autobús (en bruto) sin ningún viaje con horario real: o no aparecen
    en stop_times (líneas publicadas sin viajes) o solo las sirven viajes «de relleno» (todas las
    paradas a la misma hora, p. ej. 02:00:00)."""
    import zipfile
    frames = []
    for z in sorted(RAW.glob("gtfs_*__*.zip")):
        red = z.name.split("__")[0].removeprefix("gtfs_")
        if red not in REDES_BUS:
            continue
        with zipfile.ZipFile(z) as zf:
            st = pd.read_csv(zf.open("stops.txt"), dtype=str, keep_default_na=False)
            stt = pd.read_csv(zf.open("stop_times.txt"), dtype=str,
                              usecols=["trip_id", "stop_id", "departure_time"])
        if "location_type" in st:
            st = st[st["location_type"].isin(["0", ""])]
        horas = stt.groupby("trip_id")["departure_time"].nunique()
        buenas = set(stt.loc[stt["trip_id"].isin(horas[horas > 2].index), "stop_id"])
        st = st.assign(red=red, defecto=~st["stop_id"].isin(buenas))
        frames.append(st[["stop_id", "stop_lat", "stop_lon", "red", "defecto"]])
    return pd.concat(frames, ignore_index=True)


def huecos_gtfs() -> pd.DataFrame:
    """Por municipio: proporción de paradas de autobús sin horarios en la fuente, si tiene
    ferrocarril (Cercanías, Metro, Metro Ligero) y si se considera afectado por el hueco."""
    import geopandas as gpd

    from .datos import limites, paradas_gtfs
    lim = limites()[["ine", "geometry"]]
    s = _paradas_con_defecto()
    p = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s["stop_lon"].astype(float), s["stop_lat"].astype(float)),
                         crs=4326).to_crs(lim.crs)
    h = gpd.sjoin(p, lim, predicate="within").groupby("ine")["defecto"].mean().rename("paradas_sin_horario")
    todas = paradas_gtfs()
    fc = gpd.sjoin(todas[todas["red"].isin(REDES_FERROCARRIL)], lim.to_crs(todas.crs), predicate="within")
    out = _municipios()[["ine"]].merge(h, on="ine", how="left").fillna({"paradas_sin_horario": 0})
    out["ferrocarril"] = out["ine"].isin(set(fc["ine"]))
    out["hueco_gtfs"] = out["paradas_sin_horario"] >= UMBRAL_HUECO
    return out


def _grupo_par(df: pd.DataFrame, fc: set) -> pd.Series:
    """Tipo de par para la estimación: con Madrid capital, con ferrocarril en un extremo o sin él."""
    o_fc, d_fc = df["origen"].isin(fc), df["destino"].isin(fc)
    madrid = (df["origen"] == "28079") | (df["destino"] == "28079")
    return pd.Series(np.select([madrid, o_fc & d_fc, o_fc | d_fc], ["madrid", "ferrocarril_ambos", "ferrocarril_uno"],
                               "autobus"), index=df.index)


def _estimacion_hueco(df: pd.DataFrame, h: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    """Tiempo estimado en TP para los pares afectados por el hueco: mediana condicionada al tiempo
    en coche (regresión cuantílica p50, t_tp = a + b·t_coche), ajustada por tipo de par sobre los
    pares que los GTFS cubren bien."""
    from sklearn.linear_model import QuantileRegressor
    hueco, fc = set(h.loc[h["hueco_gtfs"], "ine"]), set(h.loc[h["ferrocarril"], "ine"])
    grupo = _grupo_par(df, fc)
    ok = (df["origen"] != df["destino"]) & df["min_tp"].notna() \
        & ~df["origen"].isin(hueco) & ~df["destino"].isin(hueco)
    est = pd.Series(np.nan, index=df.index)
    coefs = []
    for g in grupo.unique():
        x = df[ok & (grupo == g)]
        q = QuantileRegressor(quantile=0.5, alpha=0, solver="highs").fit(x[["min_coche"]], x["min_tp"])
        est[grupo == g] = q.predict(df.loc[grupo == g, ["min_coche"]])
        coefs.append({"tipo_par": g, "a_min": round(q.intercept_, 1), "b": round(q.coef_[0], 3), "pares_ajuste": len(x),
                      "error_abs_mediano_min": round((x["min_tp"] - q.predict(x[["min_coche"]])).abs().median(), 1)})
    coefs = pd.DataFrame(coefs)
    print(f"  hueco GTFS: {len(hueco)} municipios afectados\n{coefs.to_string(index=False)}", flush=True)
    return est.round(0), coefs


def construir(plan_c=False) -> pd.DataFrame:
    m = _municipios()
    coche = tiempos_coche(m)
    if plan_c:
        tp, metodo = tiempos_plan_c(m), "plan_c_aproximado"
    else:
        tp, metodo = tiempos_r5py(m), "r5py_gtfs_osm_p50_7a9h"
    df = coche.merge(tp, on=["origen", "destino"], how="left")
    df["metodo_tp"] = metodo
    if not plan_c:
        # El GTFS de interurbanos del Consorcio se publica como «Datos parciales»: hay líneas sin
        # viajes o con horarios de relleno. En los pares con un extremo afectado se usa el menor
        # entre r5py y una estimación calibrada, y se marca en metodo_tp.
        h = huecos_gtfs()
        hueco = set(h.loc[h["hueco_gtfs"], "ine"])
        est, coefs = _estimacion_hueco(df, h)
        h.to_csv(PROCESSED / "huecos_gtfs.csv", index=False)
        coefs.to_csv(PROCESSED / "estimacion_hueco_gtfs.csv", index=False)
        afectado = (df["origen"].isin(hueco) | df["destino"].isin(hueco)) & (df["origen"] != df["destino"])
        usa = afectado & (est <= MAX_MIN) & (df["min_tp"].isna() | (est < df["min_tp"]))
        df.loc[usa, "min_tp"] = est[usa]
        df.loc[usa, "metodo_tp"] = "estimado_hueco_gtfs"
    intra = df["origen"] == df["destino"]
    df.loc[intra, "min_tp"] = T_INTRA_MIN  # convención documentada
    df["accesible_tp"] = df["min_tp"].notna()
    df["min_tp"] = df["min_tp"].fillna(MAX_MIN + 1)
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
