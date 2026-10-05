"""Tiendas VTEX: API pública de catálogo (Price vs ListPrice por SKU)."""
from __future__ import annotations

from urllib.parse import quote

from ..modelos import Producto, Variante
from .base import Adaptador

TAMANO_PAGINA = 50
MAX_CATALOGO = 2500  # límite de la API de VTEX


class Vtex(Adaptador):
    def detectar(self) -> bool:
        datos = self.cliente.json(f"{self.url}/api/catalog_system/pub/products/search?_from=0&_to=0")
        return isinstance(datos, list)

    def _producto(self, p: dict) -> Producto | None:
        variantes = []
        imagen = ""
        for item in p.get("items", []):
            if not imagen and item.get("images"):
                imagen = item["images"][0].get("imageUrl", "")
            for vendedor in item.get("sellers", []):
                oferta = vendedor.get("commertialOffer") or {}
                precio = oferta.get("Price") or 0
                if precio <= 0:
                    continue
                disponible = oferta.get("IsAvailable", (oferta.get("AvailableQuantity") or 0) > 0)
                variantes.append(Variante(
                    nombre=item.get("name") or item.get("nameComplete") or "",
                    precio=float(precio),
                    precio_lista=float(oferta.get("ListPrice") or 0) or None,
                    disponible=bool(disponible),
                ))
                break  # primer vendedor = vendedor principal
        if not variantes:
            return None
        disponibles = [v for v in variantes if v.disponible] or variantes
        mejor = min(disponibles, key=lambda v: v.precio)
        link = p.get("link") or f"{self.url}/{p.get('linkText')}/p"
        if link.startswith("/"):
            link = self.url + link
        nombre = p.get("productName", "")
        if self.tienda.get("nombre_con_categoria") and p.get("categories"):
            # H&M: el nombre no dice si es de niña/niño; el departamento sí ("/NIÑOS/NIÑA 2-8A/...")
            ruta = max(p["categories"], key=len).strip("/").split("/")
            nombre += " · " + " ".join(x for x in ruta[:2] if "_" not in x)
        return Producto(
            tienda=self.id,
            sku=str(p.get("productId")),
            nombre=nombre,
            url=link,
            precio=mejor.precio,
            precio_lista=mejor.precio_lista,
            marca=p.get("brand", ""),
            imagen=imagen,
            disponible=any(v.disponible for v in variantes),
            variantes=variantes,
        )

    def buscar(self, termino: str) -> list[Producto]:
        url = (f"{self.url}/api/catalog_system/pub/products/search"
               f"?ft={quote(termino)}&_from=0&_to={TAMANO_PAGINA - 1}")
        datos = self.cliente.json(url)
        if not isinstance(datos, list):
            # Tiendas VTEX IO recientes: Intelligent Search
            url = (f"{self.url}/api/io/_v/api/intelligent-search/product_search/"
                   f"?query={quote(termino)}&count={TAMANO_PAGINA}")
            datos = (self.cliente.json(url) or {}).get("products", [])
        return [p for p in map(self._producto, datos or []) if p]

    def catalogo(self) -> list[Producto]:
        # secciones: rutas de categoría (p. ej. "551403/551406") para recorrer sólo esas partes de la tienda
        filtros = [f"&fq=C:/{s.strip('/')}/" for s in self.tienda.get("secciones") or []] or [""]
        productos = []
        for filtro in filtros:
            for desde in range(0, MAX_CATALOGO, TAMANO_PAGINA):
                url = (f"{self.url}/api/catalog_system/pub/products/search"
                       f"?_from={desde}&_to={desde + TAMANO_PAGINA - 1}{filtro}")
                lote = self.cliente.json(url)
                if not lote:
                    break
                productos += [p for p in map(self._producto, lote) if p]
        return productos
