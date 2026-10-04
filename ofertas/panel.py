"""Genera el panel web estático (HTML + data.json) con estadísticas y gráficos."""
from __future__ import annotations

import json
import shutil
import sqlite3
import statistics
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from . import alertas as mod_alertas

PLANTILLA = Path(__file__).resolve().parent.parent / "web" / "index.html"
DIAS_GRAFICO = 180


def exportar(con: sqlite3.Connection, fecha: str, config: dict, salida: Path, demo: bool = False) -> Path:
    hoy = date.fromisoformat(fecha)
    desde = (hoy - timedelta(days=DIAS_GRAFICO)).isoformat()
    # "habitual" = mediana de la misma ventana que usan las alertas
    desde_habitual = (hoy - timedelta(days=config["productos"].get("dias_historial", 60))).isoformat()

    series: dict[str, list] = defaultdict(list)
    for f in con.execute(
        "SELECT producto_id, fecha, precio, precio_lista FROM precios WHERE fecha>=? ORDER BY fecha", (desde,)
    ):
        series[f["producto_id"]].append([f["fecha"], f["precio"], f["precio_lista"]])

    productos = []
    for p in con.execute("SELECT * FROM productos WHERE ultima_vez>=?", (desde,)):
        serie = series.get(p["id"])
        if not serie:
            continue
        precios = [s[1] for s in serie]
        ultimo = serie[-1]
        productos.append({
            "id": p["id"], "n": p["nombre"], "t": p["tienda"], "c": p["categoria"], "m": p["marca"],
            "u": p["url"], "img": p["imagen"],
            "p": ultimo[1], "pl": ultimo[2], "f": ultimo[0], "vigente": ultimo[0] == fecha,
            "min": min(precios), "max": max(precios),
            "med": statistics.median([s[1] for s in serie if s[0] >= desde_habitual] or precios),
            "h": [[s[0], s[1]] for s in serie],
        })

    alertas = [dict(a) for a in con.execute(
        """SELECT a.*, p.nombre, p.tienda, p.url, p.categoria, p.imagen FROM alertas a
           JOIN productos p ON p.id = a.producto_id WHERE a.fecha >= ?
           ORDER BY a.fecha DESC, a.descuento DESC""",
        ((hoy - timedelta(days=30)).isoformat(),),
    )]
    por_dia = [dict(f) for f in con.execute(
        """SELECT fecha, COUNT(DISTINCT producto_id) AS n FROM alertas WHERE fecha>=?
           GROUP BY fecha ORDER BY fecha""", (desde,))]

    datos = {
        "generado": datetime.now().isoformat(timespec="minutes"),
        "fecha": fecha,
        "demo": demo,
        "umbral": config["productos"].get("umbral_descuento", 30),
        "categorias": {k: v.get("nombre", k) for k, v in config["productos"]["categorias"].items()},
        "tiendas": {t["id"]: t["nombre"] for t in config["tiendas"]},
        "productos": productos,
        "alertas": alertas,
        "alertas_por_dia": por_dia,
        "vigilancia": mod_alertas.vigilancia(con, fecha, config["productos"].get("umbral_descuento", 30),
                                             config["productos"]["categorias"]),
    }
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "data.json").write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")),
                                      encoding="utf-8")
    shutil.copy(PLANTILLA, salida / "index.html")
    return salida / "index.html"
