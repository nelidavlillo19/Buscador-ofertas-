"""Uso: python -m seja ARCHIVO.yaml [ARCHIVO2.yaml ...] [--json]"""

import json
import sys
from pathlib import Path

import yaml

from seja.calificacion import ErrorCompromiso, calificar, cargar_modelo, informe


def main(argv: list[str]) -> int:
    archivos = [a for a in argv if not a.startswith("--")]
    if not archivos:
        print(__doc__)
        return 2
    modelo = cargar_modelo()
    salida_json, codigo = "--json" in argv, 0
    for archivo in archivos:
        try:
            resultado = calificar(yaml.safe_load(Path(archivo).read_text(encoding="utf-8")), modelo)
        except ErrorCompromiso as e:
            print(f"{archivo}: {e}", file=sys.stderr)
            codigo = 1
            continue
        print(json.dumps(resultado.como_dict(), ensure_ascii=False, indent=2) if salida_json
              else informe(resultado) + "\n")
    return codigo


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
