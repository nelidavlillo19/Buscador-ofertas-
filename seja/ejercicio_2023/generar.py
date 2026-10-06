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


def _horas_semanales(v) -> float:
    return sum(v) / len(v) if isinstance(v, list) else float(v)


def _formula_horas(h: dict[str, float], w: dict[str, float]) -> str:
    total = sum(h.values())
    partes = " + ".join(tex(h[a]) for a in ORDEN if a in h)
    lineas = [f"$$\\sum_b h_b = {partes} = {tex(total)} \\text{{ h semanales}}$$"]
    lineas.append("$$" + r" \qquad ".join(f"w_{{\\text{{{CORTO[a]}}}}} = \\frac{{{tex(h[a])}}}{{{tex(total)}}} = "
                                          f"{tex(w[a] / 100, 3)}" for a in ORDEN if a in h) + "$$")
    return "\n\n".join(lineas)


def _rangos_docencia(jerarquia: str | None, w_doc: float, modelo: dict) -> str | None:
    if not jerarquia:
        return None
    rangos = modelo["carga_docente"].get(jerarquia, {})
    textos = [f"{p} {r[0]}–{r[1]}%" for p, r in rangos.items()]
    dentro = [p for p, r in rangos.items() if r[0] <= round(w_doc, 1) <= r[1]]
    estado = ("dentro del rango para " + _lista(dentro)) if dentro else "fuera del rango"
    return (f"La docencia pesa {n(w_doc)}%: {estado} del reglamento para {jerarquia} "
            f"({'; '.join(textos)}).")


def seccion_compromiso_2024(s: dict, modelo: dict) -> tuple[str, dict]:
    from seja.calificacion import situacion_especial
    out = [f"### Sujeto {s['sujeto']}" + (" (también en 2023)" if s.get("vinculo_2023") or s["sujeto"] == "02" else "")]
    out.append(f"**Jerarquía:** {s['jerarquia'].capitalize() if s.get('jerarquia') else 'no registrada en el formulario 2024'}"
               f" · **Formulario completo:** {'sí' if s['completo'] else 'no'} · **Declarado:** {s['declarado']}")
    out.append("\n".join(f"- **{NOMBRES_CORTOS[a]}:** {txt}" for a, txt in s["actividades"].items()))
    res = {"sujeto": s["sujeto"], "completo": s["completo"], "w": {}, "situacion": ""}
    notas = list(s["notas"])
    if s["horas"]:
        h = {a: _horas_semanales(v) for a, v in s["horas"].items()}
        obs: list[str] = []
        w = ponderacion_compromiso({"horas": s["horas"], "jornada": "completa"}, modelo, obs)
        out.append(tabla(["Ámbito", "$h_a$ (h semanales)", "$w_a$", "$\\omega_a$ (peso en la calificación)"],
                         [[NOMBRES_CORTOS[a], n(h[a]), n(w[a]) + "%", n(0.8 * w[a]) + "%"] for a in ORDEN if a in h]))
        out.append(_formula_horas(h, w))
        rango = _rangos_docencia(s.get("jerarquia"), w.get("docencia", 0), modelo)
        notas += [re.sub(r"(\d)\.(\d)", r"\1,\2", o) for o in obs] + ([rango] if rango else [])
        res["w"] = w
        res["total"] = sum(h.values())
    else:
        out.append("_Sin horas por ámbito: no se puede calcular la ponderación $w_a$._")
    if s.get("situacion_por_definir"):
        res["situacion"] = "Por definir"
        notas.append("**Art. 37: por definir** — " + s["situacion_por_definir"])
    elif s.get("situacion_especial"):
        suspendida, factor, texto = situacion_especial({"situacion_especial": s["situacion_especial"]}, modelo)
        res["situacion"] = "Suspendida" if suspendida else f"Proporcional ({n(factor * 100)}%)"
        notas.append(("**Art. 37: evaluación suspendida** — " if suspendida else
                      f"**Art. 37: evaluación proporcional, $f = {tex(factor, 3)}$** — ")
                     + re.sub(r"(\d)\.(\d)", r"\1,\2", texto) + ".")
    nombres = modelo["etapas"]["nombres"]
    filas = []
    for t in s["tareas"]:
        sub = modelo["ambitos"][t["ambito"]]["subcategorias"][t["subcategoria"]]
        comp = f"Meta: {t['meta']}" if "meta" in t else nombres.get(t.get("etapa"), t.get("etapa", "—"))
        filas.append([NOMBRES_CORTOS[t["ambito"]], t["descripcion"], comp,
                      sub.get("instrumento", "Por definir") if isinstance(sub, dict) else "Por definir"])
    out.append("**Plan de evaluación al cierre** (cada actividad se evaluará con la fórmula 3.1 que le corresponde):")
    out.append(tabla(["Ámbito", "Actividad", "Etapa o meta comprometida", "Evidencia esperada"], filas))
    out.append("**Notas:**\n\n" + "\n".join(f"- {x}" for x in notas))
    res["tareas"] = len(s["tareas"])
    return "\n\n".join(out), res


