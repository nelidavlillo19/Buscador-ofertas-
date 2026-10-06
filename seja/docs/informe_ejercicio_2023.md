---
title: "Ejercicio de calificación SEJA con los registros 2023"
subtitle: "Informe extendido · Oficina de Evaluación de Desempeño Académico"
lang: es
---

## 1. Resumen ejecutivo

Se aplicó el modelo de calificación SEJA a los registros 2023 de **nueve sujetos**. Seis de ellos (sujetos 01 a 06) tienen reporte del compromiso e informe de cierre con el cumplimiento de cada actividad. Los otros tres (sujetos 07 a 09) tienen formulario de compromiso con horas, pero no informe de cierre.

- **Resultados (escenario E1, igual peso por ámbito):** 1 en A, 3 en B, 1 en C, 1 en D. La letra cambia según cómo se pondera en los sujetos 01 y 06. Los informes 2023 no asignaban calificación: sólo marcaban 100% o 0% por actividad.

- **La ponderación no se puede calcular con los registros 2023.** Los reportes e informes no registran horas por ámbito; afirman qué ámbito es «mayoría» sin datos que lo respalden. Por eso el ejercicio usa dos escenarios de ponderación, y en los casos con actividades sin evidencia la letra depende del escenario.

- **El modelo distingue lo que el informe 2023 no distinguía:** el excedente (más ponencias que las comprometidas), el avance más allá de la etapa comprometida (proyectos cerrados, artículos publicados) y las actividades comprometidas sin evidencia, que hoy bajan el cumplimiento del ámbito.

- **Los registros tienen inconsistencias.** Hay resúmenes que contradicen su propia tabla, una jerarquía que cambia entre el reporte y el informe, actividades declaradas que no se evalúan al cierre, actividades en el ámbito equivocado y horas que se registran de tres formas distintas.

- **Recomendación principal.** Registrar en UCampus las horas semanales por ámbito, cada actividad con su subcategoría y su etapa comprometida, y la autoevaluación y la evaluación de estudiantes. Con eso la calificación se calcula automáticamente con las fórmulas de la sección 3.

## 2. Fuentes y anonimización

- **Reportes de Compromiso de Desempeño 2023** (octubre 2023): identificación, resumen, actividades por dimensión y mecanismo de evidencia.

- **Informes de Cierre 2023** (marzo 2024): etapa comprometida y evidenciada, mecanismo, % de cumplimiento por actividad, funciones de la Res. 320/93, y oportunidades y fortalezas.

- **Formularios de Compromiso de Desempeño 2023** con horas por actividad, y el formulario e instructivo 2024 de UCampus.

- **Normativa de referencia:** propuesta de Reglamento de Carrera Académica, Síntesis SEJA (agosto 2026) y Jornada Modelo de Evaluación SEJA 2024.

Las personas se identifican como *sujeto 01, 02…*. Las asignaturas se numeran por sujeto (*asignatura 1, asignatura 2…*). Se omiten los nombres de personas, jefaturas, departamentos, proyectos, eventos y comisiones.

## 3. Modelo de calificación y fórmulas

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
  correspondientes.

## 4. Cómo se corrió el ejercicio

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
   ponderación por horas (fórmula 3.3) y se revisan los registros.

## 5. Resultados de los sujetos con informe de cierre (01 a 06)

| Sujeto | Jerarquía | $S$ Doc | $S$ ICI | $S$ VcM | $S$ Gest | $C$ E1 (letra) | $C$ E2 (letra) | Tareas sin evidencia | Destacados | Funciones pendientes |
|---|---|---|---|---|---|---|---|---|---|---|
| Sujeto 01 | Asociado | 100,0% | 100,0% | 100,0% | 33,3% | 83,3% (B) | 73,3% (C) | 2 de 15 | 1 | 3 |
| Sujeto 02 | Titular | 100,0% | 0,0% | — | 0,0% | 33,3% (D) | 25,0% (D) | 6 de 9 | 0 | 9 |
| Sujeto 03 | Asociado | 75,0% | 100,0% | 0,0% | 100,0% | 68,8% (C) | 70,0% (C) | 4 de 11 | 2 | 5 |
| Sujeto 04 | Titular | 100,0% | 66,7% | 100,0% | 66,7% | 83,3% (B) | 80,0% (B) | 2 de 11 | 0 | 3 |
| Sujeto 05 | Titular | 100,0% | 66,7% | 110,0% | 100,0% | 94,2% (A) | 90,6% (A) | 1 de 12 | 3 | 5 |
| Sujeto 06 | Asociado | 100,0% | 100,0% | 100,0% | 50,0% | 87,5% (B) | 91,7% (A) | 1 de 6 | 2 | 5 |

$S$ es el cumplimiento de cada ámbito y $C$ el cumplimiento del compromiso. «—» indica que no hay actividades en ese ámbito. Las funciones pendientes se cuentan según el Reglamento de Carrera Académica, con el perfil supuesto.

### Sujeto 01

**Jerarquía:** Asociado · **Perfil supuesto:** vinculador · **Jornada:** completa · **Mayoría de horas según el reporte:** Gestión Académica

