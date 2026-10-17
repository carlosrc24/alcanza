"""Pipeline reproducible: descarga → limpieza → tiempos → indicadores → data/processed/.

    python -m src.pipeline                 # reutiliza tiempos_tp.csv si ya existe
    python -m src.pipeline --tiempos       # recalcula los tiempos con r5py (~minutos)
    python -m src.pipeline --tiempos --plan-c
"""
import argparse
import json

import pandas as pd

from . import datos, download, gtfs, indicadores, recursos, tiempos
from .config import PROCESSED, RAW


def main(recalcular_tiempos=False, plan_c=False):
    PROCESSED.mkdir(parents=True, exist_ok=True)
    print("1/6 Descarga")
    download.main(gtfs=not plan_c)

    print("2/6 Municipios")
    mun, geo = datos.construir_municipios()
    mun.to_csv(PROCESSED / "municipios.csv", index=False)
    geo = geo.to_crs(4326)
    geo["geometry"] = geo.geometry.simplify(0.0008, preserve_topology=True)
    geo.to_file(PROCESSED / "municipios.geojson", driver="GeoJSON")

    print("3/6 Puestos, parados, balance")
    pu, serie = datos.construir_puestos()
    pu.to_csv(PROCESSED / "puestos_municipio_sector.csv", index=False)
    pa = datos.construir_parados()
    pa.to_csv(PROCESSED / "parados_municipio_sector.csv", index=False)
    datos.construir_balance(pu).to_csv(PROCESSED / "balance_empleo.csv", index=False)
    datos.nombres_sector().to_csv(PROCESSED / "sectores.csv", index=False)
    datos.construir_salario().to_csv(PROCESSED / "salario_ocupacion.csv", index=False)

    print("4/6 Tiempos de viaje")
    ft = PROCESSED / "tiempos_tp.csv"
    if recalcular_tiempos or not ft.exists():
        if not plan_c:
            gtfs.normalizar_todos()
        tiempos.construir(plan_c).to_csv(ft, index=False)
    tt = pd.read_csv(ft, dtype={"origen": str, "destino": str})

    print("5/6 Indicadores")
    ind, dest = indicadores.calcular(tt, pu, pa, serie, mun)
    ind.to_csv(PROCESSED / "indicadores_municipio_sector.csv", index=False)
    dest.to_csv(PROCESSED / "oportunidad_destino.csv", index=False)

    print("6/6 Recursos")
    recursos.construir_recursos().to_csv(PROCESSED / "recursos.csv", index=False)

    # Trazabilidad: qué fichero bruto (y de qué fecha) alimenta esta versión
    metas = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(RAW.glob("*.meta.json"))]
    (PROCESSED / "fuentes.json").write_text(json.dumps(metas, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Hecho →", PROCESSED)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiempos", action="store_true")
    ap.add_argument("--plan-c", action="store_true")
    a = ap.parse_args()
    main(a.tiempos, a.plan_c)
