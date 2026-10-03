"""IKEA (ikea.com/cl): API pública de búsqueda que usa su propia página."""
from __future__ import annotations

from urllib.parse import quote

from ..modelos import Producto
from .base import Adaptador

API = "https://sik.search.blue.cdtapps.com/{pais}/{idioma}/search-result-page?q={q}&size=48&types=PRODUCT"


def _numero(precio) -> float | None:
    if not isinstance(precio, dict):
        return None
    if precio.get("numeral"):
        return float(precio["numeral"])
    entero = str(precio.get("wholeNumber") or "").replace(".", "")
    return float(entero) if entero.isdigit() else None


def extraer(datos: dict, tienda: str) -> list[Producto]:
    items = (((datos.get("searchResultPage") or {}).get("products") or {}).get("main") or {}).get("items") or []
    productos = []
    for it in items:
        p = it.get("product") or {}
        venta = p.get("salesPrice") or {}
        precio = _numero(venta)
        if not precio:
            continue
        anterior = _numero(venta.get("previous"))
        imagenes = p.get("allProductImage") or [{}]
        # el texto de la imagen describe la variante: "DJUNGELSKOG Peluche, orangután"
        nombre = imagenes[0].get("altText") or f"{p.get('name', '')} {p.get('typeName', '')}"
        productos.append(Producto(
            tienda=tienda, sku=str(p.get("itemNo") or p.get("id")), nombre=nombre, url=p.get("pipUrl", ""),
            precio=precio, precio_lista=anterior if anterior and anterior > precio else None,
            marca="IKEA", imagen=p.get("mainImageUrl", ""), disponible=bool(p.get("onlineSellable", True)),
        ))
    return productos


class Ikea(Adaptador):
    def buscar(self, termino: str) -> list[Producto]:
        pais, idioma = self.tienda.get("pais", "cl"), self.tienda.get("idioma", "es")
        datos = self.cliente.json(API.format(pais=pais, idioma=idioma, q=quote(termino)))
        return extraer(datos, self.id) if isinstance(datos, dict) else []
