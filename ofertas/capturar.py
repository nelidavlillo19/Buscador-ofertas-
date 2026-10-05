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
            if url.startswith("POST "):  # "POST <url>": p. ej. abrir sesión de invitado; la cookie queda guardada
                url = url[5:].strip()
                r = cliente.sesion.post(url, timeout=30, json={})
            else:
                # "<url> | Cabecera=valor": cabeceras extra (p. ej. Referer)
                url, _, extra = url.partition(" | ")
                cabeceras = dict(c.split("=", 1) for c in extra.split(";") if "=" in c)
                r = cliente.sesion.get(url.strip(), timeout=30, headers=cabeceras)
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
