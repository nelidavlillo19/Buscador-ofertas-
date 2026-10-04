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


def detectar(con: sqlite3.Connection, fecha: str, umbral: float, dias_historial: int,
            categorias: dict | None = None, tiendas: dict | None = None) -> list[Alerta]:
    """Dos tipos de alerta:

    * declarado: la tienda muestra precio normal y precio oferta con >= umbral % de diferencia.
    * historico: el precio de hoy es >= umbral % más bajo que la mediana de los últimos
      `dias_historial` días. Detecta ofertas reales aunque la tienda no las anuncie, y
      evita caer en "precios normales" inflados.

    Una categoría puede fijar su propio `umbral_descuento` (p. ej. 1 = avisar cualquier oferta).

    * precio_bajo: la tienda tiene `alerta_precio_maximo` (p. ej. IKEA 10000) y el producto
      cuesta eso o menos, tenga o no descuento.
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
        limite = (tiendas or {}).get(f["tienda"], {}).get("alerta_precio_maximo")
        if limite and f["precio"] <= limite:
            candidatos.append(("precio_bajo", max(f["precio_lista"] or 0, f["precio"])))
        for tipo, referencia in candidatos:
            descuento = round(100 * (1 - f["precio"] / referencia), 1)
            minimo = (categorias or {}).get(f["categoria"], {}).get("umbral_descuento", umbral)
            if tipo != "precio_bajo" and (descuento <= 0 or descuento < minimo):
                continue
            ya_avisada = con.execute(
                "SELECT 1 FROM alertas WHERE producto_id=? AND tipo=? AND fecha BETWEEN ? AND ? AND precio<=?",
                (f["id"], tipo, ayer, fecha, f["precio"]),
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
    etiquetas = {"declarado": "desc. tienda", "historico": "vs. precio habitual", "precio_bajo": "precio bajo"}
    lineas = [f"# Ofertas del {fecha}", ""]
    if not alertas:
        return "\n".join(lineas + ["Hoy no hubo productos con el descuento mínimo."])
    for a in alertas:
        cat = categorias.get(a.categoria, {}).get("nombre", a.categoria)
        marca_nueva = "🆕 " if a.nueva else ""
        lineas.append(
            f"- {marca_nueva}**{f'-{a.descuento:.0f}%' if a.descuento >= 1 else 'precio bajo'}** ({etiquetas[a.tipo]}) [{a.nombre}]({a.url}) — "
            f"{_clp(a.precio)} (antes {_clp(a.referencia)}) · {a.tienda} · {cat}"
        )
    return "\n".join(lineas) + "\n"


MAX_POR_CATEGORIA = 5


def seleccionar_para_aviso(alertas: list[Alerta], categorias: dict | None = None) -> list[Alerta]:
    """Alertas nuevas, una por producto, y como máximo las 5 mejores por categoría
    (el resto se ve en el panel) para que el correo no sea eterno."""
    mejor: dict[str, Alerta] = {}
    for a in alertas:
        if a.nueva and (a.producto_id not in mejor or a.descuento > mejor[a.producto_id].descuento):
            mejor[a.producto_id] = a
    por_cat: dict[str, list[Alerta]] = {}
    for a in sorted(mejor.values(), key=lambda a: -a.descuento):
        por_cat.setdefault(a.categoria, []).append(a)
    elegidas = [a for lista in por_cat.values() for a in lista[:MAX_POR_CATEGORIA]]
    # categorías con `destacar: true` (p. ej. peluches) van primero
    destacar = lambda a: not (categorias or {}).get(a.categoria, {}).get("destacar", False)  # noqa: E731
    return sorted(elegidas, key=lambda a: (destacar(a), -a.descuento))


def resumen_html(alertas: list[Alerta], fecha: str, categorias: dict, url_panel: str = "") -> str:
    """Correo legible: una fila por oferta, con botón para ver el producto."""
    etiquetas = {"declarado": "descuento de la tienda", "historico": "más barato que lo habitual",
                 "precio_bajo": "precio bajo"}
    filas = []
    for a in alertas:
        cat = categorias.get(a.categoria, {}).get("nombre", a.categoria)
        filas.append(f"""
<tr><td style="padding:12px 8px;border-bottom:1px solid #e3e1dc;vertical-align:top">
  <span style="background:#d03b3b;color:#fff;font-weight:bold;padding:3px 8px;border-radius:10px">{f"-{a.descuento:.0f}%" if a.descuento >= 1 else "precio bajo"}</span>
</td><td style="padding:12px 8px;border-bottom:1px solid #e3e1dc">
  <a href="{escape(a.url)}" style="color:#0b0b0b;font-weight:bold;text-decoration:none">{escape(a.nombre)}</a><br>
  <span style="font-size:18px;font-weight:bold">{_clp(a.precio)}</span>
  <span style="color:#7a7974;text-decoration:line-through">{_clp(a.referencia)}</span><br>
  <span style="color:#52514e;font-size:13px">{escape(a.tienda)} · {escape(cat)} · {etiquetas[a.tipo]}</span>
