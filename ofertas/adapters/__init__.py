"""Adaptadores por plataforma de e-commerce."""
from __future__ import annotations

import logging

from ..red import Cliente
from .base import Adaptador
from .cencosud import Cencosud
from .cruzverde import CruzVerde
from .falabella import Falabella
from .ikea import Ikea
from .jsonld import JsonLd
from .magento import Magento
from .sfcc import Ahumada, Sfcc
from .salcobrand import Salcobrand
from .shopify import Shopify
from .vtex import Vtex
from .walmart import Walmart

log = logging.getLogger(__name__)

PLATAFORMAS: dict[str, type[Adaptador]] = {
    "shopify": Shopify, "vtex": Vtex, "jsonld": JsonLd,
    "sfcc": Sfcc, "falabella": Falabella, "cencosud": Cencosud, "magento": Magento, "ikea": Ikea, "walmart": Walmart, "ahumada": Ahumada, "cruzverde": CruzVerde, "salcobrand": Salcobrand,
}


def crear(tienda: dict, cliente: Cliente) -> Adaptador | None:
    """Adaptador para la tienda, o None si el sitio no responde."""
    if cliente.get(tienda["url"]) is None:
        log.warning("%s: el sitio %s no responde, se omite hoy", tienda["id"], tienda["url"])
        return None
    plataforma = tienda.get("plataforma", "auto")
    if plataforma != "auto":
        return PLATAFORMAS[plataforma](tienda, cliente)
    for clase in (Shopify, Vtex):
        adaptador = clase(tienda, cliente)
        if adaptador.detectar():
            log.info("%s: detectada plataforma %s", tienda["id"], clase.__name__)
            return adaptador
    log.info("%s: se usará lectura genérica schema.org", tienda["id"])
    return JsonLd(tienda, cliente)
