"""Detección de ofertas (>= umbral %) y envío de avisos."""
from __future__ import annotations

import logging
import os
import smtplib
import sqlite3
import statistics
from html import escape
from dataclasses import dataclass
from datetime import date, timedelta
from email.message import EmailMessage

from . import db
from .red import Cliente

log = logging.getLogger(__name__)

MIN_DIAS_HISTORIAL = 7  # días con precio antes de confiar en el "precio habitual"


@dataclass
class Alerta:
    producto_id: str
    tipo: str
    descuento: float
    precio: float
    referencia: float
    nombre: str = ""
    tienda: str = ""
    url: str = ""
    categoria: str = ""
    nueva: bool = True


def detectar(con: sqlite3.Connection, fecha: str, umbral: float, dias_historial: int) -> list[Alerta]:
    """Dos tipos de alerta:

    * declarado: la tienda muestra precio normal y precio oferta con >= umbral % de diferencia.
    * historico: el precio de hoy es >= umbral % más bajo que la mediana de los últimos
      `dias_historial` días. Detecta ofertas reales aunque la tienda no las anuncie, y
      evita caer en "precios normales" inflados.
    """
    hoy = date.fromisoformat(fecha)
    desde = (hoy - timedelta(days=dias_historial)).isoformat()
    ayer = (hoy - timedelta(days=1)).isoformat()
    filas = con.execute(
        """SELECT p.id, p.nombre, p.tienda, p.url, p.categoria, pr.precio, pr.precio_lista
           FROM precios pr JOIN productos p ON p.id = pr.producto_id
           WHERE pr.fecha = ? AND pr.disponible = 1""",
        (fecha,),
    ).fetchall()

    alertas = []
    for f in filas:
        candidatos = []
        if f["precio_lista"] and f["precio_lista"] > f["precio"]:
            candidatos.append(("declarado", f["precio_lista"]))
        previos = db.historial(con, f["id"], desde, fecha)
        if len(previos) >= MIN_DIAS_HISTORIAL:
            candidatos.append(("historico", statistics.median(previos)))
        for tipo, referencia in candidatos:
            descuento = round(100 * (1 - f["precio"] / referencia), 1)
            if descuento < umbral:
                continue
            ya_avisada = con.execute(
                "SELECT 1 FROM alertas WHERE producto_id=? AND tipo=? AND fecha=? AND precio<=?",
                (f["id"], tipo, ayer, f["precio"]),
            ).fetchone()
            alertas.append(Alerta(f["id"], tipo, descuento, f["precio"], referencia, f["nombre"],
                                  f["tienda"], f["url"], f["categoria"], nueva=not ya_avisada))
            con.execute(
                "INSERT OR REPLACE INTO alertas VALUES (?, ?, ?, ?, ?, ?)",
                (f["id"], fecha, tipo, descuento, f["precio"], referencia),
            )
    alertas.sort(key=lambda a: -a.descuento)
    return alertas


def _clp(valor: float) -> str:
    return "$" + f"{valor:,.0f}".replace(",", ".")


def resumen_markdown(alertas: list[Alerta], fecha: str, categorias: dict) -> str:
    etiquetas = {"declarado": "desc. tienda", "historico": "vs. precio habitual"}
    lineas = [f"# Ofertas del {fecha}", ""]
    if not alertas:
        return "\n".join(lineas + ["Hoy no hubo productos con el descuento mínimo."])
    for a in alertas:
        cat = categorias.get(a.categoria, {}).get("nombre", a.categoria)
        marca_nueva = "🆕 " if a.nueva else ""
        lineas.append(
            f"- {marca_nueva}**-{a.descuento:.0f}%** ({etiquetas[a.tipo]}) [{a.nombre}]({a.url}) — "
            f"{_clp(a.precio)} (antes {_clp(a.referencia)}) · {a.tienda} · {cat}"
        )
    return "\n".join(lineas) + "\n"


def resumen_html(alertas: list[Alerta], fecha: str, categorias: dict, url_panel: str = "") -> str:
    """Correo legible: una fila por oferta, con botón para ver el producto."""
    etiquetas = {"declarado": "descuento de la tienda", "historico": "más barato que lo habitual"}
    filas = []
    for a in alertas:
        cat = categorias.get(a.categoria, {}).get("nombre", a.categoria)
        filas.append(f"""
<tr><td style="padding:12px 8px;border-bottom:1px solid #e3e1dc;vertical-align:top">
  <span style="background:#d03b3b;color:#fff;font-weight:bold;padding:3px 8px;border-radius:10px">-{a.descuento:.0f}%</span>
</td><td style="padding:12px 8px;border-bottom:1px solid #e3e1dc">
  <a href="{escape(a.url)}" style="color:#0b0b0b;font-weight:bold;text-decoration:none">{escape(a.nombre)}</a><br>
  <span style="font-size:18px;font-weight:bold">{_clp(a.precio)}</span>
  <span style="color:#7a7974;text-decoration:line-through">{_clp(a.referencia)}</span><br>
  <span style="color:#52514e;font-size:13px">{escape(a.tienda)} · {escape(cat)} · {etiquetas[a.tipo]}</span>
</td></tr>""")
    boton = (f'<p><a href="{escape(url_panel)}" style="background:#2a78d6;color:#fff;padding:10px 16px;'
             f'border-radius:8px;text-decoration:none">Ver panel con gráficos</a></p>') if url_panel else ""
    return (f'<div style="font-family:Arial,sans-serif;max-width:600px">'
            f'<h2>🛒 Ofertas de 30% o más — {fecha}</h2>'
            f'<table style="border-collapse:collapse;width:100%">{"".join(filas)}</table>{boton}</div>')


def notificar(alertas: list[Alerta], fecha: str, categorias: dict, url_panel: str = "") -> None:
    """Envía sólo las alertas nuevas por Telegram y/o correo, si están configurados."""
    nuevas = [a for a in alertas if a.nueva]
    if not nuevas:
        log.info("Sin alertas nuevas que notificar")
        return
    texto = resumen_markdown(nuevas, fecha, categorias)
    if url_panel:
        texto += f"\nPanel: {url_panel}\n"

    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat:
        cliente = Cliente(pausa=0.5)
        # Telegram limita los mensajes a 4096 caracteres
        for i in range(0, len(texto), 3800):
            cliente.sesion.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=20, data={
                "chat_id": chat, "text": texto[i:i + 3800], "parse_mode": "Markdown",
                "disable_web_page_preview": "true",
            })
        log.info("Enviadas %d alertas por Telegram", len(nuevas))

    servidor = os.environ.get("SMTP_SERVIDOR")
    if servidor and os.environ.get("CORREO_DESTINO"):
        msg = EmailMessage()
        msg["Subject"] = f"🛒 {len(nuevas)} ofertas nuevas de 30% o más ({fecha})"
        msg["From"] = os.environ.get("SMTP_USUARIO", "")
        msg["To"] = os.environ["CORREO_DESTINO"]
        msg.set_content(texto)
        msg.add_alternative(resumen_html(nuevas, fecha, categorias, url_panel), subtype="html")
        with smtplib.SMTP(servidor, int(os.environ.get("SMTP_PUERTO", "587"))) as s:
            s.starttls()
            s.login(os.environ["SMTP_USUARIO"], os.environ["SMTP_CLAVE"])
            s.send_message(msg)
        log.info("Enviadas %d alertas por correo", len(nuevas))