</td></tr>""")
    boton = (f'<p><a href="{escape(url_panel)}" style="background:#2a78d6;color:#fff;padding:10px 16px;'
             f'border-radius:8px;text-decoration:none">Ver panel con gráficos</a></p>') if url_panel else ""
    return (f'<div style="font-family:Arial,sans-serif;max-width:600px">'
            f'<h2>🛒 Ofertas del {fecha}</h2>'
            f'<table style="border-collapse:collapse;width:100%">{"".join(filas)}</table>{boton}</div>')


def _fila_html(a: Alerta, categorias: dict, nombres: dict) -> str:
    etiquetas = {"declarado": "descuento de la tienda", "historico": "más barato que lo habitual",
                 "precio_bajo": "precio bajo"}
    cat = categorias.get(a.categoria, {}).get("nombre", a.categoria)
    insignia = f"-{a.descuento:.0f}%" if a.descuento >= 1 else "precio bajo"
    antes = (f' <span style="color:#7a7974;text-decoration:line-through">{_clp(a.referencia)}</span>'
             if a.referencia > a.precio else "")
    return f"""
<tr><td style="padding:10px 6px;border-bottom:1px solid #e3e1dc;vertical-align:top;white-space:nowrap">
  <span style="background:#d03b3b;color:#fff;font-weight:bold;padding:3px 8px;border-radius:10px">{insignia}</span>
</td><td style="padding:10px 6px;border-bottom:1px solid #e3e1dc">
  <a href="{escape(a.url)}" style="color:#0b0b0b;font-weight:bold">{escape(a.nombre)}</a><br>
  <span style="font-size:17px;font-weight:bold">{_clp(a.precio)}</span>{antes}<br>
  <span style="color:#52514e;font-size:13px">{escape(nombres.get(a.tienda, a.tienda))} · {escape(cat)} · {etiquetas[a.tipo]}</span>
