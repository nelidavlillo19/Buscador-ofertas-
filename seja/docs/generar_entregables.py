"""Genera los documentos Word del modelo SEJA desde las fuentes en Markdown y la configuración del modelo.

Uso: python -m seja.docs.generar_entregables CARPETA_DE_SALIDA

- Modelo_de_Calificacion_Academica_SEJA.docx
- Requerimientos_UCampus_Evaluacion_SEJA.docx
- Resultado_Calificacion_Formato_Comision_SEJA.docx (formato de informe para la Comisión Central)

Los valores (umbrales, tope, ponderaciones, rangos, catálogo) se leen de seja/config/modelo.yaml, así que los
documentos siempre coinciden con lo que calcula el sistema. Las ecuaciones se escriben en LaTeX y pandoc las
convierte en ecuaciones nativas de Word.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from seja.calificacion import cargar_modelo, horas_jornada, peso_instrumentos

FUENTES = Path(__file__).parent / "fuentes"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]
DOCUMENTOS = {
    "modelo_calificacion.md": "Modelo_de_Calificacion_Academica_SEJA.docx",
    "requerimientos_ucampus.md": "Requerimientos_UCampus_Evaluacion_SEJA.docx",
    "informe_comision.md": "Resultado_Calificacion_Formato_Comision_SEJA.docx",
}
AZUL = "1F3864"


def tex(x: float) -> str:
    return f"{x:.2f}".replace(".", "{,}")


def tabla(encabezados: list[str], filas: list[list[str]], anchos: list[int]) -> str:
    """Tabla Markdown; `anchos` fija el ancho relativo de cada columna en Word."""
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "|".join("-" * a for a in anchos) + "|"]
    lineas += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(lineas)


def valores(modelo: dict) -> dict[str, str]:
    from datetime import date
    hoy = date.today()
    p = peso_instrumentos(modelo)
    p_estado = "por definir; valor provisional" if not modelo["componentes_fijos"].get("definido") else "definido"
    umbrales = modelo["umbrales"]

    catalogo = []
    for ambito in modelo["ambitos"].values():
        filas = []
        for sub in ambito["subcategorias"].values():
            d = sub if isinstance(sub, dict) else {"nombre": sub}
            filas.append([d["nombre"], d.get("instrumento", "Evidencia del compromiso"),
                          d.get("periodicidad", "Según el compromiso")])
        catalogo.append(f"**{ambito['nombre']}**\n\n" +
                        tabla(["Subcategoría (rol o función)", "Se evalúa con", "Periodicidad"], filas, [30, 50, 20]))

    rangos = [[jer.capitalize(), f"{r[0]}% a {r[1]}%"] for jer, r in modelo["carga_docente"].items()]

    letras = list(umbrales)
    filas_u = []
    for i, letra in enumerate(letras):
        minimo = umbrales[letra]
        if i == 0:
            cond = f"$F \\geq {minimo}\\%$"
        elif letra == letras[-1]:
            cond = f"$F < {umbrales[letras[i - 1]]}\\%$"
        else:
            cond = f"${minimo}\\% \\leq F < {umbrales[letras[i - 1]]}\\%$"
        filas_u.append([f"**{letra}**", cond, modelo["descripcion_letras"][letra]])

    escala = []
    pares = modelo["escala_numerica"]
    for i, (minimo, nota) in enumerate(pares):
        if i == 0:
            rango = f"{minimo}% o más"
        elif minimo == 0:
            rango = f"menos de {pares[i - 1][0]}%"
        else:
            rango = f"{minimo}% a {pares[i - 1][0] - 1}%"
        escala.append([rango, str(nota)])

    jornadas = "; ".join(f"jornada {k}, {c:g} h de contrato y {j:g} h a justificar"
                         for k, (c, j) in ((k, horas_jornada(modelo, k)) for k in modelo["horas_jornada"]))
    parametros = tabla(["Parámetro", "Valor"], [
        ["Autoevaluación y evaluación de estudiantes ($p$)",
         f"El mismo % para ambas ({p_estado} {p:.0%} cada una)"],
        ["Ámbitos del compromiso ($\\alpha$)", f"$1 - 2p$ ({1 - 2 * p:.0%}); $1 - p$ ({1 - p:.0%}) si está eximido/a de docencia"],
        ["Perfil", "Único"],
        ["Ponderación de los ámbitos", "Horas semanales comprometidas en cada ámbito"],
        ["Tope por tarea con excedente validado", f"{modelo['tope_excedente']}%"],
        ["Etapa evidenciada anterior a la comprometida", f"{modelo['etapas']['etapa_anterior']}%"],
        ["Estados de evidencia", "Cumplido 100; parcial 50; no cumplido 0; sin evidencia 0"],
        ["Evidencia válida", "Registrada en el CV Académico de UCampus; la carga académica no acredita cumplimiento"],
        ["Cumplimiento del ámbito", "Promedio simple de las tareas comprometidas en el ámbito"],
        ["Umbrales", "; ".join(f"{l} desde {umbrales[l]}%" for l in letras[:-1]) +
         f"; {letras[-1]} bajo {umbrales[letras[-2]]}%"],
        ["Suspensión (art. 37)", f"Ausencia justificada de más de {modelo['situaciones_especiales']['meses_suspension']} "
                                 "meses continuos"],
        ["Comisión de estudios", "Se evalúan los compromisos asociados; sin ellos, regla general de suspensión"],
        ["Jornadas", jornadas],
    ], [45, 55])

    return {
        "FECHA": f"{MESES[hoy.month - 1].capitalize()} de {hoy.year}",
        "CATALOGO": "\n\n".join(catalogo),
        "RANGOS": tabla(["Jerarquía", "Docencia esperada (% del compromiso, provisional)"], rangos, [40, 60]),
        "UMBRALES": tabla(["Letra", "Cumplimiento final", "Desempeño"], filas_u, [12, 33, 55]),
        "ESCALA": tabla(["Cumplimiento", "Escala numérica"], escala, [60, 40]),
        "PARAMETROS": parametros,
        "TOPE": str(modelo["tope_excedente"]),
        "ETAPA_ANTERIOR": str(modelo["etapas"]["etapa_anterior"]),
        "MESES": str(modelo["situaciones_especiales"]["meses_suspension"]),
        "INFORMAR_A": modelo["situaciones_especiales"]["informar_a"][:1].upper() + modelo["situaciones_especiales"]["informar_a"][1:],
        "JORNADAS": jornadas,
        "P": tex(p),
    }


def referencia(destino: Path) -> Path:
    """Plantilla de estilos de Word: Calibri en el texto, Cambria en títulos, tablas con bordes."""
    base = destino / "base.docx"
    with open(base, "wb") as f:
        f.write(subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"],
                               check=True, capture_output=True).stdout)
    with zipfile.ZipFile(base) as z:
        partes = {n: z.read(n) for n in z.namelist()}
    s = partes["word/styles.xml"].decode("utf-8")
    s = re.sub(r'w:asciiTheme="majorHAnsi" w:eastAsiaTheme="majorEastAsia" w:hAnsiTheme="majorHAnsi" '
               r'w:cstheme="majorBidi"', 'w:ascii="Cambria" w:hAnsi="Cambria" w:cs="Cambria" w:eastAsia="Cambria"', s)
    s = re.sub(r'<w:color w:val="[0-9A-F]{6}" />', f'<w:color w:val="{AZUL}" />', s)
    s = s.replace("<w:rPrDefault>", "<w:rPrDefault>", 1)
    s = re.sub(r"(<w:rPrDefault>\s*<w:rPr>)",
               r'\1<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri" w:eastAsia="Calibri" />'
               r'<w:sz w:val="22" /><w:szCs w:val="22" />', s, count=1)
    bordes = ('<w:tblBorders>' + "".join(f'<w:{b} w:val="single" w:sz="4" w:space="0" w:color="A6A6A6" />'
                                         for b in ["top", "left", "bottom", "right", "insideH", "insideV"])
              + '</w:tblBorders>')
    s = re.sub(r'(<w:style w:type="table" w:default="1" w:styleId="Table">.*?<w:tblPr>)',
               r'\1' + bordes, s, count=1, flags=re.S)
    s = re.sub(r'(<w:tblStylePr w:type="firstRow">.*?)(</w:tblStylePr>)',
               r'\1<w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="DCE3EE" /></w:tcPr>\2', s, count=1, flags=re.S)
    partes["word/styles.xml"] = s.encode("utf-8")
    ref = destino / "referencia.docx"
    with zipfile.ZipFile(ref, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in partes.items():
            z.writestr(n, data)
    return ref


def generar(salida: Path) -> list[Path]:
    if not shutil.which("pandoc"):
        raise SystemExit("Se necesita pandoc (https://pandoc.org)")
    salida.mkdir(parents=True, exist_ok=True)
    reemplazos = valores(cargar_modelo())
    hechos = []
    with tempfile.TemporaryDirectory() as tmp:
        ref = referencia(Path(tmp))
        for fuente, nombre in DOCUMENTOS.items():
            texto = (FUENTES / fuente).read_text(encoding="utf-8")
            for clave, valor in reemplazos.items():
                texto = texto.replace("{{" + clave + "}}", valor)
            faltan = re.findall(r"\{\{[A-Z_]+\}\}", texto)
            if faltan:
                raise SystemExit(f"{fuente}: marcadores sin valor {faltan}")
            md = Path(tmp) / fuente
            md.write_text(texto, encoding="utf-8")
            destino = salida / nombre
            subprocess.run(["pandoc", str(md), "-f", "markdown", "-o", str(destino), "--reference-doc", str(ref)], check=True)
            hechos.append(destino)
    return hechos


if __name__ == "__main__":
    for ruta in generar(Path(sys.argv[1] if len(sys.argv) > 1 else ".")):
        print(f"Guardado en {ruta}")
