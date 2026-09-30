"""Diagnóstico de tiendas: qué responde cada sitio y qué plataforma parece usar.

Uso: python -m ofertas.diagnostico [tienda ...]  -> escribe diagnostico/resultado.txt
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

from .__main__ import RAIZ, cargar_config
from .adapters.jsonld import PATRON_LDJSON
from .red import Cliente

PISTAS = {
    "vtex": r"vtex", "shopify": r"cdn\.shopify|Shopify\.shop", "next.js": r"__NEXT_DATA__",
    "magento": r"Magento|mage/", "salesforce": r"demandware|dwcdn|/on/demandware", "woocommerce": r"woocommerce",
    "jumpseller": r"jumpseller", "bigcommerce": r"bigcommerce", "cloudflare-reto": r"cf-chl|challenge-platform",
}
RUTAS = [
    "/products.json?limit=1",
    "/api/catalog_system/pub/products/search?_from=0&_to=0",
    "/api/catalog_system/pub/products/search?ft={q}&_from=0&_to=2",
    "/api/io/_v/api/intelligent-search/product_search/?query={q}&count=2",
    "/search?q={q}", "/busqueda?ft={q}", "/{q}?_q={q}&map=ft", "/buscar?q={q}", "/search?Ntt={q}",
]


def revisar(cliente: Cliente, tienda: dict, termino: str) -> list[str]:
    out = [f"=== {tienda['id']} ({tienda['url']}) término={termino!r}"]
    base = tienda["url"].rstrip("/")
    for ruta in ["/"] + RUTAS:
        url = base + ruta.format(q=quote(termino))
        try:
            r = cliente.sesion.get(url, timeout=25, allow_redirects=True)
        except Exception as e:  # noqa: BLE001
            out.append(f"  {ruta:<70} ERROR {type(e).__name__}: {str(e)[:120]}")
            continue
        texto = r.text or ""
        pistas = [k for k, pat in PISTAS.items() if re.search(pat, texto[:400000], re.I)]
        ld = sum(bloque.count('"Product"') for bloque in PATRON_LDJSON.findall(texto))
        extra = ""
        if "json" in r.headers.get("content-type", ""):
            try:
                d = r.json()
                extra = f" json={type(d).__name__}"
                extra += f" len={len(d)}" if isinstance(d, (list, dict)) else ""
                if isinstance(d, dict):
                    extra += f" claves={list(d)[:6]}"
            except ValueError:
                pass
        out.append(f"  {ruta:<70} {r.status_code} {len(texto):>8}b final={r.url[:80]} "
                   f"ld+json_products={ld} pistas={pistas}{extra}")
        if ruta == "/":
            for patron in (r'https?://[^"\']*api[^"\']{0,80}', r'"(?:apiKey|x-api-key|api_key)"\s*:\s*"[^"]{0,6}'):
                hallados = sorted(set(re.findall(patron, texto)))[:5]
                if hallados:
                    out.append(f"      referencias: {hallados}")
    return out


def main(argv: list[str]) -> int:
    config = cargar_config()
    cats = config["productos"]["categorias"]
    cliente = Cliente(pausa=1.0)
    lineas = []
    for t in config["tiendas"]:
        if argv and t["id"] not in argv:
            continue
        termino = cats[(t.get("categorias") or list(cats))[0]]["buscar"][0]
        lineas += revisar(cliente, t, termino)
    salida = RAIZ / "diagnostico" / "resultado.txt"
    salida.parent.mkdir(exist_ok=True)
    salida.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
