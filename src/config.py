"""Configuración central: rutas, ids del catálogo y parámetros del modelo."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REF = ROOT / "data" / "ref"

CKAN = "https://datos.comunidad.madrid/api/3/action/"

# Conjuntos del catálogo de datos abiertos de la Comunidad de Madrid (id CKAN encontrado
# buscando por título con package_search). `formato` = recurso que se descarga.
DATASETS = {
    # Puestos por municipio de TRABAJO y rama (anual). Sustituye a la estimación IPF.
    "puestos_ubicacion_rama": {"id": "afiliados_por_ubicacion_y_rama", "formato": "csv"},
    # Afiliados por municipio de RESIDENCIA y rama (anual, 1 de enero).
    "afiliados_residencia_rama": {"id": "afiliados_por_residencia_y_rama", "formato": "csv"},
    # Paro registrado por municipio de residencia y sector CNAE-09 (anual, 31 de marzo).
    "paro_sector": {"id": "paro_por_nacionalidad_sector_y_sexo_09", "formato": "csv"},
    # Población empadronada por sexo (anual).
    "padron": {"id": "padron_por_sexo", "formato": "csv"},
    # Ganancia media anual por gran grupo de ocupación CNO-11 (encuesta cuatrienal, regional)
    "salario_ocupacion": {"id": "ganancia_media_hogares_por_ocupacion_y_sexo", "formato": "csv"},
    # Recursos
    "centros_educativos": {"id": "centros_educativos", "formato": "csv"},
    "centros_sociales": {"id": "atencion_social_registro_centros", "formato": "csv"},
    # Límites municipales y distritos de Madrid (SHP 2020, publicado por la Comunidad)
    "limites": {"id": "covid19_tia_muni_y_distritos", "formato": "shp",
                "nombre_contiene": "2020"},
}

# GTFS del Consorcio Regional de Transportes (items ArcGIS enlazados desde el catálogo,
# etiqueta CRTM). Descarga: https://crtm.maps.arcgis.com/sharing/rest/content/items/<id>/data
GTFS = {
    "metro": "5c7f2951962540d69ffe8f640d94c246",
    "cercanias": "1a25440bf66f499bae2657ec7fb40144",
    "metro_ligero": "aaed26cc0ff64b0c947ac0bc3e033196",
    "interurbanos": "885399f83408473c8d815e40c5e702b7",
    "emt": "868df0e58fca47e79b942902dffd7da0",
    "urbanos_resto": "357e63c2904f43aeb5d8a267a64346d8",
}
GTFS_URL = "https://crtm.maps.arcgis.com/sharing/rest/content/items/{}/data"

# Fuentes complementarias (no están en el catálogo de la Comunidad):
EXTERNAS = {
    # El GTFS de Cercanías del CRTM no trae horarios: se usa el de Renfe (toda España; se filtra
    # al núcleo de Madrid en src/gtfs.py)
    "gtfs_renfe_cercanias": {"url": "https://ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip",
                             "ext": "zip", "titulo": "Horarios de Cercanías (GTFS) — Renfe Operadora",
                             "solo_tiempos": False},
    # Validación: microdatos de viajes de la Encuesta Domiciliaria de Movilidad 2018 (conjunto
    # «Resultados de la EDM 2018» del catálogo de la Comunidad; fichero alojado por el Consorcio)
    "edm2018_viajes": {"url": "https://crtm.maps.arcgis.com/sharing/rest/content/items/"
                              "6afd4db8175d4902ada0803f08ccf50e/data",
                       "ext": "xlsx", "titulo": "Resultados de la EDM 2018 — Viajes (Consorcio Regional de Transportes)",
                       "solo_tiempos": False},
    # Red peatonal para r5py
    "osm_madrid": {"url": "https://download.geofabrik.de/europe/spain/madrid-latest.osm.pbf",
                   "ext": "osm.pbf", "titulo": "OpenStreetMap — extracto Comunidad de Madrid (Geofabrik)",
                   "solo_tiempos": True},
}

# --- Sectores -------------------------------------------------------------------
# Paro solo trae 4 grandes sectores; los puestos traen 7 ramas. Sector común del modelo:
# las ramas de servicios se separan y el paro de «Servicios» se reparte entre ellas con la
# estructura de afiliados por residencia del propio municipio (marcado como estimado).
SECTORES = {
    "AGR": "Agricultura y ganadería",
    "IND": "Industria y energía",
    "CON": "Construcción",
    "DIS": "Comercio, transporte y hostelería",
    "EMP": "Servicios a empresas, financieros e inmobiliarios",
    "OTR": "Otros servicios (educación, sanidad, administración, personales)",
}
RAMA_A_SECTOR = {  # ramas de los ficheros de afiliación
    "Agricultura y ganadería": "AGR",
    "Minería, industria y energía": "IND",
    "Construcción": "CON",
    "Servicios de distribución y hostelería": "DIS",
    "Servicios a empresas y financieros": "EMP",
    "Inmobiliarias": "EMP",
    "Otros servicios": "OTR",
}
PARO_A_SECTOR = {"Agricultura": ["AGR"], "Industria": ["IND"], "Construcción": ["CON"],
                 "Servicios": ["DIS", "EMP", "OTR"]}
SERVICIOS = ["DIS", "EMP", "OTR"]

# --- Modelo ---------------------------------------------------------------------
UMBRALES_T = [15, 30, 45, 60, 75, 90]   # minutos
T_INTRA_MIN = 10        # tiempo dentro del propio municipio (constante documentada)
VEL_COCHE_KMH = {"urbano": 30, "interurbano": 55}
FACTOR_RODEO = 1.3      # distancia por carretera ≈ 1,3 × distancia en línea recta
