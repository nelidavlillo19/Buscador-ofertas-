"""Detección de ofertas (>= umbral %) y envío de avisos."""
from __future__ import annotations

import logging
import os
import smtplib
import sqlite3
import statistics
from html import escape
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from email.message import EmailMessage

from . import db, unidades
from .red import Cliente

log = logging.getLogger(__name__)

ZONA = ZoneInfo("America/Santiago")
MIN_DIAS_HISTORIAL = 7  # días con precio antes de confiar en el "precio habitual"
DIAS_REFERENCIA = 30    # "precio más bajo de los últimos 30 días" (regla anti ofertas infladas)
MIN_DIAS_REFERENCIA = 3
TOLERANCIA = 0.02       # diferencias de ±2% se consideran el mismo precio
SUBIDA_ALERTA = 0.10    # subida de 10% o más sobre el mínimo de 30 días = "subió de precio"


def minimo_previo(con: sqlite3.Connection, producto_id: str, fecha: str) -> float | None:
    """Precio más bajo de los 30 días anteriores (sin contar hoy), si hay historial suficiente."""
    desde = (date.fromisoformat(fecha) - timedelta(days=DIAS_REFERENCIA)).isoformat()
    previos = db.historial(con, producto_id, desde, fecha)
    return min(previos) if len(previos) >= MIN_DIAS_REFERENCIA else None


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
    nota: str = ""