def _datos_cierre(s: dict) -> dict:
    tareas = []
    for t in s["tareas"]:
        evidencia = {"estado": t["estado"]}
        for k in ("mecanismo", "excedente", "validado", "fuente"):
            if k in t:
                evidencia[k] = t[k]
        tareas.append({"ambito": t["ambito"], "subcategoria": t["subcategoria"], "descripcion": t["descripcion"],
                       "evidencia": evidencia})
    if s.get("ponderacion") == "igual":
        ambitos = [a for a in ORDEN if a in s["horas"] or any(t["ambito"] == a for t in s["tareas"])]
        pond = {"compromiso": {a: 100 / len(ambitos) for a in ambitos}}
    else:
        pond = {"horas": s["horas"]}
    return {**pond, "tareas": tareas, "jerarquia": s["jerarquia"],
            "autoevaluacion": {"porcentaje": 100}, "estudiantes": {"porcentaje": 100}}


def seccion_cierre_2024(s: dict, modelo: dict) -> tuple[str, dict]:
    out = [f"### Sujeto {s['sujeto']}"]
    out.append(f"**Jerarquía:** {s['jerarquia'].capitalize()} · **Compromiso:** {s['compromiso']}")
    r = calificar(_datos_cierre(s), modelo)
    c = round(sum(a.declarado / 100 * a.puntaje for a in r.ambitos), 1)
    filas = []
    for a in r.ambitos:
        for t in a.tareas:
            filas.append([NOMBRES_CORTOS[a.ambito], t.descripcion + (" ★" if t.destaca else ""),
                          t.mecanismo or "—", n(t.puntaje) + "%"])
    out.append(tabla(["Ámbito", "Actividad", "Evidencia", "$p_t$"], filas))
    if s.get("ponderacion") == "igual":
        out.append("Ponderación: escenario E1 (igual peso), porque sólo la gestión tiene horas registradas.")
    else:
        h = {a: _horas_semanales(v) for a, v in s["horas"].items()}
        out.append(_formula_horas(h, {a.ambito: a.declarado for a in r.ambitos}))
    out.append(tabla(["Ámbito", "$w_a$", "$S_a$", "Letra del ámbito"],
                     [[a.nombre, n(a.declarado) + "%", n(a.puntaje) + "%", a.letra] for a in r.ambitos]))
    suma = " + ".join(f"{tex(a.declarado / 100, 3)} \\cdot {tex(a.puntaje)}" for a in r.ambitos)
    out.append(f"$$C = {suma} = {tex(c)}\\%$$")
    out.append(f"**Resultado:** $C = {tex(c)}\\%$ → **{clasificar(c, modelo)}** (escala {escala(c, modelo)}), con "
               "el supuesto neutro $AE = EE = C$.")
    if r.destacados:
        out.append("**Destaca en:** " + "; ".join(d.descripcion for d in r.destacados) + ".")
    obs = [re.sub(r"(\d)\.(\d)", r"\1,\2", o) for o in r.observaciones
           if "jornada" in o or "pertenece" in o or "sin tareas" in o]
    out.append("**Notas:**\n\n" + "\n".join(f"- {x}" for x in s["notas"] + obs))
    sin_carpeta = sum(1 for t in s["tareas"] if t.get("fuente") == "carga_academica")
    return "\n\n".join(out), {"sujeto": s["sujeto"], "jer": s["jerarquia"].capitalize(), "c": c,
                              "l": clasificar(c, modelo), "sin_carpeta": sin_carpeta, "tareas": len(s["tareas"]),
                              "total": sum(_horas_semanales(v) for v in s["horas"].values())}


