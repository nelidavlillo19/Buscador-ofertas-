"""Decide si un producto pertenece a una categoría de interés."""
from __future__ import annotations

import re

from .modelos import Producto, normalizar


def _contiene(texto: str, palabras: list[str]) -> bool:
    return any(normalizar(p) in texto for p in palabras)


def _talla_coincide(nombre_variante: str, tallas: list[str]) -> bool:
    texto = normalizar(nombre_variante)
    for talla in tallas:
        t = re.escape(normalizar(talla))
        # "2" no debe coincidir con "12" ni con "24M"; "6" tampoco con "6-9M" o "3-6M" (meses)
        for m in re.finditer(rf"(?<![0-9a-z]){t}(?![0-9])", texto):
            if not re.match(r"\s*(-\s*\d+)?\s*m(?![a-z]*a)", texto[m.end():]):
                return True
    return False


def aplicar_filtro(producto: Producto, categoria: dict) -> Producto | None:
    """Devuelve el producto (posiblemente con precio ajustado a la talla) o None."""
    nombre = normalizar(f"{producto.nombre} {producto.marca}")
    if categoria.get("incluir") and not _contiene(nombre, categoria["incluir"]):
        return None
    if categoria.get("incluir_tambien") and not _contiene(nombre, categoria["incluir_tambien"]):
        return None
    if categoria.get("excluir") and _contiene(nombre, categoria["excluir"]):
        return None

    tallas = categoria.get("tallas")
    if tallas and producto.variantes:
        validas = [v for v in producto.variantes if v.disponible and _talla_coincide(v.nombre, tallas)]
        if not validas:
            return None
        mejor = min(validas, key=lambda v: v.precio)
        producto.precio = mejor.precio
        producto.precio_lista = mejor.precio_lista
        producto.disponible = True
    return producto


def clasificar(producto: Producto, categorias: dict[str, dict], permitidas: list[str] | None) -> str | None:
    """Primera categoría (en orden de configuración) que acepta el producto."""
    for cid, cat in categorias.items():
        if permitidas and cid not in permitidas:
            continue
        if aplicar_filtro(producto, cat):
            return cid
    return None