| Ámbito | Actividad | Comprometido | Evidenciado | Mecanismo | $p_t$ |
|---|---|---|---|---|---|
| Docencia | Asignaturas 1 y 2 (pregrado) | Ejecución | Finalizada | Registro UCampus | 100,0% |
| Docencia | Asignatura 3 (investigación de pregrado) | Ejecución | Finalizada | Registro UCampus | 100,0% |
| Docencia | Asignaturas 4 y 5 (investigación de postgrado) | Ejecución | Finalizada | Registro UCampus | 100,0% |
| Investigación, Creación e Innovación | Proyecto con financiamiento externo (ANID) | Ejecución | Ejecución | Carta de aprobación | 100,0% |
| Investigación, Creación e Innovación | Proyecto de creación con financiamiento externo | Ejecución | Ejecución | Carta de aprobación | 100,0% |
| Investigación, Creación e Innovación | Proyecto con financiamiento interno | Ejecución | Ejecución | Carta compromiso | 100,0% |
| Investigación, Creación e Innovación | 3 artículos (2 enviados y 1 publicado) ★ | Enviada | Publicada | Certificados y cartas | 100,0% |
| Vinculación con el Medio y Extensión | 1 coloquio | Ejecución | Finalizada | Afiches y programas | 100,0% |
| Vinculación con el Medio y Extensión | 2 seminarios | Ejecución | Finalizada | Afiches y programas | 100,0% |
| Vinculación con el Medio y Extensión | 2 exposiciones | Ejecución | Finalizada | Afiches y programas | 100,0% |
| Vinculación con el Medio y Extensión | 1 actividad de difusión | Ejecución | Finalizada | Afiches y programas | 100,0% |
| Vinculación con el Medio y Extensión | 1 asesoría externa | Ejecución | Finalizada | Notificación por correo | 100,0% |
| Gestión Académica | Coordinación de biblioteca de la unidad | Ejecución | Finalizada | Carga académica | 100,0% |
| Gestión Académica | Comité ejecutivo de magíster | Ejecución | Sin evidencia | Informe del magíster | 0,0% |
| Gestión Académica | Consejo académico del departamento | Ejecución | Sin evidencia | Informe de la carrera | 0,0% |

| Ámbito | Tareas | $S_a$ | Letra del ámbito | $w_a$ (E1) | $w_a$ (E2) |
|---|---|---|---|---|---|
| Docencia | 3 | 100,0% | A | 0,250 | 0,200 |
| Investigación, Creación e Innovación | 4 | 100,0% | A | 0,250 | 0,200 |
| Vinculación con el Medio y Extensión | 5 | 100,0% | A | 0,250 | 0,200 |
| Gestión Académica | 3 | 33,3% | D | 0,250 | 0,400 |

$$C_{E1} = 0{,}250 \cdot 100{,}0 + 0{,}250 \cdot 100{,}0 + 0{,}250 \cdot 100{,}0 + 0{,}250 \cdot 33{,}3 = 83{,}3\%$$

$$C_{E2} = 0{,}200 \cdot 100{,}0 + 0{,}200 \cdot 100{,}0 + 0{,}200 \cdot 100{,}0 + 0{,}400 \cdot 33{,}3 = 73{,}3\%$$

| Escenario | $C$ | $F$ (AE = EE = C) | Letra | Escala | $F_{\max}$ (AE = EE = 100) | Letra con $F_{\max}$ |
|---|---|---|---|---|---|---|
| E1 igual peso | 83,3% | 83,3% | B | 6 | 86,6% | B |
| E2 según reporte | 73,3% | 73,3% | C | 5 | 78,6% | B |

**Destaca en** (registro para reconocimiento institucional): 3 artículos (2 enviados y 1 publicado): avanzó más allá de lo comprometido (Enviada → Publicada).

**Funciones del Reglamento de Carrera Académica, Asociado, perfil vinculador (art. 24):** 6 cumplidas de 9. Pendientes: Colaborar en la formación y desarrollo de académicos/as de jerarquía menor o equivalente; Participar en redes nacionales e internacionales; Acreditar formación continua.

**Informe de cierre 2023 (Res. 320/93):** Todas las funciones de la Res. 320/93 cumplidas (5 de 5). Gestión: 2 de 3 actividades sin evidencia.

**Hallazgos en los registros:**

- El resumen del reporte declara funciones de docencia, investigación y gestión, pero la tabla del mismo reporte incluye 6 iniciativas de VcM y 1 asesoría externa.
- El reporte indica que la gestión es mayoritaria en horas, aunque el compromiso declara 3 actividades de gestión frente a 5 de docencia y 7 de VcM: sin horas no es verificable.

### Sujeto 02

**Jerarquía:** Titular · **Perfil supuesto:** investigador · **Jornada:** completa · **Mayoría de horas según el reporte:** Investigación, Creación e Innovación

