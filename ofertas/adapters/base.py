from __future__ import annotations

from ..modelos import Producto
from ..red import Cliente


class Adaptador:
    def __init__(self, tienda: dict, cliente: Cliente):
        self.tienda = tienda
        self.id = tienda["id"]
        self.url = tienda["url"].rstrip("/")
        self.cliente = cliente

    def detectar(self) -> bool:
        return False

    def buscar(self, termino: str) -> list[Producto]:
        raise NotImplementedError

    def catalogo(self) -> list[Producto]:
        """Catálogo completo; por defecto no soportado."""
        return []