def detectar(con: sqlite3.Connection, fecha: str, umbral: float, dias_historial: int,
            categorias: dict | None = None, tiendas: dict | None = None) -> list[Alerta]:
    """Dos tipos de alerta:

    * declarado: la tienda muestra precio normal y precio oferta con >= umbral % de diferencia.
    * historico: el precio de hoy es >= umbral % más bajo que la mediana de los últimos
      `dias_historial` días. Detecta ofertas reales aunque la tienda no las anuncie, y
      evita caer en "precios normales" inflados.

    Una categoría puede fijar su propio `umbral_descuento` (p. ej. 1 = avisar cualquier oferta).

    * por_unidad: la categoría tiene `precio_maximo_por_unidad` (p. ej. película Instax a $1.000
      por foto) y el precio dividido por las unidades del pack queda bajo ese valor.
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
        cat_cfg = (categorias or {}).get(f["categoria"], {})
        maximo_unidad = cat_cfg.get("precio_maximo_por_unidad")
        n_unidades = unidades.contar(f["nombre"]) if maximo_unidad else None
        # referencia = precio por unidad redondeado (p. ej. por foto); $999,9 cuenta como $1.000
        if n_unidades and round(f["precio"] / n_unidades) < maximo_unidad:
            candidatos.append(("por_unidad", round(f["precio"] / n_unidades)))
        minimo = minimo_previo(con, f["id"], fecha)
        for tipo, referencia in candidatos:
            nota = ""
            if tipo == "declarado" and minimo:
                if f["precio"] > minimo * (1 + TOLERANCIA):
                    # "Oferta" sobre un precio inflado: hace poco estuvo más barato. No se avisa.
                    continue
                if f["precio"] >= minimo * (1 - TOLERANCIA):
                    nota = "mismo precio de los últimos días (descuento permanente)"
                else:
                    nota = f"precio más bajo en 30 días (antes {_clp(minimo)})"
            if tipo == "por_unidad":
                lista = f["precio_lista"] or 0
                descuento = round(100 * (1 - f["precio"] / lista), 1) if lista > f["precio"] else 0.0
            else:
                descuento = round(100 * (1 - f["precio"] / referencia), 1)
            minimo = (categorias or {}).get(f["categoria"], {}).get("umbral_descuento", umbral)
            if tipo not in ("precio_bajo", "por_unidad") and (descuento <= 0 or descuento < minimo):
                continue
            ya_avisada = con.execute(
                "SELECT 1 FROM alertas WHERE producto_id=? AND tipo=? AND fecha BETWEEN ? AND ? AND precio<=?",
                (f["id"], tipo, ayer, fecha, f["precio"]),
            ).fetchone()
            alertas.append(Alerta(f["id"], tipo, descuento, f["precio"], referencia, f["nombre"],
                                  f["tienda"], f["url"], f["categoria"], nueva=not ya_avisada, nota=nota))
            con.execute(
                "INSERT OR REPLACE INTO alertas VALUES (?, ?, ?, ?, ?, ?)",
                (f["id"], fecha, tipo, descuento, f["precio"], referencia),
            )
    alertas.sort(key=lambda a: -a.descuento)
    return alertas


def vigilancia(con: sqlite3.Connection, fecha: str, umbral: float, categorias: dict | None = None) -> dict:
    """Productos para vigilar antes de eventos como el CyberDay.

    * subidas: hoy cuestan 10%+ más que su precio más bajo de los últimos 30 días.
    * infladas: anuncian un descuento grande, pero hace poco estuvieron más baratos.
    """
    subidas, infladas = [], []
    for f in con.execute(
        """SELECT p.id, p.nombre, p.tienda, p.url, p.categoria, pr.precio, pr.precio_lista
           FROM precios pr JOIN productos p ON p.id = pr.producto_id
           WHERE pr.fecha = ? AND pr.disponible = 1""", (fecha,)
    ).fetchall():
        minimo = minimo_previo(con, f["id"], fecha)
        if not minimo:
            continue
        item = {"producto_id": f["id"], "nombre": f["nombre"], "tienda": f["tienda"], "url": f["url"],
                "categoria": f["categoria"], "precio": f["precio"], "minimo": minimo,
                "precio_lista": f["precio_lista"], "subida": round(100 * (f["precio"] / minimo - 1), 1)}
        if f["precio"] >= minimo * (1 + SUBIDA_ALERTA):
            subidas.append(item)
        lista = f["precio_lista"] or 0
        minimo_cat = (categorias or {}).get(f["categoria"], {}).get("umbral_descuento", umbral)
        if lista > f["precio"] and 100 * (1 - f["precio"] / lista) >= minimo_cat \
                and f["precio"] > minimo * (1 + TOLERANCIA):
            item = dict(item, descuento_anunciado=round(100 * (1 - f["precio"] / lista), 1))
            infladas.append(item)
    subidas.sort(key=lambda x: -x["subida"])
    infladas.sort(key=lambda x: -x["descuento_anunciado"])
    return {"subidas": subidas, "infladas": infladas}


def _clp(valor: float) -> str:
    return "$" + f"{valor:,.0f}".replace(",", ".")


def resumen_markdown(alertas: list[Alerta], fecha: str, categorias: dict) -> str:
    etiquetas = {"declarado": "desc. tienda", "historico": "vs. precio habitual", "precio_bajo": "precio bajo", "por_unidad": "precio por foto"}
    lineas = [f"# Ofertas del {fecha}", ""]
    if not alertas:
        return "\n".join(lineas + ["Hoy no hubo productos con el descuento mínimo."])
    for a in alertas:
        cat = categorias.get(a.categoria, {}).get("nombre", a.categoria)
        marca_nueva = "🆕 " if a.nueva else ""
        lineas.append(
            f"- {marca_nueva}**{insignia(a)}** ({etiquetas[a.tipo]}) [{a.nombre}]({a.url}) — "
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
                 "precio_bajo": "precio bajo", "por_unidad": "precio por foto"}
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


def insignia(a: Alerta) -> str:
    if a.tipo == "por_unidad":
        return f"{_clp(a.referencia)} c/foto"
    return f"-{a.descuento:.0f}%" if a.descuento >= 1 else "precio bajo"


def _fila_html(a: Alerta, categorias: dict, nombres: dict) -> str:
    etiquetas = {"declarado": "descuento de la tienda", "historico": "más barato que lo habitual",
                 "precio_bajo": "precio bajo", "por_unidad": "precio por foto"}
    cat = categorias.get(a.categoria, {}).get("nombre", a.categoria)
    antes = (f' <span style="color:#7a7974;text-decoration:line-through">{_clp(a.referencia)}</span>'
             if a.tipo != "por_unidad" and a.referencia > a.precio else "")
    return f"""
