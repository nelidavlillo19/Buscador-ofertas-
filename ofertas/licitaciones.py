"""Licitaciones de Mercado Público (API de ChileCompra) para consultoría, auditoría, impuestos y educación.

Flujo: 1) baja la lista de licitaciones activas (código, nombre, cierre); 2) filtra por palabras del nombre;
3) consulta el detalle de las candidatas para saber el organismo comprador, región y monto; 4) deja las de
ministerios, subsecretarías y servicios de educación; 5) avisa por correo sólo las que no se habían visto.

API: https://api.mercadopublico.cl  (ticket gratuito; se pasa como parámetro ?ticket=...)
"""
from __future__ import annotations

import html
import json
import logging
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

API = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
URL_FICHA = "https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={}"


def normalizar(texto: str) -> str:
    """minúsculas y sin tildes, para comparar palabras."""
    t = unicodedata.normalize("NFKD", (texto or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def contiene(texto: str, palabras: list[str]) -> bool:
    t = normalizar(texto)
    return any(normalizar(p) in t for p in palabras)


@dataclass
class Licitacion:
    codigo: str
    nombre: str
    cierre: str = ""
    organismo: str = ""
    unidad: str = ""
    region: str = ""
    tipo: str = ""
    monto: float | None = None
    moneda: str = ""
    descripcion: str = ""

    @property
    def url(self) -> str:
        return URL_FICHA.format(self.codigo)


def candidatas(listado: list[dict], config: dict) -> list[Licitacion]:
    """Primer filtro, sólo por el nombre (la lista de activas no trae el organismo)."""
    claves, excluir = config.get("palabras_clave", []), config.get("excluir", [])
    salida = []
    for item in listado:
        nombre = item.get("Nombre") or ""
        if contiene(nombre, claves) and not contiene(nombre, excluir):
            salida.append(Licitacion(codigo=item.get("CodigoExterno", ""), nombre=nombre.strip(),
                                     cierre=(item.get("FechaCierre") or "")[:16]))
    return salida


def completar(lic: Licitacion, detalle: dict) -> Licitacion:
    """Agrega organismo, región, tipo y monto desde el detalle de la API."""
    comprador = detalle.get("Comprador") or {}
    lic.organismo = (comprador.get("NombreOrganismo") or "").strip()
    lic.unidad = (comprador.get("NombreUnidad") or "").strip()
    lic.region = (comprador.get("RegionUnidad") or "").strip()
    lic.tipo = detalle.get("Tipo") or ""
    monto = detalle.get("MontoEstimado")
    lic.monto = float(monto) if isinstance(monto, (int, float)) and monto > 0 else None
    lic.moneda = detalle.get("Moneda") or ""
    lic.descripcion = (detalle.get("Descripcion") or "").strip()
    cierre = (detalle.get("Fechas") or {}).get("FechaCierre")
    if cierre:
        lic.cierre = cierre[:16]
    return lic


def es_de_interes(lic: Licitacion, config: dict) -> bool:
    return contiene(f"{lic.organismo} {lic.unidad}", config.get("organismos", []))


def ordenar(lista: list[Licitacion], config: dict) -> list[Licitacion]:
    destacadas = config.get("regiones_destacadas", [])
    return sorted(lista, key=lambda l: (not contiene(l.region, destacadas), l.cierre or "9999"))


# ---------------------------------------------------------------- consulta a la API

class ErrorApi(RuntimeError):
    pass


def _pedir(sesion, params: dict, intentos: int = 4) -> dict:
    """GET a la API con reintentos (responde error si se consulta muy seguido)."""
    for n in range(intentos):
        try:
            r = sesion.get(API, params=params, timeout=60)
            datos = r.json()
        except Exception as e:  # noqa: BLE001 - red, JSON inválido
            log.warning("Mercado Público: %s (intento %s)", e, n + 1)
        else:
            if r.status_code == 200 and "Listado" in datos:
                return datos
            mensaje = datos.get("Mensaje") if isinstance(datos, dict) else str(datos)[:200]
            if "ticket" in normalizar(str(mensaje)):
                raise ErrorApi(f"problema con el ticket: {mensaje}")
            log.warning("Mercado Público respondió %s: %s (intento %s)", r.status_code, mensaje, n + 1)
        time.sleep(3 * (n + 1))
    raise ErrorApi("Mercado Público no respondió después de varios intentos")


def buscar(ticket: str, config: dict, pausa: float = 1.2) -> tuple[list[Licitacion], int]:
    """Licitaciones activas de interés. Devuelve (lista, total de activas revisadas)."""
    import requests

    sesion = requests.Session()
    sesion.headers["User-Agent"] = "buscador-ofertas (licitaciones)"
    activas = _pedir(sesion, {"estado": "activas", "ticket": ticket}).get("Listado") or []
    lista = candidatas(activas, config)
    maximo = int(config.get("max_detalles", 400))
    if len(lista) > maximo:
        log.warning("%s candidatas; se revisa el detalle de las primeras %s", len(lista), maximo)
        lista = lista[:maximo]
    log.info("%s licitaciones activas, %s candidatas por nombre", len(activas), len(lista))

    salida = []
    for lic in lista:
        time.sleep(pausa)
        try:
            datos = _pedir(sesion, {"codigo": lic.codigo, "ticket": ticket}, intentos=2)
        except ErrorApi as e:
            log.warning("Sin detalle de %s: %s", lic.codigo, e)
            continue
        if datos.get("Listado"):
            completar(lic, datos["Listado"][0])
            if es_de_interes(lic, config):
                salida.append(lic)
    return ordenar(salida, config), len(activas)


# ---------------------------------------------------------------- estado y correo

def cargar_vistas(ruta: Path) -> dict:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def guardar_vistas(ruta: Path, vistas: dict, vigentes: list[Licitacion], fecha: str) -> None:
    """Recuerda cada licitación vista (código -> fecha en que se vio por primera vez)."""
    for lic in vigentes:
        vistas.setdefault(lic.codigo, fecha)
    # olvida las vistas hace más de 120 días para que el archivo no crezca sin fin
    limite = _restar_dias(fecha, 120)
    vistas = {k: v for k, v in vistas.items() if v >= limite}
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(vistas, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _restar_dias(fecha: str, dias: int) -> str:
    from datetime import date, timedelta
    return (date.fromisoformat(fecha) - timedelta(days=dias)).isoformat()


def _monto(lic: Licitacion) -> str:
    if lic.monto is None:
        return "monto no informado"
    return f"${lic.monto:,.0f}".replace(",", ".") + (f" {lic.moneda}" if lic.moneda and lic.moneda != "CLP" else "")


def correo(nuevas: list[Licitacion], vigentes: int, fecha: str) -> tuple[str, str, str]:
    asunto = f"🏛️ {len(nuevas)} licitación(es) nueva(s) de consultoría y educación — {fecha}"
    texto = [asunto, ""]
    filas = []
    for lic in nuevas:
        texto += [f"- {lic.nombre}", f"  {lic.organismo} · {lic.region} · {lic.tipo} · {_monto(lic)}",
                  f"  Cierra: {lic.cierre.replace('T', ' ')} · {lic.url}", ""]
        e = html.escape
        filas.append(
            f"<tr><td style='padding:8px;border-bottom:1px solid #ddd'>"
            f"<a href='{e(lic.url)}'><b>{e(lic.nombre)}</b></a><br>"
            f"<small>{e(lic.organismo)}{' · ' + e(lic.unidad) if lic.unidad else ''}</small><br>"
            f"<small>{e(lic.descripcion[:260])}{'…' if len(lic.descripcion) > 260 else ''}</small></td>"
            f"<td style='padding:8px;border-bottom:1px solid #ddd'>{e(lic.region)}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #ddd'>{e(lic.tipo)}<br>{e(_monto(lic))}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #ddd;white-space:nowrap'>"
            f"{e(lic.cierre.replace('T', ' '))}</td></tr>")
    texto.append(f"Licitaciones de interés vigentes hoy: {vigentes}.")
    cuerpo = (
        f"<h2>{html.escape(asunto)}</h2>"
        "<table style='border-collapse:collapse;font-family:sans-serif;font-size:14px'>"
        "<tr><th align='left'>Licitación</th><th align='left'>Región</th><th align='left'>Tipo y monto</th>"
        "<th align='left'>Cierre</th></tr>" + "".join(filas) + "</table>"
        f"<p><small>Licitaciones de interés vigentes hoy: {vigentes}. Confirma siempre las bases y "
        "plazos en mercadopublico.cl. Para cambiar lo que se busca, edita config/licitaciones.yaml.</small></p>")
    return asunto, "\n".join(texto), cuerpo


def estado_markdown(vigentes: list[Licitacion], fecha: str, activas: int) -> str:
    lineas = [f"# Licitaciones de interés vigentes ({fecha})", "",
              f"Revisadas {activas} licitaciones activas en Mercado Público; {len(vigentes)} de interés.", "",
              "| Cierre | Licitación | Organismo | Región | Tipo |", "|---|---|---|---|---|"]
    for lic in vigentes:
        nombre = lic.nombre.replace("|", "/")
        lineas.append(f"| {lic.cierre.replace('T', ' ')} | [{nombre}]({lic.url}) | "
                      f"{lic.organismo.replace('|', '/')} | {lic.region} | {lic.tipo} |")
    return "\n".join(lineas) + "\n"
