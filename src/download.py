"""Descarga de las fuentes a data/raw/ (con fecha). Idempotente: no repite lo ya descargado.

    python -m src.download            # todo
    python -m src.download --sin-gtfs # sin los GTFS (~100 MB)
"""
import argparse
import datetime as dt
import io
import json

import pandas as pd
import requests

from .config import CKAN, DATASETS, GTFS, GTFS_URL, RAW

HOY = dt.date.today().isoformat()


def package_show(pid: str) -> dict:
    r = requests.get(CKAN + "package_show", params={"id": pid}, timeout=60)
    r.raise_for_status()
    return r.json()["result"]


def _ultimo(prefijo: str, ext: str):
    """Fichero más reciente ya descargado para una clave (o None)."""
    hay = sorted(RAW.glob(f"{prefijo}__*.{ext}"))
    return hay[-1] if hay else None


def descargar_dataset(clave: str, forzar: bool = False):
    meta = DATASETS[clave]
    ext = meta["formato"] if meta["formato"] != "shp" else "zip"
    previo = _ultimo(clave, ext)
    if previo and not forzar:
        return previo
    p = package_show(meta["id"])
    recursos = [r for r in p["resources"] if (r.get("format") or "").lower() == meta["formato"]]
    if "nombre_contiene" in meta:
        recursos = [r for r in recursos if meta["nombre_contiene"] in (r.get("name") or "")]
    url = recursos[0]["url"]
    destino = RAW / f"{clave}__{HOY}.{ext}"
    print(f"↓ {clave}: {url}")
    b = requests.get(url, timeout=300).content
    destino.write_bytes(b)
    # metadatos para la trazabilidad (fuente + fecha de descarga + última modificación)
    (RAW / f"{clave}__{HOY}.meta.json").write_text(json.dumps({
        "clave": clave, "id": meta["id"], "titulo": p["title"], "url": url,
        "descargado": HOY, "modificado_catalogo": recursos[0].get("last_modified") or p.get("metadata_modified"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def descargar_gtfs(forzar: bool = False):
    out = {}
    for nombre, item in GTFS.items():
        previo = _ultimo(f"gtfs_{nombre}", "zip")
        if previo and not forzar:
            out[nombre] = previo
            continue
        destino = RAW / f"gtfs_{nombre}__{HOY}.zip"
        print(f"↓ GTFS {nombre}")
        with requests.get(GTFS_URL.format(item), stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(destino, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
        out[nombre] = destino
    return out


def leer_csv(path) -> pd.DataFrame:
    """Lector único de los CSV del catálogo: `;`, utf-8 o latin-1, todo como texto."""
    b = open(path, "rb").read()
    try:
        t = b.decode("utf-8-sig")
    except UnicodeDecodeError:
        t = b.decode("latin-1")
    return pd.read_csv(io.StringIO(t), sep=";", dtype=str, keep_default_na=False)


def ruta(clave: str):
    meta = DATASETS[clave]
    ext = meta["formato"] if meta["formato"] != "shp" else "zip"
    p = _ultimo(clave, ext)
    if p is None:
        p = descargar_dataset(clave)
    return p


def main(gtfs: bool = True):
    RAW.mkdir(parents=True, exist_ok=True)
    for clave in DATASETS:
        descargar_dataset(clave)
    if gtfs:
        descargar_gtfs()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-gtfs", action="store_true")
    main(gtfs=not ap.parse_args().sin_gtfs)
