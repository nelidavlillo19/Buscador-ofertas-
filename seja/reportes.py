"""Documentos del ciclo del Compromiso de Desempeño, en Markdown (y Word con pandoc).

- ``reporte_compromiso``: reporte a la jefatura al recibir el compromiso. Muestra lo declarado, la
  distribución de horas por ámbito y las alertas.
- ``informe_cierre``: informe al cerrar el período. Incluye el cumplimiento por actividad, la
  calificación SEJA, lo que destaca, las funciones de la jerarquía, y las oportunidades y fortalezas.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path

import yaml

from seja.calificacion import (ErrorCompromiso, Resultado, calificar, cargar_modelo, nombre_subcategoria,
                               ponderacion_compromiso, texto_destacado)

FUNCIONES = Path(__file__).parent / "config" / "funciones.yaml"

ENCABEZADO = ("**Sistema de Evaluación y Jerarquización Académica SEJA**  \n"
              "Oficina de Evaluación de Desempeño Académico · Vicerrectoría Académica")

ORIENTACIONES = """El objetivo general del Sistema de Evaluación y Jerarquización Académica SEJA es contribuir al \
desarrollo profesional de académicos y académicas mediante la evaluación y jerarquización, en función de los \
estándares institucionales, la política pública vigente y la mejora continua organizacional. En este contexto, \
reconociendo la diversidad de desempeños y la contribución de los/as académicos/as adscritos al sistema, se \
establecen los siguientes principios orientadores:

