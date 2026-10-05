"""Cuenta cuántas unidades (fotos) trae un pack a partir de su nombre.

Ejemplos: "100 unidades" -> 100, "Pack 2X20" -> 40, "10/PK" -> 10, "Twin Pack 20 Hojas 53x86mm" -> 20.
"""
from __future__ import annotations

import re

from .modelos import normalizar

# En orden de confianza: una cantidad explícita de fotos gana a "2x20" y éste a "10 pack".
PATRONES = [
    (r"(\d+)\s*(?:fotografias|fotos?|unidades|uni|un|hojas|exposiciones|exp|laminas)\b", lambda m: int(m[1])),
    (r"(\d+)\s*[x×]\s*(\d+)(?!\s*mm)", lambda m: int(m[1]) * int(m[2])),
    (r"(\d+)\s*(?:peliculas|films?)\b", lambda m: int(m[1])),
    (r"(\d+)\s*/?\s*(?:pk|pack)\b", lambda m: int(m[1])),
    (r"pack\s+de\s+(\d+)", lambda m: int(m[1])),
]


def contar(nombre: str) -> int | None:
    texto = normalizar(nombre)
    for patron, valor in PATRONES:
        m = re.search(patron, texto)
        if m:
            n = valor(m)
            if 1 <= n <= 1000:
                return n
    return None
