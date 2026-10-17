"""Normalización de los GTFS para el cálculo de tiempos.

Los feeds no comparten un periodo de validez (Metro caducó en mayo de 2026; EMT e
interurbanos empiezan en octubre de 2026), así que cada feed se «congela» en un martes
laborable normal dentro de su propio calendario (día de referencia) y los servicios activos
ese día se reasignan a una fecha objetivo común (FECHA_OBJETIVO). Se eliminan los viajes que
no circulan ese día. Renfe Cercanías se filtra al núcleo de Madrid (rutas con prefijo 10).

    python -m src.gtfs
"""
import datetime as dt
import io
import zipfile

import pandas as pd

from .config import RAW, ROOT

INTERIM = ROOT / "data" / "interim"
FECHA_OBJETIVO = dt.date(2026, 10, 27)   # martes laborable
FESTIVOS = {dt.date(2026, 5, 15), dt.date(2026, 11, 9), dt.date(2026, 12, 8), dt.date(2026, 12, 6),
            dt.date(2026, 11, 2), dt.date(2026, 10, 12)}
GTFS_CRTM_VACIO = {"cercanias"}  # el feed de Cercanías del CRTM no trae horarios


def _leer(zf, nombre):
    if nombre not in zf.namelist():
        return None
    df = pd.read_csv(zf.open(nombre), dtype=str, keep_default_na=False, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    for c in df.columns:
        df[c] = df[c].str.strip()
    return df


def activos(cal, cd, d: dt.date) -> set:
    ds = d.strftime("%Y%m%d")
    dia = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][d.weekday()]
    s = set()
    if cal is not None and len(cal):
        m = (cal[dia] == "1") & (cal["start_date"] <= ds) & (cal["end_date"] >= ds)
        s = set(cal.loc[m, "service_id"])
    if cd is not None and len(cd):
        x = cd[cd["date"] == ds]
        s |= set(x.loc[x["exception_type"] == "1", "service_id"])
        s -= set(x.loc[x["exception_type"] == "2", "service_id"])
    return s


def dia_referencia(cal, cd, trips) -> dt.date:
    """Martes no festivo con más viajes, buscando desde FECHA_OBJETIVO hacia fuera."""
    fechas = []
    for c, col in ((cal, ("start_date", "end_date")), (cd, ("date", "date"))):
        if c is not None and len(c):
            fechas += [c[col[0]].min(), c[col[1]].max()]
    ini = dt.datetime.strptime(min(fechas), "%Y%m%d").date()
    fin = dt.datetime.strptime(max(fechas), "%Y%m%d").date()
    candidatos = []
    d = ini + dt.timedelta(days=(1 - ini.weekday()) % 7)
    while d <= fin:
        if d not in FESTIVOS and not (dt.date(d.year, 7, 1) <= d <= dt.date(d.year, 9, 10)) \
                and not (d.month == 12 and d.day >= 20) and not (d.month == 1 and d.day <= 7):
            candidatos.append(d)
        d += dt.timedelta(days=7)
    candidatos.sort(key=lambda x: abs((x - FECHA_OBJETIVO).days))
    por_servicio = trips.groupby("service_id").size()
    mejor, n_mejor = None, -1
    for d in candidatos[:8]:  # los 8 martes más cercanos: el de más viajes (evita días raros)
        n = por_servicio.reindex(list(activos(cal, cd, d))).fillna(0).sum()
        if n > n_mejor * 1.02:
            mejor, n_mejor = d, n
    return mejor


def normalizar(z) -> tuple[str, dt.date, int]:
    nombre = z.name.split("__")[0].removeprefix("gtfs_")
    INTERIM.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(z) as zf:
        t = {n.removesuffix(".txt"): _leer(zf, n) for n in zf.namelist() if n.endswith(".txt")}
    trips = t["trips"]
    if nombre == "renfe_cercanias":
        t["routes"] = t["routes"][t["routes"]["route_id"].str.startswith("10")]
        trips = trips[trips["route_id"].isin(t["routes"]["route_id"])]
    ref = dia_referencia(t.get("calendar"), t.get("calendar_dates"), trips)
    serv = activos(t.get("calendar"), t.get("calendar_dates"), ref)
    trips = trips[trips["service_id"].isin(serv)].copy()
    trips["service_id"] = "S"
    t["trips"] = trips
    ids = set(trips["trip_id"])
    t["stop_times"] = t["stop_times"][t["stop_times"]["trip_id"].isin(ids)]
    if t.get("frequencies") is not None:
        t["frequencies"] = t["frequencies"][t["frequencies"]["trip_id"].isin(ids)]
        if not len(t["frequencies"]):
            t.pop("frequencies")
    t["routes"] = t["routes"][t["routes"]["route_id"].isin(set(trips["route_id"]))]
    usadas = set(t["stop_times"]["stop_id"])
    st = t["stops"]
    if "parent_station" in st:
        usadas |= set(st.loc[st["stop_id"].isin(usadas), "parent_station"]) - {""}
    t["stops"] = st[st["stop_id"].isin(usadas)]
    obj = FECHA_OBJETIVO.strftime("%Y%m%d")
    t["calendar"] = pd.DataFrame([{"service_id": "S", "monday": 1, "tuesday": 1, "wednesday": 1, "thursday": 1,
                                   "friday": 1, "saturday": 1, "sunday": 1, "start_date": obj, "end_date": obj}])
    t.pop("calendar_dates", None)
    # irrelevantes para el cálculo y a veces inconsistentes (feed_info con varias filas)
    for k in ("fare_attributes", "fare_rules", "transfers", "feed_info", "shapes"):
        t.pop(k, None)
    destino = INTERIM / f"gtfs_{nombre}.zip"
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as out:
        for k, df in t.items():
            if df is not None:
                buf = io.StringIO()
                df.to_csv(buf, index=False)
                out.writestr(f"{k}.txt", buf.getvalue())
    return nombre, ref, len(trips)


def normalizar_todos():
    res = []
    for z in sorted(RAW.glob("gtfs_*.zip")):
        nombre = z.name.split("__")[0].removeprefix("gtfs_")
        if nombre in GTFS_CRTM_VACIO:
            continue
        res.append(normalizar(z))
        print("  GTFS", *res[-1])
    return pd.DataFrame(res, columns=["red", "dia_referencia", "viajes"])


if __name__ == "__main__":
    print(normalizar_todos())
