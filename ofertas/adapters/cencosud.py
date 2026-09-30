"""Santa Isabel (Cencosud): la página /busqueda trae los productos en window.__renderData
con el mismo formato de VTEX (Price / ListPrice)."""
from __future__ import annotations

import json
import re
from urllib.parse import quote

from ..modelos import Producto
from .vtex import Vtex

RENDER_DATA = re.compile(r'window\.__renderData\s*=\s*("(?:[^"\\]|\\.)*")')


def productos_render(pagina: str) -> list[dict]:
    m = RENDER_DATA.search(pagina)
    if not m:
        return []
    try:
        datos = json.loads(json.loads(m.group(1)))
        return datos["plp"]["plp_products"]["products"]
    except (ValueError, KeyError, TypeError):
        return []


class Cencosud(Vtex):
    def detectar(self) -> bool:
        return False

    def buscar(self, termino: str) -> list[Producto]:
        r = self.cliente.get(f"{self.url}/busqueda?ft={quote(termino)}")
        if r is None:
            return []
        productos = []
        for p in productos_render(r.text):
            p.setdefault("link", f"{self.url}/{p.get('linkText')}/p")
            producto = self._producto(p)
            if producto:
                productos.append(producto)
        return productos

    def catalogo(self) -> list[Producto]:
        return []
