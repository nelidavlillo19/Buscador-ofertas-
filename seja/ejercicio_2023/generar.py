"""Genera el informe extendido del ejercicio de calificación SEJA con los registros 2023 (anonimizados).

Uso: python -m seja.ejercicio_2023.generar [-o informe.md|informe.docx]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

from seja.calificacion import calificar, cargar_modelo, clasificar, ponderacion_compromiso, texto_destacado
from seja.reportes import NOMBRES_CORTOS, funciones_jerarquia, guardar

DATOS = Path(__file__).parent / "sujetos.yaml"
ORDEN = ["docencia", "investigacion", "vinculacion", "gestion"]
CORTO = {"docencia": "Doc", "investigacion": "ICI", "vinculacion": "VcM", "gestion": "Gest"}


def n(x: float, d: int = 1) -> str:
    """Número con coma decimal."""
    return f"{x:.{d}f}".replace(".", ",")


def tex(x: float, d: int = 1) -> str:
    """Número con coma decimal para LaTeX."""
    return f"{x:.{d}f}".replace(".", "{,}")


def _lista(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " y " + items[-1]


def tabla(encabezados: list[str], filas: list[list]) -> str:
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    lineas += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(lineas)


def pesos(sujeto: dict, escenario: str) -> dict[str, float]:
    """% de cada ámbito. E1: igual peso entre ámbitos con actividades. E2: el o los ámbitos que el reporte
    declara mayoritarios en horas pesan el doble."""
    ambitos = [a for a in ORDEN if any(t["ambito"] == a for t in sujeto["tareas"])]
    k = {a: (2 if escenario == "E2" and a in sujeto["mayoria_reporte"] else 1) for a in ambitos}
    total = sum(k.values())
    return {a: k[a] / total * 100 for a in ambitos}


def evaluar(sujeto: dict, escenario: str, modelo: dict):
    datos = {"academico": f"Sujeto {sujeto['sujeto']}", "periodo": 2023, "jerarquia": sujeto["jerarquia"],
             "perfil": sujeto["perfil_supuesto"], "compromiso": pesos(sujeto, escenario),
             "tareas": sujeto["tareas"],
             # La autoevaluación y la evaluación de estudiantes no están en los registros 2023: se calcula
             # aparte el cumplimiento del compromiso (C) y se completa con el supuesto neutro AE = EE = C.
             "autoevaluacion": {"porcentaje": 100}, "estudiantes": {"porcentaje": 100}}
    r = calificar(datos, modelo)
    c = round(sum(a.declarado / 100 * a.puntaje for a in r.ambitos), 1)
    return datos, r, c


def seccion_formulas() -> str:
    return r"""## 3. Modelo de calificación y fórmulas

### 3.1 Cumplimiento de cada tarea ($p_t$)

Cada actividad del compromiso es una **tarea** $t$. Su cumplimiento $p_t$ (en %) se obtiene con el instrumento
o la evidencia que le corresponde:

- **Pauta de afirmaciones** (Cumple / No cumple / No aplica), con $C$ afirmaciones cumplidas y $NC$ no cumplidas;
  las "no aplica" no cuentan:
$$p_t = \frac{C}{C + NC} \times 100$$
- **Instrumento con escala** (por ejemplo, rúbrica de 1 a 4 o nota de 1 a 7), con puntaje $x$:
$$p_t = \frac{x - x_{\min}}{x_{\max} - x_{\min}} \times 100$$
- **Evidencia con meta**: $M$ comprometido, $L$ logrado, y $f$ el factor de jornada del art. 37
  ($f = 1$ si no hay situación especial):
$$p_t = \min\left(\frac{L}{M \cdot f},\ 1\right) \times 100 \qquad \text{(sin excedente validado)}$$
$$p_t = \min\left(\frac{L}{M \cdot f} \times 100,\ 120\right) \qquad \text{(con excedente validado, } L > M\text{)}$$
- **Evidencia por etapa** (secuencias: formulación → postulación → adjudicación → ejecución → cierre;
  en preparación → enviada → aceptada → publicada; planificación → ejecución → finalizada):
$$p_t = \begin{cases} 100 & \text{si la etapa evidenciada es igual o posterior a la comprometida} \\
50 & \text{si la etapa evidenciada es anterior a la comprometida} \\ 0 & \text{sin evidencia} \end{cases}$$

