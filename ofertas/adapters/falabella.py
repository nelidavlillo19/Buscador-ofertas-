"""Falabella y Sodimac: los resultados de búsqueda vienen en el JSON __NEXT_DATA__ de la página."""
from __future__ import annotations

import json
import re
import unicodedata
from urllib.parse import quote

from ..modelos import Producto
from .base import Adaptador

NEXT_DATA = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


def _monto(precio: dict) -> float | None:
    if precio.get("priceWithoutFormatting"):
        return float(precio["priceWithoutFormatting"])
    valor = precio.get("price")
    if isinstance(valor, list):
        valor = valor[0] if valor else None
    try:
        return float(str(valor).replace(".", "").replace(",", "."))
    except (TypeError, ValueError):
        return None


def _slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", texto).strip("-")


def extraer(pagina: str, tienda: str, base: str = "") -> list[Producto]:
    m = NEXT_DATA.search(pagina)
    if not m:
        return []
    try:
        props = json.loads(m.group(1))["props"]["pageProps"]
    except (ValueError, KeyError):
        return []
    # Falabella: pageProps.results · Sodimac: pageProps.searchProps.searchData.results
    resultados = props.get("results") or ((props.get("searchProps") or {}).get("searchData") or {}).get("results") or []
    productos = []
    for r in resultados:
        precios = r.get("prices", [])
        # los precios CMR exigen tarjeta; se usa el mejor precio para todo público
        abiertos = [p for p in precios if "cmr" not in str(p.get("type", "")).lower()]
        vigentes = [_monto(p) for p in abiertos if not p.get("crossed")]
        tachados = [_monto(p) for p in abiertos if p.get("crossed")]
        vigentes = [v for v in vigentes if v]
        if not vigentes:
            continue
        if not any(p.get("crossed") for p in precios) and len(vigentes) > 1:
            # Sodimac no marca el precio tachado: el mayor es el normal
            tachados, vigentes = [max(vigentes)], [min(vigentes)]
        vendedor = r.get("sellerName") or ""
        productos.append(Producto(
            tienda=tienda, sku=str(r.get("skuId") or r.get("productId")),
            nombre=r.get("displayName", "") + (
                f" (vende {vendedor})" if vendedor and vendedor.lower() not in ("falabella", "tottus", "sodimac") else ""),
            url=r.get("url") or f"{base}/product/{r.get('productId')}/{_slug(r.get('displayName', ''))}",
            precio=min(vigentes),
            precio_lista=max([t for t in tachados if t and t > min(vigentes)], default=None),
            marca=r.get("brand", ""), imagen=(r.get("mediaUrls") or [""])[0],
        ))
    return productos


class Falabella(Adaptador):
    def buscar(self, termino: str) -> list[Producto]:
        ruta = self.tienda.get("ruta_busqueda", "/search?Ntt={q}")  # Tottus usa /buscar?Ntt={q}
        r = self.cliente.get(self.url + ruta.format(q=quote(termino)))
        return extraer(r.text, self.id, self.url) if r is not None else []
