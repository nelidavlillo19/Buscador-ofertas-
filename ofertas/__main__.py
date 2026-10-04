"""Uso:
    python -m ofertas rastrear          # revisa tiendas, guarda precios, alerta, respalda y arma el panel
    python -m ofertas probar <tienda>   # diagnostica una tienda (plataforma detectada y resultados)
    python -m ofertas panel             # sólo regenera el panel web
    python -m ofertas demo              # panel con datos simulados para ver cómo se ve
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from . import adapters, alertas, db, panel, respaldo
from .filtros import aplicar_filtro, clasificar
from .modelos import Producto
from .red import Cliente

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "data"
RUTA_DB = DATOS / "precios.sqlite"
SITIO = RAIZ / "sitio"

log = logging.getLogger("ofertas")


def cargar_config() -> dict:
    leer = lambda nombre: yaml.safe_load((RAIZ / "config" / nombre).read_text(encoding="utf-8"))  # noqa: E731
    return {"tiendas": leer("tiendas.yaml")["tiendas"], "productos": leer("productos.yaml")}


def hoy() -> str:
    return datetime.now(ZoneInfo("America/Santiago")).date().isoformat()


def recolectar(tienda: dict, categorias: dict, cliente: Cliente) -> list[Producto]:
    """Productos de interés de una tienda, ya clasificados por categoría."""
    adaptador = adapters.crear(tienda, cliente)
    if adaptador is None:
        return []
    permitidas = tienda.get("categorias") or list(categorias)
    encontrados: dict[str, Producto] = {}

    if tienda.get("catalogo_completo"):
        for p in adaptador.catalogo():
            cid = clasificar(p, categorias, permitidas)
            if cid:
                p.categoria = cid
                encontrados[p.id] = p

    for cid in permitidas:
        cat = categorias.get(cid)
        if not cat:
            log.warning("%s: categoría desconocida %r", tienda["id"], cid)
            continue
        for termino in cat.get("buscar", []):
            try:
                resultados = adaptador.buscar(termino)
            except Exception:  # noqa: BLE001 - una búsqueda rota no debe frenar el resto
                log.exception("%s: falló la búsqueda %r", tienda["id"], termino)
                continue
            for p in resultados:
                if p.id not in encontrados and aplicar_filtro(p, cat):
                    p.categoria = cid
                    encontrados[p.id] = p
    return list(encontrados.values())


def escribir_estado(fecha: str, resumen: dict, lista: list, aviso: str) -> None:
    """data/ESTADO.md: resumen legible de la última revisión (tiendas, ofertas y avisos)."""
    lineas = [f"# Última revisión: {fecha}", "", f"- Hora: {datetime.now(ZoneInfo('America/Santiago')):%H:%M} (Chile)",
              f"- Ofertas encontradas: {len({a.producto_id for a in lista})} "
              f"({len({a.producto_id for a in lista if a.nueva})} nuevas)",
              f"- Avisos: {aviso}", "", "| Tienda | Productos |", "|---|---|"]
    lineas += [f"| {n} | {c}{' ⚠️' if c == 0 else ''} |" for n, c in resumen.items()]
    (DATOS / "ESTADO.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")


def cmd_rastrear(args) -> int:
    config = cargar_config()
    categorias = config["productos"]["categorias"]
    fecha = args.fecha or hoy()
    con = db.conectar(RUTA_DB)
    cliente = Cliente(pausa=args.pausa)

    resumen = {}
    for tienda in config["tiendas"]:
        if not tienda.get("activa", True) or (args.tienda and tienda["id"] not in args.tienda):
            continue
        log.info("Revisando %s ...", tienda["nombre"])
        try:
            productos = recolectar(tienda, categorias, cliente)
        except Exception:  # noqa: BLE001
            log.exception("%s: error inesperado, se continúa con la siguiente tienda", tienda["id"])
            productos = []
        for p in productos:
            db.guardar(con, p, fecha)
        con.commit()
        resumen[tienda["nombre"]] = len(productos)
        log.info("%s: %d productos de interés", tienda["nombre"], len(productos))

    lista = alertas.detectar(con, fecha, config["productos"].get("umbral_descuento", 30),
                             config["productos"].get("dias_historial", 60), categorias,
                             {t["id"]: t for t in config["tiendas"]})
    con.commit()
    carpeta_alertas = DATOS / "alertas"
    carpeta_alertas.mkdir(parents=True, exist_ok=True)
    texto = alertas.resumen_markdown(lista, fecha, categorias)
    (carpeta_alertas / f"{fecha}.md").write_text(texto, encoding="utf-8")
    (carpeta_alertas / "ULTIMAS.md").write_text(texto, encoding="utf-8")

    if not args.sin_avisos:
        try:
            nombres = {t["nombre"]: t["id"] for t in config["tiendas"]}
            revisadas = {nombres[n]: (n, c) for n, c in resumen.items()}
            aviso = alertas.notificar(lista, fecha, categorias, os.environ.get("URL_PANEL", ""), revisadas)
        except Exception as e:  # noqa: BLE001 - un aviso fallido no debe impedir el respaldo
            log.exception("No se pudieron enviar los avisos (revisa GMAIL_USUARIO / GMAIL_CLAVE_APP)")
            aviso = f"ERROR al enviar: {type(e).__name__}: {str(e)[:200]}"
    else:
        aviso = "avisos desactivados en esta ejecución"
    escribir_estado(fecha, resumen, lista, aviso)
    respaldo.respaldar(con, DATOS / "respaldos", fecha)
    panel.exportar(con, fecha, config, SITIO)

    print("\nProductos por tienda:")
    for nombre, n in resumen.items():
        print(f"  {nombre:<15} {n:>5}{'   <-- revisar' if n == 0 else ''}")
    print(f"\nAlertas de {config['productos'].get('umbral_descuento', 30)}%+: {len(lista)} "
          f"({sum(a.nueva for a in lista)} nuevas). Detalle en data/alertas/{fecha}.md")
    return 0


def cmd_probar(args) -> int:
    config = cargar_config()
    tienda = next((t for t in config["tiendas"] if t["id"] == args.tienda), None)
    if not tienda:
        print(f"No existe la tienda {args.tienda!r}. Opciones: {[t['id'] for t in config['tiendas']]}")
        return 1
    cliente = Cliente(pausa=args.pausa)
    adaptador = adapters.crear(tienda, cliente)
    if adaptador is None:
        print(f"{tienda['url']} no responde (¿red bloqueada o sitio caído?)")
        return 2
    print(f"Plataforma usada: {type(adaptador).__name__}")
    termino = args.termino or next(iter(config["productos"]["categorias"][tienda["categorias"][0]]["buscar"]))
    resultados = adaptador.buscar(termino)
    print(f"Búsqueda {termino!r}: {len(resultados)} productos")
    for p in resultados[:15]:
        desc = f"  -{p.descuento_declarado:.0f}%" if p.descuento_declarado else ""
        print(f"  ${p.precio:>10,.0f}{desc}  {p.nombre[:70]}")
    return 0 if resultados else 2


def cmd_correo_prueba(args) -> int:
    """Envía las mejores ofertas vigentes (aunque no sean nuevas) para comprobar el correo."""
    config = cargar_config()
    categorias = config["productos"]["categorias"]
    con = db.conectar(RUTA_DB)
    fecha = con.execute("SELECT MAX(fecha) FROM alertas").fetchone()[0] or hoy()
    lista = [alertas.Alerta(f["producto_id"], f["tipo"], f["descuento"], f["precio"], f["referencia"],
                            f["nombre"], f["tienda"], f["url"], f["categoria"], nueva=False)
             for f in con.execute("""SELECT a.*, p.nombre, p.tienda, p.url, p.categoria FROM alertas a
                                     JOIN productos p ON p.id = a.producto_id WHERE a.fecha = ?""", (fecha,))]
    try:
        nombres = {t["id"]: t["nombre"] for t in config["tiendas"]}
        revisadas = {f["tienda"]: (nombres.get(f["tienda"], f["tienda"]), f["n"]) for f in con.execute(
            """SELECT p.tienda, COUNT(*) AS n FROM precios pr JOIN productos p ON p.id = pr.producto_id
               WHERE pr.fecha = ? GROUP BY p.tienda ORDER BY n DESC""", (fecha,))}
        resultado = alertas.notificar(lista, f"{fecha} (correo de prueba)", categorias,
                                      os.environ.get("URL_PANEL", ""), revisadas)
    except Exception as e:  # noqa: BLE001
        resultado = f"ERROR al enviar: {type(e).__name__}: {str(e)[:300]}"
    salida = RAIZ / "diagnostico" / "correo_resultado.txt"
    salida.parent.mkdir(exist_ok=True)
    salida.write_text(f"{datetime.now(ZoneInfo('America/Santiago')):%Y-%m-%d %H:%M} {resultado}\n", encoding="utf-8")
    print(resultado)
    return 0


def cmd_panel(args) -> int:
    config = cargar_config()
    con = db.conectar(RUTA_DB)
    fila = con.execute("SELECT MAX(fecha) FROM precios").fetchone()
    print(panel.exportar(con, fila[0] or hoy(), config, SITIO))
    return 0


def cmd_demo(args) -> int:
    from .demo import generar
    config = cargar_config()
    ruta = DATOS / "demo.sqlite"
    ruta.unlink(missing_ok=True)
    con = db.conectar(ruta)
    fecha = generar(con, config, dias=args.dias)
    categorias = config["productos"]["categorias"]
    for dia in sorted({f[0] for f in con.execute("SELECT DISTINCT fecha FROM precios")})[-args.dias:]:
        alertas.detectar(con, dia, config["productos"].get("umbral_descuento", 30),
                         config["productos"].get("dias_historial", 60), categorias,
                             {t["id"]: t for t in config["tiendas"]})
    con.commit()
    print(panel.exportar(con, fecha, config, RAIZ / "sitio-demo", demo=True))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="ofertas", description="Buscador de ofertas familiar")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--pausa", type=float, default=1.5, help="segundos entre peticiones a una tienda")
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("rastrear")
    p.add_argument("--fecha", help="fecha a registrar (AAAA-MM-DD), por defecto hoy en Chile")
    p.add_argument("--tienda", action="append", help="sólo estas tiendas (se puede repetir)")
    p.add_argument("--sin-avisos", action="store_true", help="no enviar Telegram/correo")
    p.set_defaults(func=cmd_rastrear)

    p = sub.add_parser("probar")
    p.add_argument("tienda")
    p.add_argument("termino", nargs="?")
    p.set_defaults(func=cmd_probar)

    sub.add_parser("panel").set_defaults(func=cmd_panel)
    sub.add_parser("correo-prueba").set_defaults(func=cmd_correo_prueba)

    p = sub.add_parser("demo")
    p.add_argument("--dias", type=int, default=90)
    p.set_defaults(func=cmd_demo)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
