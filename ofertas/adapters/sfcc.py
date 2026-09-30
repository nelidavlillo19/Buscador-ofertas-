"""Tiendas Salesforce Commerce Cloud (p. ej. SuperZoo): tarjetas de producto en /buscar."""
from __future__ import annotations

import html
import re
from urllib.parse import quote, urljoin

from ..modelos import Producto
from .base import Adaptador

TARJETA = re.compile(r'<div class="product" data-pid="([^"]+)"(.*?)<!-- END_dwmarker -->', re.S)


def _valores(fragmento: str) -> list[float]:
    return [float(v) for v in re.findall(r'<span class="value" content="([\d.]+)"', fragmento)]


def extraer(pagina: str, tienda: str, base: str) -> list[Producto]:
    productos = []
    for pid, bloque in TARJETA.findall(pagina):
        nombre = re.search(r'<div class="pdp-link">.*?<h2[^>]*>(.*?)</h2>', bloque, re.S)
        enlace = re.search(r'<div class="pdp-link">\s*<a[^>]+href="([^"]+)"', bloque, re.S)
        precio_html = re.search(r'<div class="price">(.*?)</div>', bloque, re.S)
        if not (nombre and precio_html):
            continue
        precios = precio_html.group(1)
        lista = re.search(r'strike-through list.*?content="([\d.]+)"', precios, re.S)
        ventas = _valores(re.sub(r"<del>.*?</del>", "", precios, flags=re.S))
        if not ventas:
            continue
        # Un rango "desde - hasta" son distintos tamaños, no un descuento: se sigue el menor.
        precio = min(ventas)
        marca = re.search(r'class="product-brand[^"]*">\s*(.*?)\s*<', bloque, re.S)
        imagen = re.search(r'<img class="tile-image"\s+src="([^"]+)"', bloque, re.S)
        productos.append(Producto(
            tienda=tienda, sku=pid, nombre=html.unescape(nombre.group(1).strip()),
            url=urljoin(base + "/", enlace.group(1)) if enlace else base,
            precio=precio, precio_lista=float(lista.group(1)) if lista else None,
            marca=html.unescape(marca.group(1)) if marca else "",
            imagen=urljoin(base + "/", imagen.group(1)) if imagen else "",
        ))
    return productos


class Sfcc(Adaptador):
    def buscar(self, termino: str) -> list[Producto]:
        r = self.cliente.get(f"{self.url}/buscar?q={quote(termino)}&sz=48")
        return extraer(r.text, self.id, self.url) if r is not None else []
