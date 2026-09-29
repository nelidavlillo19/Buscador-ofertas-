"""Base de datos SQLite con el historial diario de precios."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .modelos import Producto

ESQUEMA = """
CREATE TABLE IF NOT EXISTS productos (
    id TEXT PRIMARY KEY,
    tienda TEXT NOT NULL,
    sku TEXT NOT NULL,
    nombre TEXT NOT NULL,
    url TEXT,
    marca TEXT,
    imagen TEXT,
    categoria TEXT,
    primera_vez TEXT,
    ultima_vez TEXT
);
CREATE TABLE IF NOT EXISTS precios (
    producto_id TEXT NOT NULL REFERENCES productos(id),
    fecha TEXT NOT NULL,
    precio REAL NOT NULL,
    precio_lista REAL,
    disponible INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (producto_id, fecha)
);
CREATE TABLE IF NOT EXISTS alertas (
    producto_id TEXT NOT NULL REFERENCES productos(id),
    fecha TEXT NOT NULL,
    tipo TEXT NOT NULL,           -- 'declarado' o 'historico'
    descuento REAL NOT NULL,
    precio REAL NOT NULL,
    referencia REAL NOT NULL,     -- precio normal o precio habitual
    PRIMARY KEY (producto_id, fecha, tipo)
);
CREATE INDEX IF NOT EXISTS idx_precios_fecha ON precios(fecha);
CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria);
"""


def conectar(ruta: str | Path) -> sqlite3.Connection:
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ruta)
    con.row_factory = sqlite3.Row
    con.executescript(ESQUEMA)
    return con


def guardar(con: sqlite3.Connection, p: Producto, fecha: str) -> None:
    con.execute(
        """INSERT INTO productos (id, tienda, sku, nombre, url, marca, imagen, categoria, primera_vez, ultima_vez)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET nombre=excluded.nombre, url=excluded.url, marca=excluded.marca,
               imagen=excluded.imagen, categoria=excluded.categoria, ultima_vez=excluded.ultima_vez""",
        (p.id, p.tienda, p.sku, p.nombre, p.url, p.marca, p.imagen, p.categoria, fecha, fecha),
    )
    # Si un producto aparece varias veces el mismo día se guarda el menor precio.
    con.execute(
        """INSERT INTO precios (producto_id, fecha, precio, precio_lista, disponible)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(producto_id, fecha) DO UPDATE SET
               precio_lista = CASE WHEN excluded.precio < precio THEN excluded.precio_lista ELSE precio_lista END,
               disponible = excluded.disponible,
               precio = MIN(precio, excluded.precio)""",
        (p.id, fecha, p.precio, p.precio_lista, int(p.disponible)),
    )


def historial(con: sqlite3.Connection, producto_id: str, desde: str, hasta: str) -> list[float]:
    """Precios entre `desde` (incluido) y `hasta` (excluido)."""
    filas = con.execute(
        "SELECT precio FROM precios WHERE producto_id=? AND fecha>=? AND fecha<? ORDER BY fecha",
        (producto_id, desde, hasta),
    )
    return [f["precio"] for f in filas]
