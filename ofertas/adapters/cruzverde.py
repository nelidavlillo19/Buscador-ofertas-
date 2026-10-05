"""Cruz Verde: API de búsqueda pública; requiere abrir antes una sesión de invitado."""
from __future__ import annotations

import re
import unicodedata
from urllib.parse import quote

from ..modelos import Producto
from .base import Adaptador

API = "https://api.cruzverde.cl"


def _slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", texto).strip("-")


def extraer(datos: dict, tienda: str, base: str) -> list[Producto]:
    productos = []
    for h in (datos or {}).get("hits") or []:
        precios = h.get("prices") or {}
        venta = precios.get("price-sale-cl")
        normal = precios.get("price-list-cl")
        precio = float(venta or normal or 0)
        if not precio:
            continue
        nombre = h.get("productName", "")
        pid = str(h.get("productId"))
        imagen = (h.get("image") or {}).get("link", "")
        productos.append(Producto(
            tienda=tienda, sku=pid, nombre=nombre, url=f"{base}/{_slug(nombre)}/{pid}.html",
            precio=precio, precio_lista=float(normal) if normal and venta and normal > venta else None,
            marca=(h.get("brand") or "").title(), imagen=imagen,
            disponible=bool(h.get("stock")) or bool(h.get("homeDelivery")),
        ))
    return productos


class CruzVerde(Adaptador):
    def __init__(self, tienda, cliente):
        super().__init__(tienda, cliente)
        self._sesion_abierta = False

    def buscar(self, termino: str) -> list[Producto]:
        if not self._sesion_abierta:
            try:
                self.cliente.sesion.post(f"{API}/customer-service/login", json={}, timeout=25)
            except Exception:  # noqa: BLE001 - si falla, la búsqueda devolverá vacío
                return []
            self._sesion_abierta = True
        datos = self.cliente.json(f"{API}/product-service/products/search?limit=40&offset=0&sort=&q={quote(termino)}")
        return extraer(datos, self.id, self.url) if isinstance(datos, dict) else []