- El Compromiso de Desempeño, como mecanismo de asignación de responsabilidades evaluables mediante \
instrumentos y evidencia, debe dialogar con la asignación de la carga académica.
- La distribución de la carga horaria responde a la distribución de actividades y al mutuo acuerdo con la \
jefatura directa.
- Los/as académicos/as adscritos al SEJA reciben acompañamiento periódico de la Oficina de Evaluación de \
Desempeño Académico, para desarrollarse profesionalmente e impactar positivamente en la formación de \
nuestros estudiantes."""

NOMBRES_CORTOS = {"docencia": "Docencia", "investigacion": "Investigación, Creación e Innovación",
                  "vinculacion": "Vinculación con el Medio y Extensión", "gestion": "Gestión Académica"}


def cargar_funciones(ruta: Path | str = FUNCIONES) -> dict:
    return yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))


def _celda(texto) -> str:
    return str(texto if texto not in (None, "") else "—").replace("|", "/").replace("\n", " ")


def _tabla(encabezados: list[str], filas: list[list]) -> str:
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    lineas += ["| " + " | ".join(_celda(c) for c in fila) + " |" for fila in filas]
    return "\n".join(lineas)


def _pct(valor: float) -> str:
    return f"{valor:.1f}%".replace(".", ",")


def _lista(items: list[str]) -> str:
    items = [i for i in items if i]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " y " + items[-1]


def _identificacion(datos: dict, fecha_etiqueta: str, fecha: str) -> str:
    filas = [["Nombre académico/a", datos.get("academico")],
             ["Nombre jefatura", datos.get("jefatura")],
             ["Facultad", datos.get("facultad")],
             ["Unidad académica", datos.get("unidad")],
             ["Jerarquía y perfil", " · ".join(str(x).capitalize() for x in
                                               (datos.get("jerarquia"), datos.get("perfil")) if x)],
             ["Tipo de jornada", str(datos.get("jornada", "")).capitalize()],
             ["Tipo de contrato", datos.get("contrato")],
             ["Año de ingreso", datos.get("ingreso")],
             [fecha_etiqueta, fecha]]
    return _tabla(["Identificación", ""], [f for f in filas if f[1] not in (None, "")])


def _distribucion(datos: dict, declarado: dict[str, float], p_compromiso: float) -> str:
    horas = datos.get("horas") or {}
    filas = []
    for clave, pct in sorted(declarado.items(), key=lambda kv: -kv[1]):
        h = horas.get(clave)
        h = sum(h) / len(h) if isinstance(h, list) else h
        filas.append([NOMBRES_CORTOS[clave], f"{h:g}".replace(".", ",") if h is not None else "—",
                      _pct(pct), _pct(pct * p_compromiso)])
    return _tabla(["Ámbito", "Horas semanales", "% del compromiso", "Pondera en la calificación"], filas)


def _mecanismos(tareas: list[dict], modelo: dict) -> str:
    vistos = []
    for t in tareas:
        sub = modelo["ambitos"][t["ambito"]]["subcategorias"].get(t.get("subcategoria"), {})
        mec = ((t.get("evidencia") or {}).get("mecanismo") or (t.get("instrumento") or {}).get("nombre")
               or (sub.get("instrumento") if isinstance(sub, dict) else None) or "Por definir")
        if mec not in vistos:
            vistos.append(mec)
    return "; ".join(vistos)


def reporte_compromiso(datos: dict, modelo: dict | None = None) -> str:
    """Reporte del compromiso declarado (sin evaluar): resumen, distribución, actividades y alertas."""
    modelo = modelo or cargar_modelo()
    alertas: list[str] = []
    declarado = ponderacion_compromiso(datos, modelo, alertas)
    fijos = modelo["componentes_fijos"]
    p_compromiso = 1 - fijos["autoevaluacion"] - (0 if datos.get("exento_estudiantes") else fijos["estudiantes"])
    tareas = datos.get("tareas") or []
    for t in tareas:
        if t.get("ambito") not in modelo["ambitos"]:
            raise ErrorCompromiso(f"Actividad '{t.get('descripcion')}': ámbito '{t.get('ambito')}' no existe")

    maximo = max(declarado.values())
    dominantes = [NOMBRES_CORTOS[k].split(",")[0].lower() for k, v in declarado.items() if maximo - v < 1]
    funciones = [NOMBRES_CORTOS[k].lower() for k in modelo["ambitos"] if k in declarado]
    perfil = f", perfil {datos['perfil']}" if datos.get("perfil") else ""
    resumen = (f"Académico/a con jerarquía {str(datos.get('jerarquia', 'sin informar')).capitalize()}{perfil}, "
               f"jornada {datos.get('jornada', 'sin informar')} y contrato {datos.get('contrato', 'sin informar')}. "
               f"En el compromiso declara funciones de {_lista(funciones)}. Según las horas comprometidas, "
               f"{_lista(dominantes)} concentra{'n' if len(dominantes) > 1 else ''} la mayor parte "
               f"({_pct(maximo)}).")

    filas = []
    for clave, ambito in modelo["ambitos"].items():
        propias = [t for t in tareas if t["ambito"] == clave]
        if not propias and clave not in declarado:
            continue
        actividades = "; ".join(t.get("descripcion") or nombre_subcategoria(ambito["subcategorias"][t["subcategoria"]])
                                for t in propias)
        filas.append([NOMBRES_CORTOS[clave], actividades or "Sin actividades declaradas",
                      _mecanismos(propias, modelo) if propias else "—"])
        if clave in declarado and not propias:
            alertas.append(f"{NOMBRES_CORTOS[clave]} tiene horas comprometidas pero ninguna actividad declarada.")
        if propias and clave not in declarado:
            alertas.append(f"{NOMBRES_CORTOS[clave]} tiene actividades declaradas pero no horas: no pondera en la "
                           "calificación.")

    partes = [ENCABEZADO, f"# Reporte: Compromiso de Desempeño Académico {datos.get('periodo', '')}",
              "## Identificación",
              _identificacion(datos, "Fecha del reporte", datos.get("fecha_reporte") or date.today().isoformat()),
              "## Resumen", resumen, _distribucion(datos, declarado, p_compromiso),
              "## Actividades declaradas en el compromiso",
              _tabla(["Ámbito", "Actividades comprometidas", "Mecanismo de evidencia"], filas)]
    if alertas:
        partes += ["## Alertas para la jefatura", "\n".join(f"- {a}" for a in alertas)]
    partes += ["## Información adicional", _info_adicional(datos)]
    return "\n\n".join(partes) + "\n"


def _info_adicional(datos: dict, cierre: bool = False) -> str:
    filas = [["Compromiso de Desempeño", datos.get("enlace_compromiso")],
             ["Fecha de entrega del compromiso", datos.get("fecha_compromiso")]]
    if cierre:
        filas.append(["Fecha de cierre del informe", datos.get("fecha_cierre") or date.today().isoformat()])
    filas.append(["Más información", "seja@umce.cl"])
    return _tabla(["Información adicional", ""], [f for f in filas if f[1]])


def funciones_jerarquia(datos: dict, resultado: Resultado, funciones: dict | None = None) -> tuple[str, list]:
    """(título, filas [función, estado]) de las funciones del reglamento para la jerarquía y el perfil."""
    funciones = funciones or cargar_funciones()
    jerarquia = str(datos.get("jerarquia", "")).lower()
    perfil = str(datos.get("perfil", "")).lower()
    reglas = funciones["jerarquias"].get(jerarquia)
    if not reglas:
        return "", []
    lista = reglas.get("todos") or reglas.get(perfil)
    if not lista:
        return "", []
    articulo = reglas["articulo"] if isinstance(reglas["articulo"], int) else reglas["articulo"][perfil]
    tareas = [t for a in resultado.ambitos for t in a.tareas]
    filas = []
    for f in lista:
        def coincide(t, patron):
            ambito, sub = patron.split(".")
            return t.ambito == ambito and sub in ("*", t.subcategoria)
        propias = [t for t in tareas if any(coincide(t, p) for p in f["subcategorias"])]
        if any(t.puntaje > 0 for t in propias):
            estado = "Sí"
        elif propias:
            estado = "Sin evidencia"
        else:
            estado = "Opcional, no declarada" if f.get("opcional") else "No declarada"
        filas.append([f["funcion"], estado])
    titulo = f"{jerarquia.capitalize()}{', perfil ' + perfil if 'todos' not in reglas else ''} (art. {articulo})"
    return titulo, filas


def informe_cierre(datos: dict, modelo: dict | None = None, funciones: dict | None = None) -> str:
    """Informe de Cierre del período, con la calificación SEJA."""
    modelo = modelo or cargar_modelo()
    r = calificar(datos, modelo)
    partes = [ENCABEZADO, f"# Informe de Cierre: Compromiso de Desempeño Académico {r.periodo}",
              "## Identificación",
              _identificacion(datos, "Fecha de cierre", datos.get("fecha_cierre") or date.today().isoformat())]

    if r.estado == "suspendida":
        partes += ["## Evaluación suspendida",
                   f"{r.descripcion}: {r.situacion_especial}. La evaluación del período queda suspendida y se "
                   f"informa a {r.informar_a}.",
                   "## Información adicional", _info_adicional(datos, cierre=True)]
        return "\n\n".join(partes) + "\n"

    partes += ["## Objetivos", "\n".join([
        "- Conocer el grado de cumplimiento de las actividades declaradas en el compromiso de desempeño.",
        "- Calificar el desempeño según el modelo SEJA.",
        "- Comparar las actividades declaradas con las funciones de la jerarquía, según la normativa vigente.",
        "- Identificar oportunidades y fortalezas que promuevan el desarrollo de la carrera académica.",
        "- Registrar lo que destaca, para el reconocimiento institucional."])]

    partes.append("## Actividades comprometidas")
    for a in r.ambitos:
        partes.append(f"### Área de desempeño: {a.nombre} (pondera {_pct(a.ponderacion * 100)})")
        filas = [[t.descripcion + (" ★" if t.destaca else ""), t.comprometido, t.evidenciado,
                  t.mecanismo, _pct(t.puntaje)] for t in a.tareas]
        if filas:
            partes.append(_tabla(["Actividad", "Comprometido", "Evidenciado", "Mecanismo de evidencia",
                                  "% de cumplimiento"], filas))
        else:
            partes.append("Sin actividades evaluadas.")
        partes.append(f"Cumplimiento del área: **{_pct(a.puntaje)}** ({a.letra}).")

    filas = [[a.nombre, _pct(a.ponderacion * 100), _pct(a.puntaje), a.letra] for a in r.ambitos]
    filas.append(["Autoevaluación", _pct(r.ponderacion_autoevaluacion * 100), _pct(r.autoevaluacion), ""])
    if r.estudiantes is not None:
        filas.append(["Evaluación de estudiantes", _pct(r.ponderacion_estudiantes * 100), _pct(r.estudiantes), ""])
    partes += ["## Calificación SEJA",
               _tabla(["Componente", "Pondera", "Cumplimiento", "Letra"], filas),
               f"**Cumplimiento final: {_pct(r.puntaje)} · Calificación {r.letra}** ({r.descripcion}). "
               f"Escala numérica: {r.nota}."]

    if r.destacados:
        partes += ["## Reconocimiento institucional",
                   "Destaca en:\n\n" + "\n".join(f"- {d.descripcion} ({NOMBRES_CORTOS[d.ambito]}): "
                                               f"{texto_destacado(d)}." for d in r.destacados)]

    titulo, filas_func = funciones_jerarquia(datos, r, funciones)
    if filas_func:
        partes += [f"## Funciones de la jerarquía: {titulo}",
                   _tabla(["Función según el Reglamento de Carrera Académica", "Cumplimiento"], filas_func),
                   "_Según los registros proporcionados por el académico o la académica a la Oficina de "
                   "Evaluación de Desempeño Académico, a través de los canales digitales dispuestos._"]

    partes += ["## Oportunidades y fortalezas para el desarrollo profesional",
               _oportunidades_fortalezas(r, filas_func)]
    partes += ["## Orientaciones SEJA", ORIENTACIONES, "## Información adicional", _info_adicional(datos, True)]
    return "\n\n".join(partes) + "\n"


def _oportunidades_fortalezas(r: Resultado, filas_func: list) -> str:
    textos = []
    fuertes = [f"{a.nombre.split(' en ')[0].split(',')[0].lower()} ({_pct(a.puntaje)})"
               for a in r.ambitos if a.letra in ("A+", "A")]
    if fuertes:
        textos.append(f"Se reconocen como fortalezas del período {r.periodo} su desempeño en {_lista(fuertes)}.")
    if r.destacados:
        textos.append("Además, supera lo comprometido en: " + _lista([d.descripcion for d in r.destacados]) + ".")
    pendientes = [t for a in r.ambitos for t in a.tareas if t.puntaje < 100]
    if pendientes:
        textos.append("Oportunidades de mejora: completar o evidenciar " +
                      _lista([f"{t.descripcion} ({_pct(t.puntaje)})" for t in pendientes]) + ".")
    faltan = [f for f, estado in filas_func if estado in ("No declarada", "Sin evidencia")]
    if faltan:
        textos.append("Según la normativa vigente para su jerarquía, debe además: " +
                      _lista([f[0].lower() + f[1:] for f in faltan]) + ".")
    elif filas_func:
        textos.append("Las actividades declaradas cubren las funciones que la normativa establece para su "
                      "jerarquía y perfil.")
    textos += r.observaciones
    return "\n\n".join(textos)


def guardar(markdown: str, salida: Path | str) -> Path:
    """Guarda en .md, o en .docx/.odt/.html con pandoc."""
    salida = Path(salida)
    if salida.suffix == ".md":
        salida.write_text(markdown, encoding="utf-8")
        return salida
    if not shutil.which("pandoc"):
        raise ErrorCompromiso(f"Para generar {salida.suffix} se necesita pandoc (https://pandoc.org); "
                              "también puedes guardar en .md")
    with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as tmp:
        tmp.write(markdown)
    try:
        subprocess.run(["pandoc", tmp.name, "-f", "markdown", "-o", str(salida)], check=True)
    finally:
        Path(tmp.name).unlink(missing_ok=True)
    return salida