El **tope de 120%** limita lo que una tarea aporta a la calificación. El cumplimiento real (sin tope) y el avance
más allá de la etapa comprometida quedan **registrados como destacados** para el reconocimiento institucional.

### 3.2 Cumplimiento de cada ámbito ($S_a$)

Las tareas se promedian dentro de su ámbito $a$ (docencia; investigación, creación e innovación; vinculación con
el medio; gestión académica). $\pi_t$ es un peso opcional de la tarea, que por defecto vale 1:
$$S_a = \frac{\sum_{t \in a} \pi_t \, p_t}{\sum_{t \in a} \pi_t}$$

### 3.3 Ponderación de cada ámbito ($w_a$)

La ponderación sale de las **horas semanales** comprometidas en cada ámbito, $h_a$. Si la carga cambia entre
semestres $s$, se promedia:
$$h_a = \frac{1}{|S|} \sum_{s \in S} h_{a,s} \qquad\qquad w_a = \frac{h_a}{\sum_{b} h_b}, \qquad \sum_a w_a = 1$$

### 3.4 Cumplimiento del compromiso ($C$) y calificación final ($F$)

$$C = \sum_a w_a \, S_a$$
$$F = \alpha \sum_a w_a \, S_a + 0{,}10 \cdot AE + 0{,}10 \cdot EE = \alpha \cdot C + 0{,}10 \cdot AE + 0{,}10 \cdot EE$$

$AE$ es la autoevaluación y $EE$ la evaluación de estudiantes, ambas de 0 a 100%. $\alpha = 0{,}80$ en general,
y $\alpha = 0{,}90$ cuando la persona está eximida de docencia y no tiene evaluación de estudiantes. Así, el peso
efectivo de cada ámbito en la calificación es:
$$\omega_a = \alpha \cdot w_a$$

### 3.5 Clasificación y escala numérica

| Letra | Condición sobre $F$ | Desempeño |
|---|---|---|
| A+ | $F \geq 101\%$ | Sobresaliente: cumplimiento sobre lo comprometido |
| A | $90\% \leq F < 101\%$ | Cumplimiento pleno |
| B | $75\% \leq F < 90\%$ | Cumplimiento bueno |
| C | $55\% \leq F < 75\%$ | Cumplimiento parcial (requiere mejora) |
| D | $F < 55\%$ | Insuficiente |

Escala numérica (tabla de equivalencia): 90–100% → 7; 80–89% → 6; 70–79% → 5; 60–69% → 4; 50–59% → 3;
40–49% → 2; 39% o menos → 1.

### 3.6 Situaciones especiales (art. 37)

- Una ausencia justificada de más de 5 meses continuos suspende la evaluación.
- En cualquier otra situación, las metas se ajustan con $f = \dfrac{\%\ \text{de jornada dedicado a sus funciones}}{100}$.
- En ambos casos se informa a la Oficina de Evaluación de Desempeño Académico y a las autoridades
  correspondientes."""


def seccion_metodo() -> str:
    return r"""## 4. Cómo se corrió el ejercicio

1. **Tareas y evidencia.** Cada fila de los informes de cierre se registró como una tarea, con su ámbito y su
   subcategoría del catálogo SEJA, la etapa comprometida y la etapa evidenciada. Una actividad "sin evidencia"
   obtiene $p_t = 0$. Las actividades de "perfeccionamiento" se registraron como formación continua (docencia).
2. **Evidencia validada.** Se considera validado el avance o excedente que tiene un mecanismo de respaldo
   (carta, constancia, certificado, informe o registro).
3. **Ponderación.** Los reportes e informes 2023 **no registran horas por ámbito**, por lo que $w_a$ no se puede
   calcular con la fórmula 3.3. Se usan dos escenarios:
   - **E1, igual peso:** $w_a = \dfrac{1}{n}$, con $n$ el número de ámbitos con actividades.
   - **E2, según el reporte:** el o los ámbitos que el reporte declara mayoritarios en horas pesan el doble,
     $w_a = \dfrac{k_a}{\sum_b k_b}$, con $k_a = 2$ si el ámbito es mayoritario y $k_a = 1$ si no.