<tr><td style="padding:10px 6px;border-bottom:1px solid #e3e1dc;vertical-align:top;white-space:nowrap">
  <span style="background:#d03b3b;color:#fff;font-weight:bold;padding:3px 8px;border-radius:10px">{insignia(a)}</span>
</td><td style="padding:10px 6px;border-bottom:1px solid #e3e1dc">
  <a href="{escape(a.url)}" style="color:#0b0b0b;font-weight:bold">{escape(a.nombre)}</a><br>
  <span style="font-size:17px;font-weight:bold">{_clp(a.precio)}</span>{antes}<br>
  <span style="color:#52514e;font-size:13px">{escape(nombres.get(a.tienda, a.tienda))} · {escape(cat)} · {etiquetas[a.tipo]}</span>
  {f'<br><span style="color:#7a7974;font-size:12px">{escape(a.nota)}</span>' if a.nota else ""}
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


def _vigilancia_html(vig: dict, nombres: dict, maximo: int = 10) -> str:
    if not vig or not (vig.get("subidas") or vig.get("infladas")):
        return ""
    h = ['<h3>🔍 Vigilancia de precios (ojo con el CyberDay)</h3>',
         '<p style="color:#52514e;font-size:13px">Comparamos con el precio más bajo de los últimos 30 días. '
         'Una oferta real debe quedar bajo ese mínimo.</p>']
    if vig.get("infladas"):
        h.append(f'<h4 style="margin:12px 0 4px">⚠️ Ofertas infladas ({len(vig["infladas"])}): anuncian descuento, '
                 'pero hace poco estuvieron más baratas</h4><ul style="padding-left:18px">')
        h += [f'<li><a href="{escape(i["url"])}">{escape(i["nombre"])}</a> ({escape(nombres.get(i["tienda"], i["tienda"]))}): '
              f'dice -{i["descuento_anunciado"]:.0f}%, hoy {_clp(i["precio"])}, pero estuvo a <b>{_clp(i["minimo"])}</b></li>'
              for i in vig["infladas"][:maximo]]
        h.append("</ul>")
    if vig.get("subidas"):
        h.append(f'<h4 style="margin:12px 0 4px">📈 Subieron de precio ({len(vig["subidas"])})</h4><ul style="padding-left:18px">')
        h += [f'<li><a href="{escape(i["url"])}">{escape(i["nombre"])}</a> ({escape(nombres.get(i["tienda"], i["tienda"]))}): '
              f'hoy {_clp(i["precio"])}, <b>+{i["subida"]:.0f}%</b> sobre su mínimo de {_clp(i["minimo"])}</li>'
              for i in vig["subidas"][:maximo]]
        h.append("</ul>")
    return "".join(h)


