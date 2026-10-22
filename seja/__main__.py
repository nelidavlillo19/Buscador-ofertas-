"""Uso:
  python -m seja ARCHIVO.yaml [ARCHIVO2.yaml ...] [--json]     calificación (informe en texto o JSON)
  python -m seja reporte ARCHIVO.yaml [-o salida.md|.docx]      reporte del compromiso para la jefatura
  python -m seja cierre ARCHIVO.yaml [-o salida.md|.docx]       informe de cierre con la calificación
"""

import json
import sys
from pathlib import Path

import yaml

from seja.calificacion import ErrorCompromiso, calificar, cargar_modelo, informe
from seja.reportes import guardar, informe_cierre, reporte_compromiso


def leer(archivo: str) -> dict:
    return yaml.safe_load(Path(archivo).read_text(encoding="utf-8"))


def documento(argv: list[str], generar) -> int:
    salida = None
    if "-o" in argv:
        i = argv.index("-o")
        salida = argv[i + 1] if i + 1 < len(argv) else None
        argv = argv[:i] + argv[i + 2:]
    if len(argv) != 1 or ("-o" in sys.argv and not salida):
        print(__doc__)
        return 2
    try:
        texto = generar(leer(argv[0]))
        if salida:
            print(f"Guardado en {guardar(texto, salida)}")
        else:
            print(texto)
    except ErrorCompromiso as e:
        print(f"{argv[0]}: {e}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str]) -> int:
    if argv and argv[0] == "reporte":
        return documento(argv[1:], reporte_compromiso)
    if argv and argv[0] == "cierre":
        return documento(argv[1:], informe_cierre)
    archivos = [a for a in argv if not a.startswith("--")]
    if not archivos:
        print(__doc__)
        return 2
    modelo = cargar_modelo()
    salida_json, codigo = "--json" in argv, 0
    for archivo in archivos:
        try:
            resultado = calificar(leer(archivo), modelo)
        except ErrorCompromiso as e:
            print(f"{archivo}: {e}", file=sys.stderr)
            codigo = 1
            continue
        print(json.dumps(resultado.como_dict(), ensure_ascii=False, indent=2) if salida_json
              else informe(resultado) + "\n")
    return codigo


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