</td></tr>"""


def _mejores_por_categoria(alertas: list[Alerta], excluir: set, cuantas: int = 3) -> dict[str, list[Alerta]]:
    mejor: dict[str, Alerta] = {}
    for a in alertas:
        if a.producto_id not in excluir and (a.producto_id not in mejor or a.descuento > mejor[a.producto_id].descuento):
            mejor[a.producto_id] = a
    por_cat: dict[str, list[Alerta]] = {}
    for a in sorted(mejor.values(), key=lambda a: (-a.descuento, a.precio)):
        por_cat.setdefault(a.categoria, [])
        if len(por_cat[a.categoria]) < cuantas:
            por_cat[a.categoria].append(a)
    return por_cat


def resumen_diario(alertas: list[Alerta], fecha: str, categorias: dict, tiendas: dict,
                   url_panel: str = "") -> tuple[str, str, str]:
    """Correo diario: qué se revisó, ofertas nuevas y mejores ofertas vigentes por categoría.

    `tiendas` = {id: (nombre, productos revisados)}. Devuelve (asunto, texto, html).
    """
    nombres = {k: v[0] for k, v in tiendas.items()}
    nuevas = seleccionar_para_aviso(alertas, categorias)
    total_ofertas = len({a.producto_id for a in alertas})
    revisados = sum(n for _, n in tiendas.values())
    orden = list(categorias)
    vigentes = _mejores_por_categoria(alertas, {a.producto_id for a in nuevas})

    asunto = (f"🛒 {len(nuevas)} ofertas nuevas · {total_ofertas} vigentes ({fecha})" if nuevas
              else f"🛒 Resumen del {fecha}: {total_ofertas} ofertas vigentes")

    # --- texto plano ---
    t = [f"Resumen del {fecha}", f"Revisamos {revisados} productos en {len(tiendas)} tiendas. "
         f"Ofertas vigentes: {total_ofertas} ({len(nuevas)} nuevas).", ""]
    t += [f"  {nombre}: {n} productos{'  (revisar: sin datos)' if n == 0 else ''}" for nombre, n in tiendas.values()]
    if nuevas:
        t += ["", "OFERTAS NUEVAS"] + [f"- {a.nombre}: {_clp(a.precio)} (antes {_clp(a.referencia)}) "
                                      f"{nombres.get(a.tienda, a.tienda)} {a.url}" for a in nuevas]
    t += ["", "MEJORES OFERTAS VIGENTES POR CATEGORÍA"]
    for cid in sorted(vigentes, key=lambda c: orden.index(c) if c in orden else 99):
        t.append(categorias.get(cid, {}).get("nombre", cid))
        t += [f"  - {a.nombre}: {_clp(a.precio)} (antes {_clp(a.referencia)}) "
              f"{nombres.get(a.tienda, a.tienda)} {a.url}" for a in vigentes[cid]]
    if url_panel:
        t += ["", f"Panel con gráficos: {url_panel}"]
    texto = "\n".join(t) + "\n"

    # --- HTML ---
    filas_tiendas = "".join(
        f'<tr><td style="padding:3px 10px 3px 0">{escape(nombre)}</td>'
        f'<td style="padding:3px 0;text-align:right">{n}{" ⚠️" if n == 0 else ""}</td></tr>'
        for nombre, n in tiendas.values())
    h = [f'<div style="font-family:Arial,sans-serif;max-width:640px;color:#0b0b0b">',
         f'<h2 style="margin-bottom:4px">🛒 Resumen del {fecha}</h2>',
         f'<p style="margin-top:0;color:#52514e">Revisamos <b>{revisados}</b> productos en <b>{len(tiendas)}</b> '
         f'tiendas · <b>{total_ofertas}</b> ofertas vigentes · <b>{len(nuevas)}</b> nuevas hoy</p>']
    if url_panel:
        h.append(f'<p><a href="{escape(url_panel)}" style="background:#2a78d6;color:#fff;padding:10px 16px;'
                 f'border-radius:8px;text-decoration:none;display:inline-block">Ver panel con gráficos y todos los precios</a></p>')
    if nuevas:
        h.append('<h3>🆕 Ofertas nuevas de hoy</h3><table style="border-collapse:collapse;width:100%">'
                 + "".join(_fila_html(a, categorias, nombres) for a in nuevas) + "</table>")
    else:
        h.append("<p>Hoy no aparecieron ofertas nuevas; estas son las mejores que siguen vigentes.</p>")
    h.append("<h3>⭐ Mejores ofertas vigentes por categoría</h3>")
    for cid in sorted(vigentes, key=lambda c: (not categorias.get(c, {}).get("destacar"),
                                               orden.index(c) if c in orden else 99)):
        h.append(f'<h4 style="margin:16px 0 4px">{escape(categorias.get(cid, {}).get("nombre", cid))}</h4>'
                 '<table style="border-collapse:collapse;width:100%">'
                 + "".join(_fila_html(a, categorias, nombres) for a in vigentes[cid]) + "</table>")
    h.append(f'<h3>Tiendas revisadas</h3><table style="border-collapse:collapse;font-size:14px">{filas_tiendas}</table>')
    h.append("</div>")
    return asunto, texto, "".join(h)


def notificar(alertas: list[Alerta], fecha: str, categorias: dict, url_panel: str = "",
              tiendas: dict | None = None) -> str:
    """Envía el resumen diario por correo (y Telegram si está configurado), haya o no ofertas nuevas."""
    tiendas = tiendas or {}
    asunto, texto, html = resumen_diario(alertas, fecha, categorias, tiendas, url_panel)
    nuevas = seleccionar_para_aviso(alertas, categorias)
    estado = []

    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat:
        cliente = Cliente(pausa=0.5)
        # Telegram limita los mensajes a 4096 caracteres
        for i in range(0, len(texto), 3800):
            cliente.sesion.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=20, data={
                "chat_id": chat, "text": texto[i:i + 3800], "disable_web_page_preview": "true",
            })
        estado.append("Telegram enviado")

    # Gmail simple (GMAIL_USUARIO + GMAIL_CLAVE_APP) o un servidor SMTP cualquiera
    usuario = (os.environ.get("GMAIL_USUARIO") or os.environ.get("SMTP_USUARIO") or "").strip()
    clave = (os.environ.get("GMAIL_CLAVE_APP") or os.environ.get("SMTP_CLAVE") or "").strip()
    if usuario and clave:
        servidor = os.environ.get("SMTP_SERVIDOR") or "smtp.gmail.com"
        destino = os.environ.get("CORREO_DESTINO") or usuario
        msg = EmailMessage()
        msg["Subject"] = asunto
        msg["From"] = usuario
        msg["To"] = destino
        msg.set_content(texto)
        msg.add_alternative(html, subtype="html")
        with smtplib.SMTP(servidor, int(os.environ.get("SMTP_PUERTO") or 587)) as s:
            s.starttls()
            s.login(usuario, clave.replace(" ", ""))
            s.send_message(msg)
        log.info("Resumen enviado por correo (%d ofertas nuevas)", len(nuevas))
        estado.append(f"correo enviado ({len(nuevas)} ofertas nuevas)")
    elif not estado:
        faltan = [n for n, v in (("GMAIL_USUARIO", usuario), ("GMAIL_CLAVE_APP", clave)) if not v]
        estado.append(f"correo NO configurado (falta: {', '.join(faltan)})")
    return ", ".join(estado)