def resumen_diario(alertas: list[Alerta], fecha: str, categorias: dict, tiendas: dict,
                   url_panel: str = "", vig: dict | None = None,
                   solo_nuevas: bool = False) -> tuple[str, str, str]:
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
    if solo_nuevas:
        # modo días de ofertas: sólo lo nuevo de esta revisión
        vigentes, vig = {}, None
        asunto = f"🛒 {len(nuevas)} ofertas nuevas ({fecha}, revisión de las {datetime.now(ZONA):%H:%M})"

    # --- texto plano ---
    t = [f"Resumen del {fecha}", f"Revisamos {revisados} productos en {len(tiendas)} tiendas. "
         f"Ofertas vigentes: {total_ofertas} ({len(nuevas)} nuevas).", ""]
    t += [f"  {nombre}: {n} productos{'  (revisar: sin datos)' if n == 0 else ''}" for nombre, n in tiendas.values()]
    if nuevas:
        t += ["", "OFERTAS NUEVAS"] + [f"- {a.nombre}: {_clp(a.precio)} ({insignia(a) if a.tipo == 'por_unidad' else 'antes ' + _clp(a.referencia)}) "
                                      f"{nombres.get(a.tienda, a.tienda)} {a.url}" for a in nuevas]
    if vigentes:
        t += ["", "MEJORES OFERTAS VIGENTES POR CATEGORÍA"]
    for cid in sorted(vigentes, key=lambda c: orden.index(c) if c in orden else 99):
        t.append(categorias.get(cid, {}).get("nombre", cid))
        t += [f"  - {a.nombre}: {_clp(a.precio)} ({insignia(a) if a.tipo == 'por_unidad' else 'antes ' + _clp(a.referencia)}) "
              f"{nombres.get(a.tienda, a.tienda)} {a.url}" for a in vigentes[cid]]
    if vig and vig.get("infladas"):
        t += ["", "OJO: OFERTAS INFLADAS (estuvieron más baratas en los últimos 30 días)"]
        t += [f"  - {i['nombre']}: dice -{i['descuento_anunciado']:.0f}%, hoy {_clp(i['precio'])}, "
              f"estuvo a {_clp(i['minimo'])}" for i in vig["infladas"][:10]]
    if vig and vig.get("subidas"):
        t += ["", "SUBIERON DE PRECIO"]
        t += [f"  - {i['nombre']}: hoy {_clp(i['precio'])} (+{i['subida']:.0f}% sobre {_clp(i['minimo'])})"
              for i in vig["subidas"][:10]]
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
    if vigentes:
        h.append("<h3>⭐ Mejores ofertas vigentes por categoría</h3>")
    for cid in sorted(vigentes, key=lambda c: (not categorias.get(c, {}).get("destacar"),
                                               orden.index(c) if c in orden else 99)):
        h.append(f'<h4 style="margin:16px 0 4px">{escape(categorias.get(cid, {}).get("nombre", cid))}</h4>'
                 '<table style="border-collapse:collapse;width:100%">'
                 + "".join(_fila_html(a, categorias, nombres) for a in vigentes[cid]) + "</table>")
    h.append(_vigilancia_html(vig or {}, nombres))
    h.append(f'<h3>Tiendas revisadas</h3><table style="border-collapse:collapse;font-size:14px">{filas_tiendas}</table>')
    h.append("</div>")
    return asunto, texto, "".join(h)


def notificar(alertas: list[Alerta], fecha: str, categorias: dict, url_panel: str = "",
              tiendas: dict | None = None, vig: dict | None = None, solo_nuevas: bool = False) -> str:
    """Envía el resumen diario por correo (y Telegram si está configurado), haya o no ofertas nuevas.

    Con `solo_nuevas` el correo trae sólo las ofertas nuevas y no se envía si no hay ninguna.
    """
    tiendas = tiendas or {}
    nuevas = seleccionar_para_aviso(alertas, categorias)
    if solo_nuevas and not nuevas:
        return "sin ofertas nuevas: no se envió correo (modo sólo nuevas)"
    asunto, texto, html = resumen_diario(alertas, fecha, categorias, tiendas, url_panel, vig, solo_nuevas)
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


def enviar_correo(asunto: str, texto: str, html: str) -> str:
    """Envía un correo con las credenciales de Gmail/SMTP configuradas. Devuelve el estado."""
    usuario = (os.environ.get("GMAIL_USUARIO") or os.environ.get("SMTP_USUARIO") or "").strip()
    clave = (os.environ.get("GMAIL_CLAVE_APP") or os.environ.get("SMTP_CLAVE") or "").strip()
    if not (usuario and clave):
        return "correo NO configurado"
    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = usuario
    msg["To"] = os.environ.get("CORREO_DESTINO") or usuario
    msg.set_content(texto)
    msg.add_alternative(html, subtype="html")
    with smtplib.SMTP(os.environ.get("SMTP_SERVIDOR") or "smtp.gmail.com", int(os.environ.get("SMTP_PUERTO") or 587)) as s:
        s.starttls()
        s.login(usuario, clave.replace(" ", ""))
        s.send_message(msg)
    return "correo enviado"


