"""Falabella: los resultados de búsqueda vienen en el JSON __NEXT_DATA__ de la página."""
from __future__ import annotations

import json
import re
from urllib.parse import quote

from ..modelos import Producto
from .base import Adaptador

NEXT_DATA = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


def _monto(valores) -> float | None:
    try:
        return float(str(valores[0]).replace(".", "").replace(",", "."))
    except (IndexError, TypeError, ValueError):
        return None


def extraer(pagina: str, tienda: str) -> list[Producto]:
    m = NEXT_DATA.search(pagina)
    if not m:
        return []
    try:
        resultados = json.loads(m.group(1))["props"]["pageProps"].get("results") or []
    except (ValueError, KeyError):
        return []
    productos = []
    for r in resultados:
        # cmrPrice exige tarjeta CMR; se usa el mejor precio para todo público
        vigentes = [_monto(p.get("price")) for p in r.get("prices", [])
                    if not p.get("crossed") and p.get("type") != "cmrPrice"]
        tachados = [_monto(p.get("price")) for p in r.get("prices", []) if p.get("crossed")]
        vigentes = [v for v in vigentes if v]
        if not vigentes:
            continue
        vendedor = r.get("sellerName") or ""
        productos.append(Producto(
            tienda=tienda, sku=str(r.get("skuId") or r.get("productId")),
            nombre=r.get("displayName", "") + (f" (vende {vendedor})" if vendedor and vendedor != "Falabella" else ""),
            url=r.get("url", ""), precio=min(vigentes),
            precio_lista=max([t for t in tachados if t], default=None),
            marca=r.get("brand", ""), imagen=(r.get("mediaUrls") or [""])[0],
        ))
    return productos


class Falabella(Adaptador):
    def buscar(self, termino: str) -> list[Producto]:
        r = self.cliente.get(f"{self.url}/search?Ntt={quote(termino)}")
        return extraer(r.text, self.id) if r is not None else []
