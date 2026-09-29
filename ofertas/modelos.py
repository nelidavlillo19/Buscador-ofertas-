from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar nombres de productos."""
    texto = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in texto if not unicodedata.combining(c)).lower().strip()


@dataclass
class Variante:
    nombre: str
    precio: float
    precio_lista: float | None = None
    disponible: bool = True


@dataclass
class Producto:
    tienda: str
    sku: str
    nombre: str
    url: str
    precio: float
    precio_lista: float | None = None
    marca: str = ""
    imagen: str = ""
    disponible: bool = True
    variantes: list[Variante] = field(default_factory=list)
    categoria: str = ""

    @property
    def id(self) -> str:
        return f"{self.tienda}:{self.sku}"

    @property
    def descuento_declarado(self) -> float:
        """% de descuento que muestra la tienda (precio normal vs precio oferta)."""
        if not self.precio_lista or self.precio_lista <= self.precio or self.precio <= 0:
            return 0.0
        return round(100 * (1 - self.precio / self.precio_lista), 1)