| Ámbito | Actividad | Comprometido | Evidenciado | Mecanismo | $p_t$ |
|---|---|---|---|---|---|
| Docencia | Asignaturas 1 y 2 (pregrado) | Ejecución | Finalizada | Registro UCampus | 100,0% |
| Docencia | 9 trabajos de memoria de título | Ejecución | Finalizada | Registro UCampus | 100,0% |
| Docencia | Asignaturas 3 a 12 (postgrado) | Ejecución | Finalizada | Registro UCampus | 100,0% |
| Investigación, Creación e Innovación | Proyecto con financiamiento externo (ANID) | Ejecución | Sin evidencia | Constancia de la entidad (postulación, adjudicación o cierre) y evaluación de la Dirección de Investigación | 0,0% |
| Investigación, Creación e Innovación | Proyecto con financiamiento interno | Ejecución | Sin evidencia | Constancia de la entidad (postulación, adjudicación o cierre) y evaluación de la Dirección de Investigación | 0,0% |
| Investigación, Creación e Innovación | 1 publicación | Enviada | Sin evidencia | Constancia de la revista, indexación, factor de impacto y copia de la publicación | 0,0% |
| Gestión Académica | Coordinación de programa de magíster | Ejecución | Sin evidencia | — | 0,0% |
| Gestión Académica | Comisión de jerarquización | Ejecución | Sin evidencia | — | 0,0% |
| Gestión Académica | Consejo de departamento | Ejecución | Sin evidencia | — | 0,0% |

| Ámbito | Tareas | $S_a$ | Letra del ámbito | $w_a$ (E1) | $w_a$ (E2) |
|---|---|---|---|---|---|
| Docencia | 3 | 100,0% | A | 0,333 | 0,250 |
| Investigación, Creación e Innovación | 3 | 0,0% | D | 0,333 | 0,500 |
| Gestión Académica | 3 | 0,0% | D | 0,333 | 0,250 |

$$C_{E1} = 0{,}333 \cdot 100{,}0 + 0{,}333 \cdot 0{,}0 + 0{,}333 \cdot 0{,}0 = 33{,}3\%$$

$$C_{E2} = 0{,}250 \cdot 100{,}0 + 0{,}500 \cdot 0{,}0 + 0{,}250 \cdot 0{,}0 = 25{,}0\%$$

| Escenario | $C$ | $F$ (AE = EE = C) | Letra | Escala | $F_{\max}$ (AE = EE = 100) | Letra con $F_{\max}$ |
|---|---|---|---|---|---|---|
| E1 igual peso | 33,3% | 33,3% | D | 1 | 46,6% | D |
| E2 según reporte | 25,0% | 25,0% | D | 1 | 40,0% | D |

**Funciones del Reglamento de Carrera Académica, Titular, perfil investigador (art. 28):** 2 cumplidas de 12. Pendientes: Liderar actividades para la formación y desarrollo de académicos/as de jerarquía menor; Liderar proyectos de investigación, innovación o creación competitivos; Postular a fondos de proyectos con financiamiento externo; Integrar núcleos o claustros de postgrado (estándares CNA); Publicar como autor/a principal resultados de investigación o difundir obra; Presentar trabajos en eventos a nivel internacional; Participar en redes a nivel internacional; Acreditar formación continua; Realizar tareas de coordinación en la gestión académica-administrativa.

**Informe de cierre 2023 (Res. 320/93):** 3 de 7 funciones de la Res. 320/93 cumplidas. Investigación y gestión: ninguna actividad evidenciada. El texto del informe afirma que las actividades declaradas son las exigidas para la jerarquía.

**Hallazgos en los registros:**

- El resumen del reporte menciona vinculación con el medio, pero no se declaran actividades de VcM en la tabla ni en el informe.
- El reporte señala 9 actividades curriculares y práctica; el informe de cierre evalúa 2 de pregrado, 9 memorias y 10 de postgrado (21).
- El informe concluye que las actividades son las exigidas para la jerarquía aunque marca 4 funciones como no cumplidas.

### Sujeto 03

**Jerarquía:** Asociado · **Perfil supuesto:** vinculador · **Jornada:** completa · **Mayoría de horas según el reporte:** Docencia

| Ámbito | Actividad | Comprometido | Evidenciado | Mecanismo | $p_t$ |
|---|---|---|---|---|---|
| Docencia | Asignaturas 1 a 7 (pregrado) | Ejecución | Finalizada | Registro UCampus | 100,0% |
| Docencia | 1 actividad de memorias | Ejecución | Finalizada | Registro UCampus | 100,0% |
| Docencia | Asignaturas 8 a 10 (investigación de postgrado) | Ejecución | Finalizada | Registro UCampus | 100,0% |
| Docencia | Apoyo a la formación académica (perfeccionamiento) | Ejecución | Sin evidencia | — | 0,0% |
| Investigación, Creación e Innovación | Proyecto con financiamiento interno ★ | Postulación | Adjudicación | Carta | 100,0% |
| Investigación, Creación e Innovación | Postulación a proyecto con financiamiento externo (ANID) | Postulación | Postulación | Carta de recepción | 100,0% |
| Investigación, Creación e Innovación | 1 artículo ★ | En preparación | Enviada | Carta | 100,0% |
| Vinculación con el Medio y Extensión | 1 proyecto de extensión | Ejecución | Sin evidencia | Constancia (postulación, adjudicación, cierre), pauta y reporte de la Dirección de VcM | 0,0% |
| Vinculación con el Medio y Extensión | 1 ponencia | Ejecución | Sin evidencia | Certificado de la entidad organizadora (nombre, rol, fecha, lugar y organización) | 0,0% |
| Vinculación con el Medio y Extensión | 1 asesoría externa | Ejecución | Sin evidencia | — | 0,0% |
| Gestión Académica | Coordinación de unidad académica | Ejecución | Ejecución | Constancia | 100,0% |