def reporte_grupo(con: sqlite3.Connection, fecha: str, cats: dict, nombres: dict, lista: list[Alerta],
                  revisadas: dict, titulo: str, url_panel: str = "", por_categoria: int = 6) -> tuple[str, str, str]:
    """Reporte de un grupo de categorías (p. ej. viaje): ofertas nuevas y mejores precios vigentes."""
    nuevas = seleccionar_para_aviso([a for a in lista if a.categoria in cats], cats)
    hora = datetime.now(ZONA).strftime("%H:%M")
    asunto = f"{titulo} {fecha} {hora}: {len(nuevas)} ofertas nuevas"
    h = [f'<div style="font-family:Arial,sans-serif;max-width:640px;color:#0b0b0b">',
         f'<h2 style="margin-bottom:4px">{escape(titulo)} · {fecha} {hora}</h2>',
         f'<p style="margin-top:0;color:#52514e">Revisamos <b>{sum(revisadas.values())}</b> productos de viaje en '
         f'<b>{len(revisadas)}</b> tiendas · <b>{len(nuevas)}</b> ofertas nuevas</p>']
    t = [f"{titulo} {fecha} {hora}", f"Productos revisados: {sum(revisadas.values())} en {len(revisadas)} tiendas", ""]
    if url_panel:
        h.append(f'<p><a href="{escape(url_panel)}" style="background:#2a78d6;color:#fff;padding:10px 16px;'
                 f'border-radius:8px;text-decoration:none;display:inline-block">Ver panel con gráficos</a></p>')
    if nuevas:
        h.append('<h3>🆕 Ofertas nuevas</h3><table style="border-collapse:collapse;width:100%">'
                 + "".join(_fila_html(a, cats, nombres) for a in nuevas) + "</table>")
        t += ["OFERTAS NUEVAS"] + [f"- {a.nombre}: {_clp(a.precio)} ({insignia(a)}) {a.url}" for a in nuevas] + [""]
    else:
        h.append("<p>No hay ofertas nuevas desde la revisión anterior. Estos son los mejores precios de ahora:</p>")
    for cid, cat in cats.items():
        filas = con.execute(
            """SELECT p.nombre, p.tienda, p.url, pr.precio, pr.precio_lista FROM precios pr
               JOIN productos p ON p.id = pr.producto_id
               WHERE pr.fecha = ? AND p.categoria = ? AND pr.disponible = 1""", (fecha, cid)).fetchall()
        def orden(f):  # primero lo más rebajado, luego lo más barato
            desc = 1 - f["precio"] / f["precio_lista"] if f["precio_lista"] and f["precio_lista"] > f["precio"] else 0
            return (-round(desc, 2), f["precio"])
        mejores = sorted(filas, key=orden)[:por_categoria]
        h.append(f'<h3 style="margin:18px 0 4px">{escape(cat.get("nombre", cid))} '
                 f'<span style="color:#7a7974;font-size:13px;font-weight:normal">({len(filas)} productos)</span></h3>')
        t.append(f"{cat.get('nombre', cid)} ({len(filas)} productos)")
        if not mejores:
            h.append('<p style="color:#7a7974">Sin productos encontrados en esta revisión.</p>')
            continue
        h.append('<table style="border-collapse:collapse;width:100%;font-size:14px">')
        for f in mejores:
            antes = f["precio_lista"] if f["precio_lista"] and f["precio_lista"] > f["precio"] else None
            desc = f' <span style="color:#d03b3b;font-weight:bold">-{100 * (1 - f["precio"] / antes):.0f}%</span>' if antes else ""
            h.append(f'<tr><td style="padding:6px 4px;border-bottom:1px solid #e3e1dc">'
                     f'<a href="{escape(f["url"])}" style="color:#0b0b0b">{escape(f["nombre"])}</a><br>'
                     f'<span style="color:#52514e;font-size:12px">{escape(nombres.get(f["tienda"], f["tienda"]))}</span></td>'
                     f'<td style="padding:6px 4px;border-bottom:1px solid #e3e1dc;text-align:right;white-space:nowrap">'
                     f'<b>{_clp(f["precio"])}</b>{desc}'
                     + (f'<br><span style="color:#7a7974;text-decoration:line-through;font-size:12px">{_clp(antes)}</span>' if antes else "")
                     + "</td></tr>")
            t.append(f"  - {f['nombre']}: {_clp(f['precio'])}" + (f" (antes {_clp(antes)})" if antes else "")
                     + f" {nombres.get(f['tienda'], f['tienda'])} {f['url']}")
        h.append("</table>")
    h.append("</div>")
    return asunto, "\n".join(t) + "\n", "".join(h)
