"""Recursos cercanos: escuelas infantiles (0–3), formación (FP, adultos, empleo) y centros
de atención social relevantes para la búsqueda de empleo."""
import geopandas as gpd
import pandas as pd

from .download import leer_csv, ruta

ESCUELA_INFANTIL = {"EEI", "EIPR", "EEI-CN", "CPR INF"}
FORMACION = {
    "CP IFP": "fp", "CPR FPE": "fp", "IES": "fp_ies", "CF EMPLEO": "formacion_empleo",
    "UFIL": "formacion_empleo", "CEPA": "adultos", "E.M.EPA": "adultos", "CPRIEPA": "adultos",
}
SOCIAL_SECTORES = {"Mujer", "Familia", "Infancia", "Otros grupos en situación de necesidad",
                   "(Inmigracion) Otros grupos en situación de necesidad", "Refugiados y asilados",
                   "Personas sin hogar"}


def _a_latlon(df, x, y):
    df = df[(pd.to_numeric(df[x], errors="coerce") > 0) & (pd.to_numeric(df[y], errors="coerce") > 0)].copy()
    g = gpd.GeoSeries(gpd.points_from_xy(df[x].astype(float), df[y].astype(float)), crs=25830).to_crs(4326)
    df["lat"], df["lon"] = g.y.round(6).values, g.x.round(6).values
    return df


def construir_recursos() -> pd.DataFrame:
    c = leer_csv(ruta("centros_educativos"))
    c = c[c["SITUACIÓN"] == "ALTA"]
    c["tipo"] = c["TIPO_ABRV"].map(lambda t: "escuela_infantil" if t in ESCUELA_INFANTIL else FORMACION.get(t))
    c = c[c["tipo"].notna()]
    c = _a_latlon(c, "UTM_X", "UTM_Y")
    edu = pd.DataFrame({
        "tipo": c["tipo"], "subtipo": c["TIPO_EXT"].str.capitalize(), "nombre": c["CENTRO"].str.title(),
        "titularidad": c["TITULARIDAD"].str.capitalize(),
        "ine": "28" + c["CDMUNI"].str.zfill(3), "direccion": (c["CDTPVIA"] + " " + c["DOMICILIO"] + " " + c["NMVIAL"]).str.strip(),
        "telefono": c["TELEFONO"], "web": c["WEB"], "lat": c["lat"], "lon": c["lon"],
        "fuente": "Centros educativos de la Comunidad de Madrid",
    })
    s = leer_csv(ruta("centros_sociales"))
    s = s[s["sector"].isin(SOCIAL_SECTORES) | s["subtipo"].str.contains("LABORAL", case=False)]
    s = s[s["tipo"] != "CENTROS RESIDENCIALES"]
    s = _a_latlon(s, "direccion_coor_x", "direccion_coor_y")
    soc = pd.DataFrame({
        "tipo": "servicio_social", "subtipo": (s["sector"] + " · " + s["subtipo"].str.capitalize()),
        "nombre": s["denominacion"].str.title(), "titularidad": s["entidad_naturaleza"].str.capitalize(),
        "ine": "28" + s["municipio_codigo"].str.zfill(3),
        "direccion": (s["direccion_via_tipo"] + " " + s["direccion_via_nombre"] + " " + s["direccion_portal"]).str.strip(),
        "telefono": s["contacto_telefono"], "web": "", "lat": s["lat"], "lon": s["lon"],
        "fuente": "Registro de centros de atención social",
    })
    r = pd.concat([edu, soc], ignore_index=True)
    r = r[r["lat"].between(39.8, 41.2) & r["lon"].between(-4.7, -3.0)]
    return r.reset_index(drop=True)


if __name__ == "__main__":
    r = construir_recursos()
    print(r.tipo.value_counts(), r.head())