| Ámbito | Tareas | $S_a$ | Letra del ámbito | $w_a$ (E1) | $w_a$ (E2) |
|---|---|---|---|---|---|
| Docencia | 4 | 75,0% | B | 0,250 | 0,400 |
| Investigación, Creación e Innovación | 3 | 100,0% | A | 0,250 | 0,200 |
| Vinculación con el Medio y Extensión | 3 | 0,0% | D | 0,250 | 0,200 |
| Gestión Académica | 1 | 100,0% | A | 0,250 | 0,200 |

$$C_{E1} = 0{,}250 \cdot 75{,}0 + 0{,}250 \cdot 100{,}0 + 0{,}250 \cdot 0{,}0 + 0{,}250 \cdot 100{,}0 = 68{,}8\%$$

$$C_{E2} = 0{,}400 \cdot 75{,}0 + 0{,}200 \cdot 100{,}0 + 0{,}200 \cdot 0{,}0 + 0{,}200 \cdot 100{,}0 = 70{,}0\%$$

| Escenario | $C$ | $F$ (AE = EE = C) | Letra | Escala | $F_{\max}$ (AE = EE = 100) | Letra con $F_{\max}$ |
|---|---|---|---|---|---|---|
| E1 igual peso | 68,8% | 68,8% | C | 4 | 75,0% | B |
| E2 según reporte | 70,0% | 70,0% | C | 5 | 76,0% | B |

**Destaca en** (registro para reconocimiento institucional): Proyecto con financiamiento interno: avanzó más allá de lo comprometido (Postulación → Adjudicación); 1 artículo: avanzó más allá de lo comprometido (En preparación → Enviada).

**Funciones del Reglamento de Carrera Académica, Asociado, perfil vinculador (art. 24):** 4 cumplidas de 9. Pendientes: Colaborar en la formación y desarrollo de académicos/as de jerarquía menor o equivalente; Liderar iniciativas, proyectos o programas de VcM competitivos o de relevancia regional o nacional; Exponer, presentar o difundir actividades académicas y de VcM; Participar en redes nacionales e internacionales; Acreditar formación continua.

**Informe de cierre 2023 (Res. 320/93):** 3 de 5 funciones de la Res. 320/93 cumplidas. VcM y perfeccionamiento sin evidencia.

**Hallazgos en los registros:**

- El reporte declara una «tenencia» en VcM que no aparece en el informe de cierre; el informe evalúa una ponencia que el reporte no menciona.
- La «colaboración con el departamento» declarada en gestión no se evalúa en el informe de cierre.
- El perfeccionamiento se registra como un área aparte; en SEJA corresponde a formación continua (docencia).

### Sujeto 04

**Jerarquía:** Titular · **Perfil supuesto:** investigador · **Jornada:** completa · **Mayoría de horas según el reporte:** Investigación, Creación e Innovación

| Ámbito | Actividad | Comprometido | Evidenciado | Mecanismo | $p_t$ |
|---|---|---|---|---|---|
| Docencia | Asignaturas 1 a 3 (pregrado) | Ejecución | Finalizada | Registro UCampus | 100,0% |
| Docencia | 3 actividades de memorias | Ejecución | Finalizada | Registro UCampus | 100,0% |
| Docencia | Asignatura 4 (postgrado) | Ejecución | Finalizada | Registro UCampus | 100,0% |
| Docencia | Curso de formación de la unidad de desarrollo académico | Ejecución | Finalizada | Constancia | 100,0% |
| Investigación, Creación e Innovación | 2 proyectos en ejecución | Ejecución | Ejecución | Constancia y carta | 100,0% |
| Investigación, Creación e Innovación | Postulación a proyecto con financiamiento externo (ANID) | Postulación | Sin evidencia | — | 0,0% |
| Investigación, Creación e Innovación | 3 artículos | Publicada | Publicada | Documento | 100,0% |
| Vinculación con el Medio y Extensión | 2 ponencias | Ejecución | Finalizada | Certificado | 100,0% |
| Gestión Académica | Claustro académico de magíster | Ejecución | Ejecución | Constancia | 100,0% |
| Gestión Académica | Integrante de núcleo de investigación | Ejecución | Sin evidencia | — | 0,0% |
| Gestión Académica | Claustro académico de doctorado | Ejecución | Ejecución | Constancia | 100,0% |