DOCUMENTOS = {
    "01": ("Reporte e informe de cierre", "—"), "02": ("Reporte e informe de cierre", "Compromiso (incompleto)"),
    "03": ("Reporte e informe de cierre", "—"),
    "04": ("Reporte e informe de cierre", "—"), "05": ("Reporte e informe de cierre", "—"),
    "06": ("Reporte e informe de cierre", "—"), "07": ("Compromiso con horas", "—"),
    "08": ("Compromiso con horas", "Compromiso"), "09": ("Compromiso con horas", "Compromiso"),
}


def seccion_relacion(datos: dict, res_23: list, res_24c: list, res_24k: list) -> str:
    docs = dict(DOCUMENTOS)
    for s in datos["compromisos_2024"]:
        docs.setdefault(s["sujeto"], ("—", "Compromiso" + ("" if s["completo"] else " (incompleto)")))
    for s in datos["cierres_2024"]:
        if not s.get("omitir"):
            docs.setdefault(s["sujeto"], ("—", "Informe de cierre"))
    filas = []
    for suj in sorted(docs):
        d23, d24 = docs[suj]
        ciclo = "Completo en ambos años" if "cierre" in d23 and "cierre" in d24 and "Compromiso" in d24 else (
            "Ambos años, ciclo incompleto" if d23 != "—" and d24 != "—" else "Sólo 2023" if d24 == "—" else "Sólo 2024")
        filas.append([f"Sujeto {suj}", d23, d24, ciclo])
    out = ["## 9. Relación entre 2023 y 2024",
           "Documentos disponibles por sujeto. Un ciclo completo requiere, para cada año, el compromiso con horas y el "
           "informe de cierre con evidencia en la carpeta. No se incluyen los informes de cierre 2024 sin compromiso de "
           "desempeño (sección 8).",
           tabla(["Sujeto", "2023", "2024", "Relación"], filas)]
    r23 = {r["sujeto"]: r for r in res_23}
    r24c = {r["sujeto"]: r for r in res_24c}
    r24k = {r["sujeto"]: r for r in res_24k}
    comp = []
    if "02" in r23:
        comp.append(f"- **Sujeto 02.** En 2023 tuvo $C = {tex(r23['02']['c1'])}\\%$ ({r23['02']['l1']}, E1): "
                    "investigación y gestión sin evidencia. Su compromiso 2024 está incompleto (sólo docencia), así que "
                    "no se puede ver si corrigió esos ámbitos.")
    if False:  # el informe 2024 del sujeto 03 se omite: no tiene compromiso
        comp.append(f"- **Sujeto 03.** En 2023 tuvo $C = {tex(r23['03']['c1'])}\\%$ ({r23['03']['l1']}, E1) con "
                    f"actividades en los 4 ámbitos. En 2024 no se encontró el compromiso y la carga registra sólo docencia "
                    f"(20 h): $C$ = {n(r24c['03']['c_inf'])}% según el informe, pero {n(r24c['03']['c_est'])}% con el "
                    "criterio estricto. El informe 2024 marca como no cumplidas la dirección de memorias y la gestión.")
    for suj in ("08", "09"):
        if suj in r24k and r24k[suj]["w"]:
            s = next(x for x in datos["compromisos_2024"] if x["sujeto"] == suj)
            antes = s["vinculo_2023"]
            despues = r24k[suj]["w"]
            cambios = ", ".join(f"{CORTO[a]} {n(antes.get(a, 0))}% → {n(despues.get(a, 0))}%" for a in ORDEN)
            comp.append(f"- **Sujeto {suj}.** Ponderación por horas 2023 → 2024: {cambios}. "
                        + ("La gestión declarada en 2024 no tiene horas, por eso baja a 0%."
                           if despues.get("gestion", 0) == 0 else ""))
    out += ["### Comparación de los sujetos con registros en ambos años", "\n".join(comp)]
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

    datos["compromisos_2024"].sort(key=lambda x: x["sujeto"])
    datos["cierres_2024"].sort(key=lambda x: x["sujeto"])
    det_24k, res_24k = zip(*[seccion_compromiso_2024(x, modelo) for x in datos["compromisos_2024"]])
    omitidos = [x["sujeto"] for x in datos["cierres_2024"] if x.get("omitir")]
    det_24c, res_24c = zip(*[seccion_cierre_2024(x, modelo) for x in datos["cierres_2024"] if not x.get("omitir")])
    tabla_24k = tabla(["Sujeto", "Completo", "Horas semanales", "$w$ Doc", "$w$ ICI", "$w$ VcM", "$w$ Gest",
                       "Actividades", "Art. 37"],
                      [[f"Sujeto {r['sujeto']}", "Sí" if r["completo"] else "No",
                        n(r["total"]) if r.get("total") else "—"] +
                       [n(r["w"][a]) + "%" if a in r["w"] else "—" for a in ORDEN] +
                       [r["tareas"], r["situacion"] or "—"] for r in res_24k])
    tabla_24c = tabla(["Sujeto", "Jerarquía", "Horas registradas", "Actividades sin evidencia en la carpeta", "$C$", "Letra"],
                      [[f"Sujeto {r['sujeto']}", r["jer"], n(r["total"]), f"{r['sin_carpeta']} de {r['tareas']}",
                        n(r["c"]) + "%", r["l"]] for r in res_24c])

    partes = [
        "---\ntitle: \"Ejercicio de calificación SEJA con los registros 2023 y 2024\"\n"
        "subtitle: \"Informe extendido · Oficina de Evaluación de Desempeño Académico\"\nlang: es\n---",
        "## 1. Resumen ejecutivo",
        f"Se aplicó el modelo de calificación SEJA a los registros 2023 y 2024 de **25 sujetos**:\n\n"
        f"- **2023:** sujetos 01 a 06, con reporte e informe de cierre; sujetos 07 a 09, con compromiso con horas.\n"
        f"- **2024:** {len(res_24k)} compromisos (sujetos 02, 08, 09 y 10 a 18) y {len(res_24c)} informes de cierre "
        f"con compromiso (sujetos {_lista([r['sujeto'] for r in res_24c])}); se omiten {len(omitidos)} informes de cierre "
        f"sin compromiso de desempeño.\n"
        f"- **En ambos años:** sujetos 02, 08 y 09.",
        "### Resultados 2023",
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
        "### Resultados 2024",
        f"- **Compromisos 2024.** {sum(1 for r in res_24k if r['w'])} de {len(res_24k)} permiten calcular la ponderación "
        "por horas. Los demás no tienen resumen de horas o el formulario quedó incompleto. El formulario 2024 no tiene "
        "casilla de gestión, y las horas de gestión aparecen en observaciones o mezcladas con docencia.",
        "- **Informes de cierre 2024.** La evidencia válida es la de la carpeta individual (Drive). La información "
        "que la Oficina recoge de la carga académica es un trabajo adicional y no acredita cumplimiento: esas actividades "
        "valen 0%, y quien no provee evidencias obtiene la calificación mínima. Con ese criterio, "
        + _lista([f"el sujeto {r['sujeto']} obtiene {n(r['c'])}% ({r['l']})" for r in res_24c]) + ". "
        f"Se omiten los informes de cierre de {len(omitidos)} sujetos sin compromiso de desempeño, porque la falta "
        "puede deberse a que el nivel central no entregó toda la información a la Oficina para la inducción.",
        "- **Carga fuera de rango.** Hay docencias fuera del rango del reglamento (86,7% en un compromiso y 19,5% en un "
        "cierre) y horas declaradas fuera de los resúmenes.",
        "### Conclusión",
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
        "- **Formularios de Compromiso de Desempeño 2024** (respuestas en QuestionPro) e **Informes de Cierre 2024**.",
        "- **Normativa de referencia:** propuesta de Reglamento de Carrera Académica, Síntesis SEJA (agosto 2026) y "
        "Jornada Modelo de Evaluación SEJA 2024.",
        "Las personas se identifican como *sujeto 01, 02…*. Las asignaturas se numeran por sujeto (*asignatura 1, "
        "asignatura 2…*). Se omiten los nombres de personas, jefaturas, departamentos, proyectos, eventos y "
        "comisiones. Tampoco se incluyen los RUT, correos ni direcciones IP de los formularios, ni los nombres de "
        "terceros (coinvestigadores, estudiantes, autores) que aparecen en ellos. Las personas presentes en ambos años "
        "conservan su código (sujetos 02, 03, 08 y 09).",
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
        "## 7. Compromisos 2024",
        "Para cada compromiso se calcula la ponderación por horas (fórmula 3.3) y se deja el **plan de evaluación**: "
        "qué etapa o meta se comprometió en cada actividad y con qué evidencia se evaluará al cierre. El formulario 2024 "
        "no registra jerarquía; se informa cuando se conoce por otro documento.",
        tabla_24k,
        *det_24k,
        "## 8. Informes de cierre 2024",
        "**Criterio de evidencia.** Es obligatorio subir la evidencia a la carpeta individual (Drive). Cuando la Oficina "
        "recoge información de la carga académica, se trata de un trabajo adicional que no acredita cumplimiento: esas "
        "actividades obtienen $p_t = 0$, y la persona que no provee evidencias obtiene la calificación mínima. La carga "
        "académica sí se usa para las horas $h_a$ de la ponderación (fórmula 3.3).",
        "**Sujetos omitidos.** Se omiten los informes de cierre de los sujetos " + _lista(omitidos) + ", que no tienen "
        "compromiso de desempeño: la falta puede deberse a un error del nivel central, que no entregó toda la "
        "información a la Oficina para realizar la inducción.",
        tabla_24c,
        *det_24c,
        seccion_relacion(datos, resumenes, list(res_24c), list(res_24k)),
        "## 10. Hallazgos transversales",
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
            "7. **El formulario 2024 no permite ponderar.** No pide jerarquía, perfil ni jornada, no tiene casilla de "
            "gestión y su resumen acepta «horas o porcentaje». Varios formularios quedaron incompletos (sin resumen, sin "
            "VcM o sólo con docencia), y las personas anotan horas en observaciones.",
            "8. **Los informes de cierre 2024 asignan 100% sin evidencia.** En la mayoría el 100% proviene de la carga "
            "académica de la Dirección de Docencia y la carpeta individual no tiene evidencias. Con el criterio de "
            "evidencia en la carpeta esas actividades valen 0%. Además, seis informes corresponden a personas sin "
            "compromiso de desempeño, y uno marca funciones de titular para un asociado.",
            "9. **Cargas académicas sin control.** Una docencia de 86,7% con una persona que deja constancia de no poder "
            "comprometer investigación ni VcM, y horas de gestión que quedan fuera de los resúmenes.",
            "10. **La normativa cambia.** Los informes 2023 revisan funciones de la Res. 320/93. La propuesta de "
            "Reglamento de Carrera Académica define funciones por jerarquía y perfil, con carga docente esperada, lo que "
            "deja más funciones pendientes en varios sujetos (por ejemplo, formación de académicos, redes y formación "
            "continua)."]),
        "## 11. Recomendaciones",
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
            "institucional.",
            "7. Recordar que la **carpeta individual (Drive) es obligatoria**: sin evidencia, la actividad vale 0% y la "
            "calificación es la mínima. La carga académica sirve para las horas ($h_a$), no para el cumplimiento ($p_t$).",
            "8. Asegurar con el nivel central que la Oficina reciba la nómina completa para la **inducción**, de modo que "
            "nadie quede sin compromiso de desempeño.",
            "9. Definir para cada **comisión de estudios** su duración, sus condiciones y los compromisos asociados que se "
            "evaluarán.",
            "10. Validar al cerrar el compromiso que la suma de horas esté dentro de la jornada y que la docencia esté en el "
            "rango de la jerarquía y el perfil; alertar a la jefatura si no.",
            "11. Completar los documentos faltantes para cerrar la relación entre 2023 y 2024 (sección 9)."]),
        "## Anexo. Parámetros del modelo",
        tabla(["Parámetro", "Valor"], [
            ["Autoevaluación / evaluación de estudiantes", "10% / 10%"],
            ["Compromiso (ámbitos)", "80% (90% si está eximido/a de docencia)"],
            ["Tope por tarea con excedente validado", "120%"],
            ["Etapa evidenciada anterior a la comprometida", "50%"],
            ["Suspensión (art. 37)", "Ausencia justificada de más de 5 meses continuos"],
            ["Comisión de estudios", "Se evalúan los compromisos asociados; si no los hay, regla general de suspensión"],
            ["Evidencia válida", "Carpeta individual (Drive); la carga académica no acredita cumplimiento"],
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
