"""Respaldo diario: CSV comprimido con los precios del día + copia de la base."""
from __future__ import annotations

import csv
import gzip
import logging
import shutil
import sqlite3
from pathlib import Path

log = logging.getLogger(__name__)

COPIAS_BASE = 7  # copias diarias de la base completa que se conservan


def respaldar(con: sqlite3.Connection, carpeta: Path, fecha: str) -> Path:
    destino = carpeta / fecha[:4] / f"precios-{fecha}.csv.gz"
    destino.parent.mkdir(parents=True, exist_ok=True)
    filas = con.execute(
        """SELECT pr.fecha, p.tienda, p.categoria, p.sku, p.nombre, p.marca,
                  pr.precio, pr.precio_lista, pr.disponible, p.url
           FROM precios pr JOIN productos p ON p.id = pr.producto_id
           WHERE pr.fecha = ? ORDER BY p.categoria, p.tienda, p.nombre""",
        (fecha,),
    )
    with gzip.open(destino, "wt", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["fecha", "tienda", "categoria", "sku", "nombre", "marca",
                    "precio", "precio_lista", "disponible", "url"])
        w.writerows(tuple(fila) for fila in filas)

    # Copia consistente de la base completa (rotativa)
    copias = carpeta / "base"
    copias.mkdir(parents=True, exist_ok=True)
    con.commit()
    copia = copias / f"precios-{fecha}.sqlite"
    with sqlite3.connect(copia) as dst:
        con.backup(dst)
    with open(copia, "rb") as fin, gzip.open(f"{copia}.gz", "wb") as fout:
        shutil.copyfileobj(fin, fout)
    copia.unlink()
    for vieja in sorted(copias.glob("precios-*.sqlite.gz"))[:-COPIAS_BASE]:
        vieja.unlink()
    log.info("Respaldo guardado en %s", destino)
    return destino