| Ámbito | Tareas | $S_a$ | Letra del ámbito | $w_a$ (E1) | $w_a$ (E2) |
|---|---|---|---|---|---|
| Docencia | 4 | 100,0% | A | 0,250 | 0,200 |
| Investigación, Creación e Innovación | 3 | 66,7% | C | 0,250 | 0,400 |
| Vinculación con el Medio y Extensión | 1 | 100,0% | A | 0,250 | 0,200 |
| Gestión Académica | 3 | 66,7% | C | 0,250 | 0,200 |

$$C_{E1} = 0{,}250 \cdot 100{,}0 + 0{,}250 \cdot 66{,}7 + 0{,}250 \cdot 100{,}0 + 0{,}250 \cdot 66{,}7 = 83{,}3\%$$

$$C_{E2} = 0{,}200 \cdot 100{,}0 + 0{,}400 \cdot 66{,}7 + 0{,}200 \cdot 100{,}0 + 0{,}200 \cdot 66{,}7 = 80{,}0\%$$

| Escenario | $C$ | $F$ (AE = EE = C) | Letra | Escala | $F_{\max}$ (AE = EE = 100) | Letra con $F_{\max}$ |
|---|---|---|---|---|---|---|
| E1 igual peso | 83,3% | 83,3% | B | 6 | 86,6% | B |
| E2 según reporte | 80,0% | 80,0% | B | 6 | 84,0% | B |

**Funciones del Reglamento de Carrera Académica, Titular, perfil investigador (art. 28):** 9 cumplidas de 12. Pendientes: Liderar actividades para la formación y desarrollo de académicos/as de jerarquía menor; Integrar núcleos o claustros de postgrado (estándares CNA); Participar en redes a nivel internacional.

**Informe de cierre 2023 (Res. 320/93):** 6 de 7 funciones de la Res. 320/93 cumplidas. Pendiente: colaborar en planes de perfeccionamiento de ayudantes y académicos de jerarquía menor.

**Hallazgos en los registros:**

- Los claustros de magíster y doctorado y el núcleo de investigación se registraron en gestión; en el catálogo SEJA los claustros de postgrado corresponden a investigación.
- Las ponencias se registran en VcM; el catálogo SEJA las admite en investigación (divulgación) o en VcM (presentaciones).

### Sujeto 05

**Jerarquía:** Titular (el reporte de octubre registra Asociado) · **Perfil supuesto:** investigador · **Jornada:** completa · **Mayoría de horas según el reporte:** Investigación, Creación e Innovación, Gestión Académica

| Ámbito | Actividad | Comprometido | Evidenciado | Mecanismo | $p_t$ |
|---|---|---|---|---|---|
| Docencia | Asignaturas 1 y 2 (pregrado) | Ejecución | Finalizada | Registro UCampus | 100,0% |
| Docencia | 12 actividades de memorias | Ejecución | Finalizada | Registro UCampus | 100,0% |
| Docencia | Asignaturas 3 a 5 (postgrado) | Ejecución | Finalizada | Registro UCampus | 100,0% |
| Investigación, Creación e Innovación | Proyecto con financiamiento interno ★ | Ejecución | Cierre | Informe | 100,0% |
| Investigación, Creación e Innovación | Proyecto con financiamiento externo ★ | Ejecución | Cierre | Informe | 100,0% |
| Investigación, Creación e Innovación | 1 artículo | Enviada | Sin evidencia | Constancia de la revista, indexación, factor de impacto y copia de la publicación | 0,0% |
| Vinculación con el Medio y Extensión | Proyecto de convenio marco | Ejecución | Finalizada | Informe | 100,0% |
| Vinculación con el Medio y Extensión | Ponencias (2 comprometidas, 3 realizadas) ★ | 2 | 3 | Afiche | 120,0% |
| Gestión Académica | Coordinación de un observatorio | Ejecución | Finalizada | Constancia | 100,0% |
| Gestión Académica | Creación de un programa de magíster | Ejecución | Finalizada | Constancia | 100,0% |
| Gestión Académica | Comité de autoevaluación de magíster | Ejecución | Finalizada | Constancia | 100,0% |
| Gestión Académica | Comité académico de núcleo de magíster | Ejecución | Finalizada | Constancia | 100,0% |

| Ámbito | Tareas | $S_a$ | Letra del ámbito | $w_a$ (E1) | $w_a$ (E2) |
|---|---|---|---|---|---|
| Docencia | 3 | 100,0% | A | 0,250 | 0,167 |
| Investigación, Creación e Innovación | 3 | 66,7% | C | 0,250 | 0,333 |
| Vinculación con el Medio y Extensión | 2 | 110,0% | A+ | 0,250 | 0,167 |
| Gestión Académica | 4 | 100,0% | A | 0,250 | 0,333 |

$$C_{E1} = 0{,}250 \cdot 100{,}0 + 0{,}250 \cdot 66{,}7 + 0{,}250 \cdot 110{,}0 + 0{,}250 \cdot 100{,}0 = 94{,}2\%$$

