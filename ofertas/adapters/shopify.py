"""Tiendas Shopify: /products.json expone precio y precio de comparación por variante."""
from __future__ import annotations

from urllib.parse import quote

from ..modelos import Producto, Variante
from .base import Adaptador

MAX_PAGINAS = 40


def _num(valor) -> float | None:
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


class Shopify(Adaptador):
    def detectar(self) -> bool:
        datos = self.cliente.json(f"{self.url}/products.json?limit=1")
        return isinstance(datos, dict) and "products" in datos

    def _producto(self, p: dict, centavos: bool = False) -> Producto | None:
        factor = 100 if centavos else 1
        variantes = []
        for v in p.get("variants", []):
            precio = _num(v.get("price"))
            if precio is None:
                continue
            lista = _num(v.get("compare_at_price"))
            variantes.append(Variante(
                nombre=v.get("title") or "",
                precio=precio / factor,
                precio_lista=lista / factor if lista else None,
                disponible=bool(v.get("available", True)),
            ))
        if not variantes:
            return None
        disponibles = [v for v in variantes if v.disponible] or variantes
        mejor = min(disponibles, key=lambda v: v.precio)
        imagenes = p.get("images") or []
        imagen = imagenes[0] if imagenes else ""
        if isinstance(imagen, dict):
            imagen = imagen.get("src", "")
        if imagen.startswith("//"):
            imagen = "https:" + imagen
        return Producto(
            tienda=self.id,
            sku=str(p.get("id") or p.get("handle")),
            nombre=p.get("title", ""),
            url=f"{self.url}/products/{p.get('handle')}",
            precio=mejor.precio,
            precio_lista=mejor.precio_lista,
            marca=p.get("vendor", ""),
            imagen=imagen,
            disponible=any(v.disponible for v in variantes),
            variantes=variantes,
        )

    def catalogo(self) -> list[Producto]:
        productos = []
        for pagina in range(1, MAX_PAGINAS + 1):
            datos = self.cliente.json(f"{self.url}/products.json?limit=250&page={pagina}")
            lote = (datos or {}).get("products") or []
            if not lote:
                break
            productos += [p for p in map(self._producto, lote) if p]
        return productos

    def buscar(self, termino: str) -> list[Producto]:
        url = (f"{self.url}/search/suggest.json?q={quote(termino)}"
               "&resources[type]=product&resources[limit]=10")
        datos = self.cliente.json(url) or {}
        encontrados = datos.get("resources", {}).get("results", {}).get("products", [])
        productos = []
        for item in encontrados:
            detalle = self.cliente.json(f"{self.url}/products/{item.get('handle')}.js")
            if detalle:
                # /products/<handle>.js entrega precios en centavos
                p = self._producto(detalle, centavos=True)
                if p:
                    productos.append(p)
        return productos
