"""Uso:
    python -m revisor_sueldos analizar <planillas...> [--config archivo.yaml] [--salida carpeta]
        lee planillas CSV/XLSX (archivos o carpetas) en formato Transparencia Activa y genera
        informe.html, revision_sueldos.xlsx y un resumen en pantalla
    python -m revisor_sueldos ejemplo [--salida carpeta]
        genera planillas ficticias y las analiza, para ver cómo funciona
"""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from . import cargar, costeo, ejemplo, proyeccion, reporte, trayectorias

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "config" / "revisor_sueldos.yaml"


def analizar(rutas: list[Path], config: dict, fuente: str) -> dict:
    registros = cargar.cargar(rutas, config)
    tray = trayectorias.analizar(registros, config)
    return {
        "fuente": fuente,
        "registros": len(registros),
        "periodo": costeo.por_periodo(registros, config),
        "tipo": costeo.por_tipo(registros, config),
        "anual": costeo.anual(registros, config),
        "hallazgos": costeo.hallazgos(registros, config),
        "trayectorias": tray,
        "proyeccion": proyeccion.proyectar(trayectorias.consolidar(registros), tray["resumen"], config),
    }


def escribir(resultado: dict, salida: Path) -> None:
    salida.mkdir(parents=True, exist_ok=True)
    reporte.excel(resultado, salida / "revision_sueldos.xlsx")
    reporte.informe_html(resultado, salida / "informe.html")
    print(f"{resultado['registros']} filas leídas.")
    print("\nTasa anual de ascenso (histórica):")
    for g, r in sorted(resultado["trayectorias"]["resumen"].items()):
        print(f"  {reporte.NOMBRES_GRUPO.get(g, g):16} {reporte.pct(r['tasa_ascenso_anual']):>7}")
    print("\nProyección (TOTAL):")
    for f in resultado["proyeccion"]["filas"]:
        if f["grupo"] == "TOTAL":
            print(f"  {f['anio']}  sin reforma {reporte.millones(f['costo_base']):>16}  "
                  f"con reforma {reporte.millones(f['costo_reforma_total']):>16}  ({reporte.pct(f['diferencia_pct'])})")
    print(f"\nHallazgos de revisión: {len(resultado['hallazgos'])}")
    print(f"Informe: {salida / 'informe.html'}\nExcel:   {salida / 'revision_sueldos.xlsx'}")


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m revisor_sueldos", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="comando", required=True)
    a = sub.add_parser("analizar")
    a.add_argument("planillas", nargs="+", type=Path)
    a.add_argument("--config", type=Path, default=CONFIG)
    a.add_argument("--salida", type=Path, default=RAIZ / "informe_sueldos")
    e = sub.add_parser("ejemplo")
    e.add_argument("--config", type=Path, default=CONFIG)
    e.add_argument("--salida", type=Path, default=RAIZ / "informe_sueldos_ejemplo")
    args = ap.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if args.comando == "ejemplo":
        rutas = ejemplo.generar(args.salida / "planillas_ficticias")
        escribir(analizar(rutas, config, "planillas FICTICIAS generadas para demostración"), args.salida)
    else:
        nombres = ", ".join(p.name for p in args.planillas)
        escribir(analizar(args.planillas, config, nombres), args.salida)


if __name__ == "__main__":
    main()