$$C_{E2} = 0{,}167 \cdot 100{,}0 + 0{,}333 \cdot 66{,}7 + 0{,}167 \cdot 110{,}0 + 0{,}333 \cdot 100{,}0 = 90{,}6\%$$

| Escenario | $C$ | $F$ (AE = EE = C) | Letra | Escala | $F_{\max}$ (AE = EE = 100) | Letra con $F_{\max}$ |
|---|---|---|---|---|---|---|
| E1 igual peso | 94,2% | 94,2% | A | 7 | 95,4% | A |
| E2 según reporte | 90,6% | 90,6% | A | 7 | 92,5% | A |

**Destaca en** (registro para reconocimiento institucional): Proyecto con financiamiento interno: avanzó más allá de lo comprometido (Ejecución → Cierre); Proyecto con financiamiento externo: avanzó más allá de lo comprometido (Ejecución → Cierre); Ponencias (2 comprometidas, 3 realizadas): 150% de lo comprometido.

**Funciones del Reglamento de Carrera Académica, Titular, perfil investigador (art. 28):** 7 cumplidas de 12. Pendientes: Liderar actividades para la formación y desarrollo de académicos/as de jerarquía menor; Integrar núcleos o claustros de postgrado (estándares CNA); Publicar como autor/a principal resultados de investigación o difundir obra; Participar en redes a nivel internacional; Acreditar formación continua.

**Informe de cierre 2023 (Res. 320/93):** 6 de 7 funciones de la Res. 320/93 cumplidas. Pendiente: colaborar en planes de perfeccionamiento de ayudantes y académicos de jerarquía menor.

**Hallazgos en los registros:**

- El reporte de octubre registra la jerarquía Asociado y el informe de cierre registra Titular.
- El reporte declara 2 ponencias y el informe evidencia 3: es un excedente que el informe 2023 no distingue.

### Sujeto 06

**Jerarquía:** Asociado · **Perfil supuesto:** investigador · **Jornada:** completa · **Mayoría de horas según el reporte:** Docencia, Investigación, Creación e Innovación

| Ámbito | Actividad | Comprometido | Evidenciado | Mecanismo | $p_t$ |
|---|---|---|---|---|---|
| Docencia | Asignaturas 1 a 7 (postgrado) | Ejecución | Finalizada | Registro UCampus | 100,0% |
| Investigación, Creación e Innovación | Proyecto de postdoctorado ★ | Ejecución | Cierre | Artículo | 100,0% |
| Investigación, Creación e Innovación | 3 publicaciones ★ | En preparación | Publicada | Artículo | 100,0% |
| Vinculación con el Medio y Extensión | 3 ponencias | Ejecución | Finalizada | Certificados | 100,0% |
| Gestión Académica | Presidencia de comité científico de conferencia internacional | Ejecución | Finalizada | Certificado de participación | 100,0% |
| Gestión Académica | Comisión de investigación | Ejecución | Sin evidencia | — | 0,0% |

| Ámbito | Tareas | $S_a$ | Letra del ámbito | $w_a$ (E1) | $w_a$ (E2) |
|---|---|---|---|---|---|
| Docencia | 1 | 100,0% | A | 0,250 | 0,333 |
| Investigación, Creación e Innovación | 2 | 100,0% | A | 0,250 | 0,333 |
| Vinculación con el Medio y Extensión | 1 | 100,0% | A | 0,250 | 0,167 |
| Gestión Académica | 2 | 50,0% | D | 0,250 | 0,167 |

$$C_{E1} = 0{,}250 \cdot 100{,}0 + 0{,}250 \cdot 100{,}0 + 0{,}250 \cdot 100{,}0 + 0{,}250 \cdot 50{,}0 = 87{,}5\%$$

$$C_{E2} = 0{,}333 \cdot 100{,}0 + 0{,}333 \cdot 100{,}0 + 0{,}167 \cdot 100{,}0 + 0{,}167 \cdot 50{,}0 = 91{,}7\%$$

| Escenario | $C$ | $F$ (AE = EE = C) | Letra | Escala | $F_{\max}$ (AE = EE = 100) | Letra con $F_{\max}$ |
|---|---|---|---|---|---|---|
| E1 igual peso | 87,5% | 87,5% | B | 6 | 90,0% | A |
| E2 según reporte | 91,7% | 91,7% | A | 7 | 93,4% | A |

**Destaca en** (registro para reconocimiento institucional): Proyecto de postdoctorado: avanzó más allá de lo comprometido (Ejecución → Cierre); 3 publicaciones: avanzó más allá de lo comprometido (En preparación → Publicada).

**Funciones del Reglamento de Carrera Académica, Asociado, perfil investigador (art. 23):** 6 cumplidas de 11. Pendientes: Dirigir trabajos conducentes a título profesional y/o grados académicos de pre y postgrado; Colaborar en la formación y desarrollo de académicos/as de jerarquía menor o equivalente; Participar en redes nacionales e internacionales; Formar parte de equipos de investigación interdisciplinarios o multidisciplinarios; Acreditar formación continua.