4. **Autoevaluación y estudiantes.** No hay registro de $AE$ ni $EE$. Se informa $C$ y se usa el supuesto neutro
   $AE = EE = C$, con el que $F = C$. Como referencia se informa $F_{\max} = 0{,}8\,C + 20$, la calificación si
   $AE = EE = 100\%$.
5. **Perfil.** El formulario 2023 no pedía perfil. Se supone uno para revisar las funciones del Reglamento de
   Carrera Académica, que dependen de la jerarquía y del perfil.
6. **Sujetos 07 a 09.** Tienen compromiso con horas, pero no informe de cierre. Con ellos se aplica la
   ponderación por horas (fórmula 3.3) y se revisan los registros."""


def seccion_sujeto(s: dict, modelo: dict) -> tuple[str, dict]:
    datos1, r1, c1 = evaluar(s, "E1", modelo)
    _, r2, c2 = evaluar(s, "E2", modelo)
    out = [f"### Sujeto {s['sujeto']}"]
    jer = s["jerarquia"].capitalize()
    nota_jer = "" if s["jerarquia"] == s["jerarquia_reporte"] else \
        f" (el reporte de octubre registra {s['jerarquia_reporte'].capitalize()})"
    out.append(f"**Jerarquía:** {jer}{nota_jer} · **Perfil supuesto:** {s['perfil_supuesto']} · "
               f"**Jornada:** {s['jornada']} · **Mayoría de horas según el reporte:** "
               f"{', '.join(NOMBRES_CORTOS[a] for a in s['mayoria_reporte'])}")

    filas = []
    for a in r1.ambitos:
        for t in a.tareas:
            filas.append([NOMBRES_CORTOS[a.ambito], t.descripcion + (" ★" if t.destaca else ""), t.comprometido,
                          t.evidenciado, t.mecanismo or "—", n(t.puntaje) + "%"])
    out.append(tabla(["Ámbito", "Actividad", "Comprometido", "Evidenciado", "Mecanismo", "$p_t$"], filas))

    filas = []
    for a1, a2 in zip(r1.ambitos, r2.ambitos):
        filas.append([NOMBRES_CORTOS[a1.ambito], len(a1.tareas), n(a1.puntaje) + "%", a1.letra,
                      n(a1.declarado / 100, 3), n(a2.declarado / 100, 3)])
    out.append(tabla(["Ámbito", "Tareas", "$S_a$", "Letra del ámbito", "$w_a$ (E1)", "$w_a$ (E2)"], filas))

    for esc, r, c in (("E1", r1, c1), ("E2", r2, c2)):
        suma = " + ".join(f"{tex(a.declarado / 100, 3)} \\cdot {tex(a.puntaje)}" for a in r.ambitos)
        out.append(f"$$C_{{{esc}}} = {suma} = {tex(c)}\\%$$")
    f1max, f2max = 0.8 * c1 + 20, 0.8 * c2 + 20
    out.append(tabla(["Escenario", "$C$", "$F$ (AE = EE = C)", "Letra", "Escala", "$F_{\\max}$ (AE = EE = 100)",
                      "Letra con $F_{\\max}$"],
                     [["E1 igual peso", n(c1) + "%", n(c1) + "%", clasificar(c1, modelo),
                       escala(c1, modelo), n(f1max) + "%", clasificar(round(f1max, 1), modelo)],
                      ["E2 según reporte", n(c2) + "%", n(c2) + "%", clasificar(c2, modelo),
                       escala(c2, modelo), n(f2max) + "%", clasificar(round(f2max, 1), modelo)]]))

    if r1.destacados:
        out.append("**Destaca en** (registro para reconocimiento institucional): " +
                   "; ".join(f"{d.descripcion}: {texto_destacado(d)}" for d in r1.destacados) + ".")
    titulo, ff = funciones_jerarquia(datos1, r1)
    pendientes = [f for f, e in ff if e in ("No declarada", "Sin evidencia")]
    if ff:
        cumplidas = sum(1 for _, e in ff if e == "Sí")
        obligatorias = sum(1 for f, e in ff if not e.startswith("Opcional"))
        out.append(f"**Funciones del Reglamento de Carrera Académica, {titulo}:** {cumplidas} cumplidas de "
                   f"{len(ff)}. Pendientes: " + ("; ".join(pendientes) if pendientes else "ninguna") + ".")
    out.append(f"**Informe de cierre 2023 (Res. 320/93):** {s['informe_2023']}")
    out.append("**Hallazgos en los registros:**\n\n" + "\n".join(f"- {h}" for h in s["hallazgos"]))
    resumen = {"sujeto": s["sujeto"], "jer": jer, "ambitos": {a.ambito: a.puntaje for a in r1.ambitos},
               "c1": c1, "c2": c2, "l1": clasificar(c1, modelo), "l2": clasificar(c2, modelo),
               "dest": len(r1.destacados), "pend": len(pendientes),
               "sin_ev": sum(1 for a in r1.ambitos for t in a.tareas if t.puntaje == 0),
               "tareas": sum(len(a.tareas) for a in r1.ambitos)}
    return "\n\n".join(out), resumen


def escala(p: float, modelo: dict) -> int:
    for minimo, nota in modelo["escala_numerica"]:
        if p >= minimo:
            return nota
    return 1


def seccion_horas(s: dict, modelo: dict) -> str:
    out = [f"### Sujeto {s['sujeto']}"]
    out.append(f"**Jerarquía:** {s['jerarquia'].capitalize()} · **Perfil supuesto:** {s['perfil_supuesto']} · "
               f"**Jornada:** {s['jornada']}")
    out.append("\n".join(f"- **{NOMBRES_CORTOS[a]}:** {txt}" for a, txt in s["actividades"].items()))
    obs: list[str] = []
    datos = {"horas": s["horas"], "jornada": s["jornada"], "jerarquia": s["jerarquia"],
             "perfil": s["perfil_supuesto"]}
    w = ponderacion_compromiso(datos, modelo, obs)
    total_decl = sum(s["declarado"].values())
    h = {a: (sum(v) / len(v) if isinstance(v, list) else v) for a, v in s["horas"].items()}
    total = sum(h.values())
    filas = []
    for a in ORDEN:
        if a in s["declarado"] or a in h:
            d = s["declarado"].get(a, 0)
            filas.append([NOMBRES_CORTOS[a], n(d), n(d / total_decl * 100) + "%", n(h.get(a, 0)),
                          n(w.get(a, 0)) + "%", n(0.8 * w.get(a, 0)) + "%"])
    out.append(tabla(["Ámbito", "Horas declaradas", "% declarado", "$h_a$ ordenadas", "$w_a$", "$\\omega_a$"],
                     filas))
    partes = " + ".join(tex(h[a]) for a in ORDEN if a in h)
    out.append(f"$$\\sum_b h_b = {partes} = {tex(total)} \\text{{ h semanales}}$$")
    out.append("$$" + r" \qquad ".join(f"w_{{\\text{{{CORTO[a]}}}}} = \\frac{{{tex(h[a])}}}{{{tex(total)}}} = "
                                        f"{tex(w[a] / 100, 3)}" for a in ORDEN if a in h) + "$$")
    obs = [re.sub(r"(\d)\.(\d)", r"\1,\2", x) for x in obs]
    out.append("**Notas:**\n\n" + "\n".join(f"- {x}" for x in s["notas"] + obs))
    return "\n\n".join(out)


def generar() -> str:
    modelo = cargar_modelo()
    datos = yaml.safe_load(DATOS.read_text(encoding="utf-8"))
    detalles, resumenes = [], []
    for s in datos["con_cierre"]:
        texto, res = seccion_sujeto(s, modelo)
        detalles.append(texto)
        resumenes.append(res)

    filas = [[f"Sujeto {r['sujeto']}", r["jer"]] +
             [n(r["ambitos"][a]) + "%" if a in r["ambitos"] else "—" for a in ORDEN] +
             [f"{n(r['c1'])}% ({r['l1']})", f"{n(r['c2'])}% ({r['l2']})", f"{r['sin_ev']} de {r['tareas']}",
              r["dest"], r["pend"]] for r in resumenes]
    tabla_resumen = tabla(["Sujeto", "Jerarquía", "$S$ Doc", "$S$ ICI", "$S$ VcM", "$S$ Gest", "$C$ E1 (letra)",
                           "$C$ E2 (letra)", "Tareas sin evidencia", "Destacados", "Funciones pendientes"], filas)
    letras = [r["l1"] for r in resumenes]
    conteo = ", ".join(f"{letras.count(l)} en {l}" for l in ["A+", "A", "B", "C", "D"] if letras.count(l))
    cambios = [r["sujeto"] for r in resumenes if r["l1"] != r["l2"]]

    partes = [
        "---\ntitle: \"Ejercicio de calificación SEJA con los registros 2023\"\n"
        "subtitle: \"Informe extendido · Oficina de Evaluación de Desempeño Académico\"\nlang: es\n---",
        "## 1. Resumen ejecutivo",
        f"Se aplicó el modelo de calificación SEJA a los registros 2023 de **nueve sujetos**. Seis de ellos (sujetos "
        f"01 a 06) tienen reporte del compromiso e informe de cierre con el cumplimiento de cada actividad. Los otros "
        f"tres (sujetos 07 a 09) tienen formulario de compromiso con horas, pero no informe de cierre.",
        f"- **Resultados (escenario E1, igual peso por ámbito):** {conteo}. "
        + (f"La letra cambia según cómo se pondera en {'el sujeto' if len(cambios) == 1 else 'los sujetos'} "
           f"{_lista(cambios)}."
           if cambios else "La letra no cambia entre los escenarios E1 y E2.")
        + " Los informes 2023 no asignaban calificación: sólo marcaban 100% o 0% por actividad.",
        "- **La ponderación no se puede calcular con los registros 2023.** Los reportes e informes no registran horas por "
        "ámbito; afirman qué ámbito es «mayoría» sin datos que lo respalden. Por eso el ejercicio usa dos escenarios de "
        "ponderación, y en los casos con actividades sin evidencia la letra depende del escenario.",
        "- **El modelo distingue lo que el informe 2023 no distinguía:** el excedente (más ponencias que las comprometidas), "
        "el avance más allá de la etapa comprometida (proyectos cerrados, artículos publicados) y las actividades "
        "comprometidas sin evidencia, que hoy bajan el cumplimiento del ámbito.",
        "- **Los registros tienen inconsistencias.** Hay resúmenes que contradicen su propia tabla, una jerarquía que "
        "cambia entre el reporte y el informe, actividades declaradas que no se evalúan al cierre, actividades en el "
        "ámbito equivocado y horas que se registran de tres formas distintas.",
        "- **Recomendación principal.** Registrar en UCampus las horas semanales por ámbito, cada actividad con su "
        "subcategoría y su etapa comprometida, y la autoevaluación y la evaluación de estudiantes. Con eso la calificación "
        "se calcula automáticamente con las fórmulas de la sección 3.",
        "## 2. Fuentes y anonimización",
        "- **Reportes de Compromiso de Desempeño 2023** (octubre 2023): identificación, resumen, actividades por "
        "dimensión y mecanismo de evidencia.",
        "- **Informes de Cierre 2023** (marzo 2024): etapa comprometida y evidenciada, mecanismo, % de cumplimiento por "
        "actividad, funciones de la Res. 320/93, y oportunidades y fortalezas.",
        "- **Formularios de Compromiso de Desempeño 2023** con horas por actividad, y el formulario e instructivo 2024 "
        "de UCampus.",
        "- **Normativa de referencia:** propuesta de Reglamento de Carrera Académica, Síntesis SEJA (agosto 2026) y "
        "Jornada Modelo de Evaluación SEJA 2024.",
        "Las personas se identifican como *sujeto 01, 02…*. Las asignaturas se numeran por sujeto (*asignatura 1, "
        "asignatura 2…*). Se omiten los nombres de personas, jefaturas, departamentos, proyectos, eventos y "
        "comisiones.",
        seccion_formulas(),
        seccion_metodo(),
        "## 5. Resultados de los sujetos con informe de cierre (01 a 06)",
        tabla_resumen,
        "$S$ es el cumplimiento de cada ámbito y $C$ el cumplimiento del compromiso. «—» indica que no hay actividades "
        "en ese ámbito. Las funciones pendientes se cuentan según el Reglamento de Carrera Académica, con el perfil "
        "supuesto.",
        *detalles,
        "## 6. Ponderación por horas (sujetos 07 a 09)",
        "Se compara el % que resulta de las horas tal como se declararon con el % que resulta de las horas ordenadas: "
        "semanales, promediando semestres, y con cada actividad en el ámbito que le corresponde según el catálogo. "
        "$\\omega_a = 0{,}8\\,w_a$ es el peso efectivo del ámbito en la calificación final.",
        *[seccion_horas(s, modelo) for s in datos["solo_compromiso"]],
        "## 7. Hallazgos transversales",
        "\n".join([
            "1. **Sin horas no hay ponderación.** Ningún reporte ni informe 2023 registra horas por ámbito, y el "
            "formulario 2024 eliminó las horas por actividad. La afirmación «X es mayoría» no se puede verificar.",
            "2. **Los informes 2023 no califican.** Marcan 100% o 0% por actividad, no agregan por ámbito ni asignan una "
            "letra, y no distinguen el excedente ni el avance más allá de lo comprometido.",
            "3. **Inconsistencias entre documentos del mismo sujeto.** Hay resúmenes que no coinciden con su tabla "
            "(sujetos 01 y 02), una jerarquía distinta entre el reporte y el informe (sujeto 05), actividades "
            "declaradas que no se evalúan al cierre (sujetos 03 y 06) y conteos distintos de actividades (sujeto 02).",
            "4. **Conclusiones que contradicen la tabla de funciones.** Un informe afirma que las actividades son las "
            "exigidas para la jerarquía aunque marca 4 funciones como no cumplidas (sujeto 02).",
            "5. **Clasificación de actividades.** Los claustros de postgrado, los núcleos de investigación, la revisión de "
            "artículos, las representaciones internacionales y la organización de eventos se registran en gestión, pero "
            "pertenecen a investigación o a VcM. El «perfeccionamiento» se registra como un área aparte.",
            "6. **Las horas se registran de tres formas.** Hay sumas de los dos semestres, valores «x + x» y horas con "
            "minutos escritas como decimales («16.45»).",
            "7. **La normativa cambia.** Los informes 2023 revisan funciones de la Res. 320/93. La propuesta de "
            "Reglamento de Carrera Académica define funciones por jerarquía y perfil, con carga docente esperada, lo que "
            "deja más funciones pendientes en varios sujetos (por ejemplo, formación de académicos, redes y formación "
            "continua)."]),
        "## 8. Recomendaciones",
        "\n".join([
            "1. Registrar en UCampus las **horas semanales por ámbito** (por semestre en docencia) y calcular el resumen "
            "automáticamente con la fórmula 3.3.",
            "2. Declarar cada actividad eligiendo su **subcategoría del catálogo SEJA** y su **etapa comprometida**; al "
            "cierre, registrar la **etapa evidenciada** y el **mecanismo**.",
            "3. Aplicar y registrar la **autoevaluación** y la **evaluación de estudiantes** (20% de la calificación).",
            "4. Pedir el **perfil** (investigador/a o vinculador/a) y mostrar el rango de carga docente de la jerarquía.",
            "5. Generar el reporte de octubre y el informe de cierre **desde los mismos datos** (`python -m seja reporte` "
            "y `python -m seja cierre`), para evitar las inconsistencias entre documentos.",
            "6. Mantener el registro de **destacados** (excedentes y avances validados) para el reconocimiento "
            "institucional."]),
        "## Anexo. Parámetros del modelo",
        tabla(["Parámetro", "Valor"], [
            ["Autoevaluación / evaluación de estudiantes", "10% / 10%"],
            ["Compromiso (ámbitos)", "80% (90% si está eximido/a de docencia)"],
            ["Tope por tarea con excedente validado", "120%"],
            ["Etapa evidenciada anterior a la comprometida", "50%"],
            ["Suspensión (art. 37)", "Ausencia justificada de más de 5 meses continuos"],
            ["Umbrales", "A+ ≥ 101%; A 90–100%; B 75–89%; C 55–74%; D < 55%"],
            ["Jornada", "Completa 44 h; media 22 h"]]),
    ]
    return "\n\n".join(partes) + "\n"


if __name__ == "__main__":
    texto = generar()
    if "-o" in sys.argv:
        print(f"Guardado en {guardar(texto, sys.argv[sys.argv.index('-o') + 1])}")
    else:
        print(texto)
