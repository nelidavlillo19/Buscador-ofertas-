"""Salcobrand: su buscador usa Algolia con una clave pública que exige venir desde salcobrand.cl."""
from __future__ import annotations

from urllib.parse import quote

from ..modelos import Producto
from .base import Adaptador

APP = "GM3RP06HJG"
CLAVE = "0259fe250b3be4b1326eb85e47aa7d81"   # clave pública de búsqueda de la propia página
INDICE = "sb_variant_production"


def _num(valor) -> float | None:
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


def extraer(datos: dict, tienda: str, base: str) -> list[Producto]:
    productos = []
    for h in (datos or {}).get("hits") or []:
        normal = _num(h.get("normal_price"))
        oferta = _num(h.get("direct_discount"))   # el precio con tarjeta SBPay (direct_discount_sbpay) no se usa
        precio = oferta or normal
        if not precio:
            continue
        productos.append(Producto(
            tienda=tienda, sku=str(h.get("sku") or h.get("objectID")), nombre=h.get("name", ""),
            url=f"{base}/products/{h.get('slug')}", precio=precio,
            precio_lista=normal if normal and normal > precio else None,
            marca=h.get("brand") or "", imagen=h.get("catalog_image_url") or "",
            disponible=bool(h.get("has_stock", True)),
        ))
    return productos


class Salcobrand(Adaptador):
    def buscar(self, termino: str) -> list[Producto]:
        url = (f"https://{APP}-dsn.algolia.net/1/indexes/{INDICE}?query={quote(termino)}&hitsPerPage=40"
               f"&x-algolia-application-id={APP}&x-algolia-api-key={CLAVE}")
        r = self.cliente.get(url, headers={"Referer": "https://salcobrand.cl/", "Origin": "https://salcobrand.cl"})
        try:
            return extraer(r.json(), self.id, self.url) if r is not None else []
        except ValueError:
            return []