**Informe de cierre 2023 (Res. 320/93):** 5 de 5 funciones de la Res. 320/93 cumplidas. Gestión: 1 de 2 actividades sin evidencia.

**Hallazgos en los registros:**

- El reporte declara dirección de trabajos de tesis de postgrado; el informe de cierre no la evalúa (no se sabe si se cumplió).
- La presidencia de un comité científico internacional es una actividad de redes o VcM más que de gestión académica.

## 6. Ponderación por horas (sujetos 07 a 09)

Se compara el % que resulta de las horas tal como se declararon con el % que resulta de las horas ordenadas: semanales, promediando semestres, y con cada actividad en el ámbito que le corresponde según el catálogo. $\omega_a = 0{,}8\,w_a$ es el peso efectivo del ámbito en la calificación final.

### Sujeto 07

**Jerarquía:** Asistente · **Perfil supuesto:** vinculador · **Jornada:** completa

- **Docencia:** Asignatura 1 (3 h) y talleres de práctica: asignaturas 2 y 3 (3 h y 1,5 h), en cada semestre
- **Gestión Académica:** Unidad de gestión curricular (1,5 h), reunión de departamento (1,5 h), coordinación de prácticas (22 h)
- **Vinculación con el Medio y Extensión:** Coordinación de jornadas nacionales de la disciplina (2 h, declarada en gestión); 2 capacitaciones a instituciones externas (sin horas)

| Ámbito | Horas declaradas | % declarado | $h_a$ ordenadas | $w_a$ | $\omega_a$ |
|---|---|---|---|---|---|
| Docencia | 15,0 | 35,7% | 7,5 | 21,7% | 17,4% |
| Vinculación con el Medio y Extensión | 0,0 | 0,0% | 2,0 | 5,8% | 4,6% |
| Gestión Académica | 27,0 | 64,3% | 25,0 | 72,5% | 58,0% |

$$\sum_b h_b = 7{,}5 + 2{,}0 + 25{,}0 = 34{,}5 \text{ h semanales}$$

$$w_{\text{Doc}} = \frac{7{,}5}{34{,}5} = 0{,}217 \qquad w_{\text{VcM}} = \frac{2{,}0}{34{,}5} = 0{,}058 \qquad w_{\text{Gest}} = \frac{25{,}0}{34{,}5} = 0{,}725$$

**Notas:**

- El resumen declaró 15 h de docencia sumando los dos semestres; en horas semanales son 7,5.
- La organización de un evento académico nacional se declaró en gestión; corresponde a VcM.
- La docencia pesa 21,7% del compromiso; para asistente vinculador el reglamento indica entre 60% y 70%.

### Sujeto 08

**Jerarquía:** Asociado · **Perfil supuesto:** investigador · **Jornada:** completa

- **Docencia:** 1.er semestre: asignaturas 1 y 2 (pregrado), asignatura 3 (postgrado), dirección de 3 tesis; 2.º semestre: seminario de título, asignatura 4 (postgrado), dirección de 2 tesis
- **Investigación, Creación e Innovación:** 4 proyectos (1 cierre y 3 postulaciones, 1 h c/u) y 3 publicaciones (4 h)
- **Vinculación con el Medio y Extensión:** 3 proyectos de extensión o creación (4 h c/u), 1 evento internacional (2 h), 2 redes internacionales (1 h c/u)
- **Gestión Académica:** Núcleo de magíster (2 h), comité de doctorado (5 h), reunión de departamento (1,5 h), comisión de concurso (0,5 h)

| Ámbito | Horas declaradas | % declarado | $h_a$ ordenadas | $w_a$ | $\omega_a$ |
|---|---|---|---|---|---|
| Docencia | 17,0 | 34,0% | 16,9 | 33,8% | 27,1% |
| Investigación, Creación e Innovación | 8,0 | 16,0% | 8,0 | 16,0% | 12,8% |
| Vinculación con el Medio y Extensión | 16,0 | 32,0% | 16,0 | 32,1% | 25,7% |
| Gestión Académica | 9,0 | 18,0% | 9,0 | 18,0% | 14,4% |

$$\sum_b h_b = 16{,}9 + 8{,}0 + 16{,}0 + 9{,}0 = 49{,}9 \text{ h semanales}$$

$$w_{\text{Doc}} = \frac{16{,}9}{49{,}9} = 0{,}338 \qquad w_{\text{ICI}} = \frac{8{,}0}{49{,}9} = 0{,}160 \qquad w_{\text{VcM}} = \frac{16{,}0}{49{,}9} = 0{,}321 \qquad w_{\text{Gest}} = \frac{9{,}0}{49{,}9} = 0{,}180$$

**Notas:**

- «16.45» y «3.45» horas se interpretan como 16 h 45 min y 3 h 45 min.
- 4 ponencias y la revisión de artículos se declararon sin horas: se evalúan, pero no ponderan.
- Las horas declaradas (49,9 h semanales) superan la jornada completa (44 h).
- La docencia pesa 33,8% del compromiso; para asociado investigador el reglamento indica entre 40% y 60%.

### Sujeto 09

