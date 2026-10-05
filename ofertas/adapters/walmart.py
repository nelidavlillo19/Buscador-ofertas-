"""Líder (Walmart Chile): los resultados de búsqueda vienen en el JSON __NEXT_DATA__ de super.lider.cl."""
from __future__ import annotations

import json
import re
from urllib.parse import quote

from ..modelos import Producto
from .base import Adaptador

NEXT_DATA = re.compile(r'<script id="?__NEXT_DATA__"?[^>]*>(.*?)</script>', re.S)


def _monto(texto) -> float | None:
    if isinstance(texto, (int, float)):
        return float(texto) or None
    digitos = re.sub(r"[^\d]", "", str(texto or ""))
    return float(digitos) if digitos else None


def extraer(pagina: str, tienda: str, base: str) -> list[Producto]:
    m = NEXT_DATA.search(pagina)
    if not m:
        return []
    try:
        pilas = json.loads(m.group(1))["props"]["pageProps"]["initialData"]["searchResult"]["itemStacks"]
    except (ValueError, KeyError, TypeError):
        return []
    productos = []
    for pila in pilas or []:
        for it in pila.get("items") or []:
            nombre = (it.get("name") or "").strip()
            if not nombre:  # los agotados vienen sin nombre
                continue
            info = it.get("priceInfo") or {}
            precio = _monto(info.get("linePrice")) or _monto(it.get("price"))
            if not precio:
                continue
            antes = _monto(info.get("wasPrice"))
            url = it.get("canonicalUrl") or f"/ip/{it.get('usItemId')}"
            productos.append(Producto(
                tienda=tienda, sku=str(it.get("usItemId")), nombre=nombre,
                url=url if url.startswith("http") else base + url,
                precio=precio, precio_lista=antes if antes and antes > precio else None,
                marca=it.get("brand") or "", imagen=it.get("image") or "",
                disponible=not it.get("isOutOfStock", False),
            ))
    return productos


class Walmart(Adaptador):
    def buscar(self, termino: str) -> list[Producto]:
        r = self.cliente.get(f"{self.url}/search?q={quote(termino)}&ps=44")
        return extraer(r.text, self.id, self.url) if r is not None else []
