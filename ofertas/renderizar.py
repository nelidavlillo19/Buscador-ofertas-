"""Abre páginas con un navegador real (Chromium) para ver si una tienda bloquea a los programas.

Lee URLs de diagnostico/renderizar.txt y guarda diagnostico/html/r<n>.html.gz + indice_navegador.txt
"""
from __future__ import annotations

import gzip
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def main() -> int:
    from playwright.sync_api import sync_playwright
    urls = [l.strip() for l in (RAIZ / "diagnostico" / "renderizar.txt").read_text().splitlines()
            if l.strip() and not l.startswith("#")]
    carpeta = RAIZ / "diagnostico" / "html"
    carpeta.mkdir(parents=True, exist_ok=True)
    indice = []
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pag = nav.new_page(locale="es-CL", user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"))
        for i, url in enumerate(urls):
            try:
                resp = pag.goto(url, wait_until="domcontentloaded", timeout=60000)
                pag.wait_for_timeout(8000)
                html = pag.content()
                (carpeta / f"r{i:02d}.html.gz").write_bytes(gzip.compress(html.encode()))
                indice.append(f"r{i:02d} {resp.status if resp else '?'} {len(html)} {pag.url[:90]} titulo={pag.title()[:60]!r}")
            except Exception as e:  # noqa: BLE001
                indice.append(f"r{i:02d} ERROR {type(e).__name__}: {str(e)[:100]} {url}")
        nav.close()
    (carpeta / "indice_navegador.txt").write_text("\n".join(indice) + "\n")
    print("\n".join(indice))
    return 0


if __name__ == "__main__":
    sys.exit(main())
