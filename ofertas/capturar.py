"""Guarda páginas de tiendas (comprimidas) para estudiar cómo publican sus precios.

Lee URLs de diagnostico/capturar.txt y escribe diagnostico/html/<n>.html.gz
"""
from __future__ import annotations

import gzip
import sys
from pathlib import Path

from .red import Cliente

RAIZ = Path(__file__).resolve().parent.parent


def main() -> int:
    urls = [l.strip() for l in (RAIZ / "diagnostico" / "capturar.txt").read_text().splitlines()
            if l.strip() and not l.startswith("#")]
    carpeta = RAIZ / "diagnostico" / "html"
    carpeta.mkdir(parents=True, exist_ok=True)
    cliente = Cliente(pausa=1.0)
    indice = []
    for i, url in enumerate(urls):
        try:
            r = cliente.sesion.get(url, timeout=30)
        except Exception as e:  # noqa: BLE001 - un dominio inexistente no debe frenar el resto
            indice.append(f"{i:02d} ERROR {type(e).__name__} {url}")
            continue
        (carpeta / f"{i:02d}.html.gz").write_bytes(gzip.compress(r.content))
        indice.append(f"{i:02d} {r.status_code} {len(r.content)} {r.url[:90]} <- {url}")
    (carpeta / "indice.txt").write_text("\n".join(indice) + "\n")
    print("\n".join(indice))
    return 0


if __name__ == "__main__":
    sys.exit(main())
