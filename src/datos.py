"""Limpieza: municipios, puestos por municipio de trabajo y sector, parados por municipio de
residencia y sector, balance de empleo. Todo con clave INE de 5 dígitos (28xxx)."""
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd

from .config import PARO_A_SECTOR, PROCESSED, RAMA_A_SECTOR, RAW, SECTORES, SERVICIOS
from .download import leer_csv, ruta

SIN_MUNICIPIO = "9999"


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.str.replace(",", ".", regex=False).replace({"-": np.nan, "": np.nan}),
                         errors="coerce")


def _municipios(df: pd.DataFrame) -> pd.DataFrame:
    """Filas de municipios con código INE 28xxx (el código del fichero = 3 dígitos + control)."""
    m = df[(df["Tipo territorio"] == "Municipios") & (df["Código territorio"] != SIN_MUNICIPIO)].copy()
    m["ine"] = "28" + m["Código territorio"].str.zfill(4).str[:3]
    m["valor"] = _num(m["Valor"])
    m["anio"] = m["Año"].astype(int)
    return m


# ---------------------------------------------------------------------------- municipios
def limites() -> gpd.GeoDataFrame:
    """Polígonos de los 179 municipios (los 21 distritos de Madrid se disuelven en 28079)."""
    g = gpd.read_file(f"zip://{ruta('limites')}")
    cod = g["codigo_geo"].astype(str)
    g["ine"] = np.where(cod.str.len() == 6, "28079", "28" + cod.str.zfill(4).str[:3])
    g = g.dissolve(by="ine", as_index=False)[["ine", "geometry"]]
    return g.to_crs(25830)


def paradas_gtfs() -> gpd.GeoDataFrame:
    """Todas las paradas de los GTFS del CRTM + Renfe Cercanías (EPSG:25830)."""
    frames = []
    for z in sorted(RAW.glob("gtfs_*.zip")):
        with zipfile.ZipFile(z) as zf:
            with zf.open("stops.txt") as f:
                s = pd.read_csv(f, dtype=str, usecols=lambda c: c in {"stop_id", "stop_lat", "stop_lon", "location_type"})
        s = s[s.get("location_type", "0").fillna("0").isin(["0", ""])] if "location_type" in s else s
        s["red"] = z.name.split("__")[0].removeprefix("gtfs_")
        frames.append(s)
    s = pd.concat(frames, ignore_index=True)
    s["stop_lat"] = s["stop_lat"].astype(float)
    s["stop_lon"] = s["stop_lon"].astype(float)
    s = s[s["stop_lat"].between(39.8, 41.2) & s["stop_lon"].between(-4.7, -3.0)]
    return gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.stop_lon, s.stop_lat), crs=4326).to_crs(25830)


def construir_municipios() -> tuple[pd.DataFrame, gpd.GeoDataFrame]:
    g = limites()
    # Nombre y población: padrón (último año), por código
    pad = _municipios(leer_csv(ruta("padron")))
    pad = pad[pad["Sexo"] == "Total"]
    anio_pad = pad["anio"].max()
    pad = pad[pad["anio"] == anio_pad][["ine", "Territorio", "valor"]].rename(
        columns={"Territorio": "nombre", "valor": "poblacion"})
    g = g.merge(pad, on="ine", how="left")

    # «Núcleo» = mediana de las paradas de transporte del municipio (evita centroides en el
    # monte en municipios grandes); si no hay paradas, punto representativo del polígono.
    st = gpd.sjoin(paradas_gtfs(), g[["ine", "geometry"]], predicate="within")
    med = st.groupby("ine").apply(lambda d: pd.Series({"x": d.geometry.x.median(), "y": d.geometry.y.median(),
                                                       "n_paradas": len(d)}), include_groups=False)
    g = g.merge(med, on="ine", how="left")
    rp = g.geometry.representative_point()
    sin = g["x"].isna()
    g.loc[sin, "x"], g.loc[sin, "y"] = rp[sin].x, rp[sin].y
    g["n_paradas"] = g["n_paradas"].fillna(0).astype(int)
    # Asegurar que el núcleo cae dentro del municipio
    pts = gpd.GeoSeries(gpd.points_from_xy(g.x, g.y), crs=25830)
    fuera = ~pts.within(g.geometry)
    g.loc[fuera, "x"], g.loc[fuera, "y"] = rp[fuera].x, rp[fuera].y
    ll = gpd.GeoSeries(gpd.points_from_xy(g.x, g.y), crs=25830).to_crs(4326)
    g["lat"], g["lon"] = ll.y.round(6), ll.x.round(6)
    g["x"], g["y"] = g["x"].round(1), g["y"].round(1)
    g["area_km2"] = (g.geometry.area / 1e6).round(2)
    g["poblacion"] = g["poblacion"].astype("Int64")
    g["anio_poblacion"] = anio_pad
    tabla = g[["ine", "nombre", "lat", "lon", "x", "y", "area_km2", "poblacion", "anio_poblacion", "n_paradas"]]
    return tabla.sort_values("ine").reset_index(drop=True), g[["ine", "nombre", "geometry"]]


