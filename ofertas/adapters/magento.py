"""Tiendas Magento "headless" (p. ej. Casa Ideas): API GraphQL pública de productos."""
from __future__ import annotations

from urllib.parse import quote

from ..modelos import Producto
from .base import Adaptador

CONSULTA = (
    '{products(search:"%s",pageSize:%d){items{sku name url_key url_suffix stock_status '
    "small_image{url} price_range{minimum_price{regular_price{value} final_price{value}}}}}}"
)


class Magento(Adaptador):
    def __init__(self, tienda, cliente):
        super().__init__(tienda, cliente)
        self.api = tienda.get("api", f"{self.url}/graphql")
        self.ruta_producto = tienda.get("ruta_producto", "/{url_key}{url_suffix}")

    def buscar(self, termino: str) -> list[Producto]:
        consulta = CONSULTA % (termino.replace('"', ""), 48)
        datos = self.cliente.json(f"{self.api}?query={quote(consulta)}") or {}
        items = (((datos.get("data") or {}).get("products") or {}).get("items")) or []
        productos = []
        for it in items:
            precios = (it.get("price_range") or {}).get("minimum_price") or {}
            final = (precios.get("final_price") or {}).get("value")
            normal = (precios.get("regular_price") or {}).get("value")
            if not final:
                continue
            ruta = self.ruta_producto.format(url_key=it.get("url_key", ""), url_suffix=it.get("url_suffix") or "")
            productos.append(Producto(
                tienda=self.id, sku=str(it.get("sku")), nombre=it.get("name", ""), url=self.url + ruta,
                precio=float(final), precio_lista=float(normal) if normal and normal > final else None,
                imagen=(it.get("small_image") or {}).get("url", ""),
                disponible=it.get("stock_status", "IN_STOCK") == "IN_STOCK",
            ))
        return productos