**Jerarquía:** Asociado · **Perfil supuesto:** investigador · **Jornada:** completa

- **Docencia:** Asignaturas 1 a 6 (pregrado), 18 h semanales en cada semestre
- **Investigación, Creación e Innovación:** Proyecto de innovación pedagógica con financiamiento externo (8 h), 1 artículo (4,5 h), revisión de artículos para revista científica (2 h, declarada en gestión)
- **Vinculación con el Medio y Extensión:** Seminario de divulgación (2 h), representación en comisión internacional de divulgación (2 h, declarada en gestión)
- **Gestión Académica:** Reunión de departamento (1,5 h)

| Ámbito | Horas declaradas | % declarado | $h_a$ ordenadas | $w_a$ | $\omega_a$ |
|---|---|---|---|---|---|
| Docencia | 18,0 | 47,4% | 18,0 | 47,4% | 37,9% |
| Investigación, Creación e Innovación | 12,5 | 32,9% | 14,5 | 38,2% | 30,5% |
| Vinculación con el Medio y Extensión | 2,0 | 5,3% | 4,0 | 10,5% | 8,4% |
| Gestión Académica | 5,5 | 14,5% | 1,5 | 3,9% | 3,2% |

$$\sum_b h_b = 18{,}0 + 14{,}5 + 4{,}0 + 1{,}5 = 38{,}0 \text{ h semanales}$$

$$w_{\text{Doc}} = \frac{18{,}0}{38{,}0} = 0{,}474 \qquad w_{\text{ICI}} = \frac{14{,}5}{38{,}0} = 0{,}382 \qquad w_{\text{VcM}} = \frac{4{,}0}{38{,}0} = 0{,}105 \qquad w_{\text{Gest}} = \frac{1{,}5}{38{,}0} = 0{,}039$$

**Notas:**

- Dos actividades declaradas en gestión pertenecen a otros ámbitos según el catálogo SEJA.

## 7. Hallazgos transversales

1. **Sin horas no hay ponderación.** Ningún reporte ni informe 2023 registra horas por ámbito, y el formulario 2024 eliminó las horas por actividad. La afirmación «X es mayoría» no se puede verificar.
2. **Los informes 2023 no califican.** Marcan 100% o 0% por actividad, no agregan por ámbito ni asignan una letra, y no distinguen el excedente ni el avance más allá de lo comprometido.
3. **Inconsistencias entre documentos del mismo sujeto.** Hay resúmenes que no coinciden con su tabla (sujetos 01 y 02), una jerarquía distinta entre el reporte y el informe (sujeto 05), actividades declaradas que no se evalúan al cierre (sujetos 03 y 06) y conteos distintos de actividades (sujeto 02).
4. **Conclusiones que contradicen la tabla de funciones.** Un informe afirma que las actividades son las exigidas para la jerarquía aunque marca 4 funciones como no cumplidas (sujeto 02).
5. **Clasificación de actividades.** Los claustros de postgrado, los núcleos de investigación, la revisión de artículos, las representaciones internacionales y la organización de eventos se registran en gestión, pero pertenecen a investigación o a VcM. El «perfeccionamiento» se registra como un área aparte.
6. **Las horas se registran de tres formas.** Hay sumas de los dos semestres, valores «x + x» y horas con minutos escritas como decimales («16.45»).
7. **La normativa cambia.** Los informes 2023 revisan funciones de la Res. 320/93. La propuesta de Reglamento de Carrera Académica define funciones por jerarquía y perfil, con carga docente esperada, lo que deja más funciones pendientes en varios sujetos (por ejemplo, formación de académicos, redes y formación continua).

## 8. Recomendaciones

1. Registrar en UCampus las **horas semanales por ámbito** (por semestre en docencia) y calcular el resumen automáticamente con la fórmula 3.3.
2. Declarar cada actividad eligiendo su **subcategoría del catálogo SEJA** y su **etapa comprometida**; al cierre, registrar la **etapa evidenciada** y el **mecanismo**.
3. Aplicar y registrar la **autoevaluación** y la **evaluación de estudiantes** (20% de la calificación).
4. Pedir el **perfil** (investigador/a o vinculador/a) y mostrar el rango de carga docente de la jerarquía.
5. Generar el reporte de octubre y el informe de cierre **desde los mismos datos** (`python -m seja reporte` y `python -m seja cierre`), para evitar las inconsistencias entre documentos.
6. Mantener el registro de **destacados** (excedentes y avances validados) para el reconocimiento institucional.

## Anexo. Parámetros del modelo

| Parámetro | Valor |
|---|---|
| Autoevaluación / evaluación de estudiantes | 10% / 10% |
| Compromiso (ámbitos) | 80% (90% si está eximido/a de docencia) |
| Tope por tarea con excedente validado | 120% |
| Etapa evidenciada anterior a la comprometida | 50% |
| Suspensión (art. 37) | Ausencia justificada de más de 5 meses continuos |
| Umbrales | A+ ≥ 101%; A 90–100%; B 75–89%; C 55–74%; D < 55% |
| Jornada | Completa 44 h; media 22 h |