# ------------------------------------------------------------------------------- puestos
def construir_puestos() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Puestos (afiliados en alta) por municipio del centro de trabajo y sector, a 31 dic.

    Desde 2021 las ramas vienen redondeadas a múltiplos de 5 y no suman el total: se
    reescalan para que cuadren con el total municipal; «No consta» se reparte pro rata.
    Devuelve (último año, serie de todos los años para la tendencia)."""
    u = _municipios(leer_csv(ruta("puestos_ubicacion_rama")))
    tot = u[u["Rama de actividad"] == "Total"][["ine", "anio", "valor"]].rename(columns={"valor": "total"})
    r = u[u["Rama de actividad"].isin(RAMA_A_SECTOR)].copy()
    r["sector"] = r["Rama de actividad"].map(RAMA_A_SECTOR)
    r = r.groupby(["ine", "anio", "sector"], as_index=False)["valor"].sum(min_count=1)
    # Hasta 2020: «-» = dato < 5 → el residuo (total − conocidos) se reparte entre los ocultos
    r = r.merge(tot, on=["ine", "anio"])
    r["oculto"] = r["valor"].isna()
    conocidos = r.groupby(["ine", "anio"])["valor"].transform("sum")
    n_ocultos = r.groupby(["ine", "anio"])["oculto"].transform("sum")
    resid = (r["total"] - conocidos).clip(lower=0)
    r.loc[r.oculto, "valor"] = (resid / n_ocultos.replace(0, np.nan))[r.oculto]
    # Reescalado al total (corrige redondeo y reparte «No consta»)
    suma = r.groupby(["ine", "anio"])["valor"].transform("sum")
    r["puestos"] = np.where(suma > 0, r["valor"] * r["total"] / suma, 0.0)
    serie = r[["ine", "anio", "sector", "puestos"]]

    anio = int(serie["anio"].max())
    ult = serie[serie["anio"] == anio].copy()
    ult["puestos"] = ult["puestos"].round(1)
    ult["anio"] = anio
    ult["fecha_referencia"] = f"{anio}-12-31"
    ult["estimado"] = False  # dato observado; solo reescalado por redondeo/«No consta»
    return ult.sort_values(["ine", "sector"]).reset_index(drop=True), serie


def tendencia(serie: pd.DataFrame, umbral: float = 0.02) -> pd.DataFrame:
    """Variación interanual de puestos por municipio y sector (último año vs anterior)."""
    a = int(serie["anio"].max())
    p = serie[serie["anio"].isin([a - 1, a])].pivot_table(index=["ine", "sector"], columns="anio",
                                                           values="puestos").reset_index()
    p["var_interanual"] = (p[a] - p[a - 1]) / p[a - 1].replace(0, np.nan)
    p["tendencia"] = np.select([p["var_interanual"] > umbral, p["var_interanual"] < -umbral],
                               ["sube", "baja"], "estable")
    p.loc[p["var_interanual"].isna(), "tendencia"] = "sin datos"
    return p[["ine", "sector", "var_interanual", "tendencia"]]


# ------------------------------------------------------------------------------- parados
def estructura_residencia() -> pd.DataFrame:
    """Afiliados por municipio de residencia y sector (1 de enero, último año)."""
    a = _municipios(leer_csv(ruta("afiliados_residencia_rama")))
    anio = a["anio"].max()
    a = a[a["anio"] == anio]
    tot = a[a["Rama de actividad"] == "Total"][["ine", "valor"]].rename(columns={"valor": "ocupados_residentes"})
    r = a[a["Rama de actividad"].isin(RAMA_A_SECTOR)].copy()
    r["sector"] = r["Rama de actividad"].map(RAMA_A_SECTOR)
    r = r.groupby(["ine", "sector"], as_index=False)["valor"].sum()
    r["anio"] = anio
    return r.rename(columns={"valor": "afiliados_residentes"}), tot.assign(anio_residencia=anio)


def construir_parados() -> pd.DataFrame:
    """Parados por municipio de residencia y sector (31 de marzo, último año).

    El paro solo distingue 4 sectores: «Servicios» se reparte entre DIS/EMP/OTR según la
    estructura de afiliados residentes del propio municipio (estimado=True). «Sin sector de
    actividad» (sin empleo anterior) se reparte pro rata entre todos los sectores y se informa
    aparte, porque compite por cualquier puesto de entrada."""
    p = _municipios(leer_csv(ruta("paro_sector")))
    p = p[(p["Sexo"] == "Total") & (p["Nacionalidad"].isin(["Españoles", "Extranjeros"]))]
    anio = p["anio"].max()
    # El último año puede venir solo con el total: estructura sectorial del último año con
    # desglose, escalada al total municipal más reciente.
    anio_sec = p[p["Sector"] != "Total"]["anio"].max()
    tot = p[(p["anio"] == anio) & (p["Sector"] == "Total")].groupby("ine")["valor"].sum()
    p = p[(p["anio"] == anio_sec) & (p["Sector"] != "Total")]
    p = p.groupby(["ine", "Sector"], as_index=False)["valor"].sum()
    w = p.pivot_table(index="ine", columns="Sector", values="valor", fill_value=0)
    w = w.mul((tot / w.sum(axis=1)).reindex(w.index).fillna(1.0), axis=0)

    est, _ = estructura_residencia()
    est = est.pivot_table(index="ine", columns="sector", values="afiliados_residentes", fill_value=0)
    filas = []
    for ine, row in w.iterrows():
        serv = est.loc[ine, SERVICIOS] if ine in est.index else pd.Series(1.0, index=SERVICIOS)
        serv = serv / serv.sum() if serv.sum() > 0 else pd.Series(1 / 3, index=SERVICIOS)
        for nombre_paro, sectores in PARO_A_SECTOR.items():
            for s in sectores:
                v = row.get(nombre_paro, 0) * (serv[s] if nombre_paro == "Servicios" else 1.0)
                filas.append((ine, s, v, nombre_paro == "Servicios" or anio_sec != anio))
        sin = row.get("Sin sector de actividad", 0)
        filas.append((ine, "_SIN", sin, False))
    d = pd.DataFrame(filas, columns=["ine", "sector", "parados_con_sector", "estimado"])
    sin = d[d.sector == "_SIN"].set_index("ine")["parados_con_sector"]
    d = d[d.sector != "_SIN"].copy()
    cuota = d["parados_con_sector"] / d.groupby("ine")["parados_con_sector"].transform("sum").replace(0, np.nan)
    d["parados_sin_empleo_anterior"] = (cuota.fillna(1 / len(SECTORES)) * d["ine"].map(sin)).round(1)
    d["parados_con_sector"] = d["parados_con_sector"].round(1)
    d["parados"] = (d["parados_con_sector"] + d["parados_sin_empleo_anterior"]).round(1)
    d["anio"] = anio
    d["anio_estructura_sectorial"] = anio_sec
    d["fecha_referencia"] = f"{anio}-03-31"
    return d.sort_values(["ine", "sector"]).reset_index(drop=True)


def construir_balance(puestos: pd.DataFrame) -> pd.DataFrame:
    _, res = estructura_residencia()
    pt = puestos.groupby("ine", as_index=False)["puestos"].sum()
    b = pt.merge(res, on="ine", how="outer")
    b["balance"] = (b["puestos"] / b["ocupados_residentes"]).round(3)
    b["tipo"] = np.select([b["balance"] >= 1.1, b["balance"] <= 0.6], ["polo de empleo", "ciudad dormitorio"],
                          "equilibrado")
    b["anio_puestos"] = int(puestos["anio"].iloc[0])
    return b.rename(columns={"ocupados_residentes": "residentes_ocupados"}).round({"puestos": 0})


GRANDES_GRUPOS_CNO = {  # palabra clave del concepto → gran grupo CNO-11
    "directores": 1, "científicos": 2, "apoyo": 3, "contables": 4, "restauración": 5,
    "agrícola": 6, "artesanos": 7, "operadores": 8, "elementales": 9,
}


def construir_salario() -> pd.DataFrame:
    """Ganancia media anual por gran grupo CNO-11 (Comunidad de Madrid, último año).
    Un «-» delante del dato = muestra de 100 a 500 observaciones (poco fiable)."""
    s = leer_csv(ruta("salario_ocupacion"))
    s = s[s["Sexo"] == "Total"]
    anio = s["Año"].max()
    s = s[s["Año"] == anio]
    filas = []
    for _, r in s.iterrows():
        g = next((v for k, v in GRANDES_GRUPOS_CNO.items() if k in r["Concepto"]), None)
        v = r["Valor"].strip()
        if g is None or v in ("", "-", ".."):
            continue
        filas.append({"gran_grupo_cno": g, "concepto": r["Concepto"].replace("Ganancia media anual de ", ""),
                      "salario_medio": round(abs(float(v)), 0), "poco_fiable": v.startswith("-"),
                      "anio": int(anio)})
    return pd.DataFrame(filas).sort_values("gran_grupo_cno")


def nombres_sector() -> pd.DataFrame:
    return pd.DataFrame({"sector": list(SECTORES) + ["TOT"],
                         "nombre_sector": list(SECTORES.values()) + ["Todos los sectores"]})


if __name__ == "__main__":
    PROCESSED.mkdir(parents=True, exist_ok=True)
    mun, geo = construir_municipios()
    print(mun.head(), len(mun))
    pu, serie = construir_puestos()
    pa = construir_parados()
    print(pu.groupby("sector").puestos.sum(), pa.groupby("sector").parados.sum())
    print(construir_balance(pu).sort_values("balance").head())
