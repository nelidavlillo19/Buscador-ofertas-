"""Lectura genérica: datos schema.org (JSON-LD) en la página de búsqueda de la tienda.

Si la página se arma con JavaScript, define OFERTAS_NAVEGADOR=1 y instala
`playwright` para renderizarla con Chromium antes de leerla.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from urllib.parse import quote, urljoin

from ..modelos import Producto
from .base import Adaptador

log = logging.getLogger(__name__)

RUTAS_BUSQUEDA = ["/search?q={q}", "/busqueda?ft={q}", "/{q}?_q={q}&map=ft", "/buscar?q={q}"]
PATRON_LDJSON = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I)


def _nodos(dato):
    """Recorre recursivamente el JSON-LD y entrega cada objeto."""
    if isinstance(dato, list):
        for x in dato:
            yield from _nodos(x)
    elif isinstance(dato, dict):
        yield dato
        for clave in ("@graph", "itemListElement", "item", "mainEntity"):
            if clave in dato:
                yield from _nodos(dato[clave])


def _es_producto(nodo: dict) -> bool:
    tipo = nodo.get("@type")
    return tipo == "Product" or (isinstance(tipo, list) and "Product" in tipo)


def _precio(ofertas) -> float | None:
    if isinstance(ofertas, list):
        precios = [_precio(o) for o in ofertas]
        precios = [p for p in precios if p]
        return min(precios) if precios else None
    if not isinstance(ofertas, dict):
        return None
    for clave in ("price", "lowPrice"):
        try:
            v = float(str(ofertas.get(clave)).replace(",", "."))
            if v > 0:
                return v
        except (TypeError, ValueError):
            pass
    return _precio(ofertas.get("offers"))


def extraer_productos(html: str, tienda: str, base: str) -> list[Producto]:
    productos = {}
    for bloque in PATRON_LDJSON.findall(html):
        try:
            dato = json.loads(bloque.strip())
        except ValueError:
            continue
        for nodo in _nodos(dato):
            if not _es_producto(nodo):
                continue
            precio = _precio(nodo.get("offers"))
            if not precio:
                continue
            url = urljoin(base + "/", nodo.get("url") or "")
            sku = str(nodo.get("sku") or nodo.get("productID")
                      or hashlib.md5(url.encode()).hexdigest()[:12])
            marca = nodo.get("brand") or ""
            if isinstance(marca, dict):
                marca = marca.get("name", "")
            imagen = nodo.get("image") or ""
            if isinstance(imagen, list):
                imagen = imagen[0] if imagen else ""
            if isinstance(imagen, dict):
                imagen = imagen.get("url", "")
            ofertas = nodo.get("offers") or {}
            disponible = "OutOfStock" not in json.dumps(ofertas)
            productos[sku] = Producto(tienda=tienda, sku=sku, nombre=nodo.get("name", ""), url=url,
                                      precio=precio, marca=marca, imagen=imagen, disponible=disponible)
    return list(productos.values())


def _renderizar(url: str) -> str | None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.warning("OFERTAS_NAVEGADOR=1 pero playwright no está instalado")
        return None
    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        try:
            pagina = navegador.new_page(locale="es-CL")
            pagina.goto(url, wait_until="networkidle", timeout=45000)
            return pagina.content()
        except Exception as e:  # noqa: BLE001 - cualquier fallo de render se registra y se sigue
            log.warning("No se pudo renderizar %s: %s", url, e)
            return None
        finally:
            navegador.close()


class JsonLd(Adaptador):
    def __init__(self, tienda, cliente):
        super().__init__(tienda, cliente)
        self._ruta = tienda.get("ruta_busqueda")  # se puede fijar en tiendas.yaml

    def _html(self, url: str) -> str | None:
        if os.environ.get("OFERTAS_NAVEGADOR") == "1":
            return _renderizar(url)
        r = self.cliente.get(url)
        return r.text if r is not None else None

    def buscar(self, termino: str) -> list[Producto]:
        rutas = [self._ruta] if self._ruta else RUTAS_BUSQUEDA
        for ruta in rutas:
            html = self._html(self.url + ruta.format(q=quote(termino)))
            productos = extraer_productos(html or "", self.id, self.url)
            if productos:
                self._ruta = ruta  # recordar la ruta que funcionó
                return productos
        return []
