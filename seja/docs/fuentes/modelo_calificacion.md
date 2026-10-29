---
title: "Modelo de Calificación Académica SEJA"
subtitle: "Sistema de Evaluación y Jerarquización Académica · Oficina de Evaluación de Desempeño Académico · Vicerrectoría Académica"
date: "{{FECHA}}"
lang: es
---

# 1. Propósito

Este documento describe el modelo con que el Sistema de Evaluación y Jerarquización Académica (SEJA) califica el
desempeño de cada académico y académica de la UMCE a partir de su Compromiso de Desempeño Académico. Define qué se
evalúa, con qué instrumentos y evidencias, cómo se pondera cada ámbito, cómo se calcula la calificación final y cómo
se clasifica.

El modelo es **flexible**: cada persona compromete sus propias actividades y su propia distribución de horas, según
su jerarquía y su jornada. Por eso no hay una ponderación única: la calificación se calcula con la combinación
de tareas y horas que cada persona declaró y que su jefatura aprobó.

# 2. Marco normativo

- **Reglamento de Carrera Académica UMCE** (propuesta): jerarquías, funciones y carga docente (Título II). La carrera académica UMCE tiene un **único perfil**;
  evaluación académica (Título III), en particular los artículos 31 a 41.
- **Síntesis de avances y principales definiciones SEJA** (agosto 2026): definiciones de los cuatro ámbitos
  evaluables.
- **Jornada Modelo de Evaluación SEJA 2024:** instrumentos con pauta de afirmaciones, catálogo de actividades,
  periodicidad y tabla de equivalencia a la escala numérica.
- **Formulario de Compromiso de Desempeño Académico** (UCampus).

# 3. Estructura del modelo

La calificación se construye en tres niveles:

| Nivel | Qué es | Cómo se obtiene |
|---|---|---|
| **Tarea** | Cada actividad comprometida (un curso, un proyecto, una publicación, una coordinación) | Con un instrumento estandarizado y/o con la evidencia de la carpeta individual |
| **Ámbito** | Docencia; Investigación, Creación e Innovación; Vinculación con el Medio y Extensión; Gestión Académica | Promedio de sus tareas |
| **Calificación final** | Resultado del período | Ámbitos ponderados por las horas comprometidas (80%), más autoevaluación (10%) y evaluación de estudiantes (10%) |

## 3.1 Ámbitos y subcategorías

Cada tarea se registra en una subcategoría (rol o función) de uno de los cuatro ámbitos. La subcategoría define el
instrumento o la evidencia con que se evalúa y su periodicidad.

{{CATALOGO}}

# 4. Ciclo de evaluación

1. **Compromiso de Desempeño.** El académico o académica declara, de acuerdo con su dirección, sus actividades del
   período: cada una con su subcategoría, sus horas semanales y lo que compromete (una meta, una etapa del proceso o
   una actividad evaluada con instrumento). La jefatura da su visto bueno.
2. **Evidencias.** Durante el período, la persona sube la evidencia de cada actividad a su **carpeta individual
   (Drive)**.
3. **Aplicación de instrumentos.** La Oficina coordina la aplicación de las pautas a estudiantes, direcciones y
   unidades, y la autoevaluación.
4. **Calificación.** La Oficina calcula el cumplimiento de cada tarea y de cada ámbito, y la calificación final, con
   las fórmulas de las secciones 5 a 8.
5. **Informe y Comisión.** La Oficina elabora el expediente y el informe de cierre. La Comisión Central de
   Calificación y Jerarquización Académica decide la calificación y la registra en un acta.
6. **Notificación y apelación.** Se notifica por escrito a la persona, que puede apelar en los plazos del reglamento.

# 5. Cumplimiento de cada tarea

El cumplimiento de la tarea $t$, $p_t$, se expresa en porcentaje y se obtiene según la forma de evaluación que
corresponde a su subcategoría.

## 5.1 Pauta de afirmaciones (Cumple / No cumple / No aplica)

Es el formato de los instrumentos institucionales (evaluación de estudiantes, de la dirección, autoevaluación, pautas
de las direcciones de Investigación y de Vinculación con el Medio). Con $C$ afirmaciones cumplidas y $NC$ no
cumplidas; las afirmaciones "no aplica" no cuentan:

$$p_t = \frac{C}{C + NC} \times 100$$

## 5.2 Instrumento con escala

Para un instrumento con puntaje $x$ en una escala de $x_{\min}$ a $x_{\max}$ (por ejemplo, una rúbrica de 1 a 4):

$$p_t = \frac{x - x_{\min}}{x_{\max} - x_{\min}} \times 100$$

## 5.3 Evidencia con meta

Cuando se compromete una cantidad $M$ (por ejemplo, 2 artículos o 3 tesis dirigidas) y se logra $L$:

$$p_t = \min\left(\frac{L}{M \cdot f},\ 1\right) \times 100$$

donde $f$ es el factor de jornada de la sección 9 ($f = 1$ si no hay situación especial).

## 5.4 Evidencia por etapa del proceso

Cuando se compromete llegar a una etapa (por ejemplo, el envío de un artículo o la ejecución de un proyecto), se
compara la etapa evidenciada con la comprometida dentro de su secuencia:

| Secuencia | Etapas |
|---|---|
| Proyecto | Formulación → Postulación → Adjudicación → Ejecución → Cierre |
| Publicación | En preparación → Enviada → Aceptada → Publicada |
| Actividad | Planificación → Ejecución → Finalizada |

$$p_t = \begin{cases} 100 & \text{si la etapa evidenciada es igual o posterior a la comprometida} \\ {{ETAPA_ANTERIOR}} & \text{si la etapa evidenciada es anterior a la comprometida} \\ 0 & \text{si no hay evidencia} \end{cases}$$

## 5.5 Evidencia por estado

Para actividades sin meta numérica ni etapa: cumplido = 100; parcial = 50; no cumplido o sin evidencia = 0.

## 5.6 Instrumento y evidencia en la misma tarea

Si una tarea tiene instrumento y evidencia, $p_t$ es el promedio de ambos resultados.

## 5.7 Evidencia válida

La evidencia válida es la que la persona sube a su **carpeta individual (Drive)**. La información que la Oficina pueda
recoger de otras fuentes, como la carga académica, es un trabajo adicional y **no acredita cumplimiento**: la tarea
vale $p_t = 0$. Quien no provee evidencias obtiene la calificación mínima. La carga académica sí se usa para las horas
de la ponderación (sección 7).

## 5.8 Excedente y reconocimiento institucional

Si lo logrado supera lo comprometido ($L > M$) y el excedente está **validado**, la tarea cuenta sobre 100%, con un
tope de {{TOPE}}%:

$$p_t = \min\left(\frac{L}{M \cdot f} \times 100,\ {{TOPE}}\right)$$

Lo que supera el tope no sube la calificación, pero queda **registrado como destacado** (tarea, subcategoría y
cumplimiento real) para el reconocimiento institucional. También se registra como destacado el avance validado más
allá de la etapa comprometida (por ejemplo, comprometer el envío de un artículo y publicarlo). Un excedente sin
validar cuenta como 100%.

# 6. Cumplimiento de cada ámbito

Las tareas de cada ámbito $a$ se promedian. $\pi_t$ es un peso opcional de la tarea, que por defecto vale 1:

$$S_a = \frac{\sum_{t \in a} \pi_t \, p_t}{\sum_{t \in a} \pi_t}$$

Cada ámbito recibe además su propia letra, con los umbrales de la sección 8. Un ámbito con horas comprometidas y sin
tareas evaluadas tiene $S_a = 0$.

# 7. Ponderación de cada ámbito

La ponderación de cada ámbito es la proporción de las **horas semanales** que la persona comprometió en él. Si la
carga cambia entre semestres $s$, se usa el promedio:

$$h_a = \frac{1}{|S|} \sum_{s \in S} h_{a,s}$$

$$w_a = \frac{h_a}{\sum_b h_b}, \qquad \sum_a w_a = 1$$

Las horas que se comprometen son las de la jornada **menos el horario de almuerzo** (1 hora diaria):
{{JORNADAS}}. Las actividades sin horas (por ejemplo, una ponencia) se evalúan dentro de su ámbito, pero no aportan
horas a la ponderación. Cada actividad cuenta en el ámbito de su subcategoría, no en la sección del formulario donde se escribió.

**Validaciones del compromiso.** Al calcular la ponderación se advierte a la jefatura si:

- la suma de horas no coincide con las horas a justificar de la jornada (39 h o 20 h);
- el peso de la docencia, $w_{\text{docencia}}$, queda fuera del rango esperado para la jerarquía (provisional,
  mientras el reglamento lo fija para el perfil único):

{{RANGOS}}

# 8. Calificación final y clasificación

## 8.1 Cumplimiento del compromiso y calificación final

El cumplimiento del compromiso es el promedio de los ámbitos ponderado por las horas:

$$C = \sum_a w_a \, S_a$$

La calificación final agrega la autoevaluación ($AE$) y la evaluación de estudiantes ($EE$), ambas de 0 a 100%.
Las dos tienen **siempre el mismo peso** $p$: al fijar el de una, el de la otra es el mismo. El valor de $p$
**aún no está definido**; mientras tanto se usa $p = {{P}}$ como valor provisional.

$$F = \alpha \sum_a w_a \, S_a + p \cdot AE + p \cdot EE = \alpha \cdot C + p \cdot AE + p \cdot EE, \qquad \alpha = 1 - 2p$$

Si la persona está eximida de docencia y no tiene evaluación de estudiantes, ese peso se suma a los ámbitos:
$\alpha = 1 - p$ y $F = \alpha \cdot C + p \cdot AE$. El peso efectivo de cada ámbito en la calificación final
es:

$$\omega_a = \alpha \cdot w_a$$

## 8.2 Clasificación

{{UMBRALES}}

La letra depende sólo del cumplimiento final $F$: no se exige un mínimo por ámbito ni combinaciones de logro entre
ámbitos.

## 8.3 Escala numérica

Para la equivalencia con la escala de 1 a 7 (Jornada 2024):

{{ESCALA}}

## 8.4 Consecuencias de la clasificación

- **A+:** desempeño sobresaliente; la persona es candidata a reconocimiento institucional, junto con el registro de
  lo que destaca.
- **A en los dos últimos procesos:** requisito para ascender de jerarquía (art. 11).
- **D, o C en dos procesos consecutivos:** ingreso obligatorio al programa institucional de acompañamiento y
  fortalecimiento académico (art. 41).

# 9. Situaciones especiales (art. 37)

| Situación | Tratamiento |
|---|---|
| Ausencia justificada de más de {{MESES}} meses continuos, por cualquier motivo | Se **suspende** la evaluación del período |
| Comisión de estudios | Depende del período y las condiciones con que se otorgó. Si tiene compromisos asociados, se evalúan en relación al % de jornada, aunque dure más de {{MESES}} meses; si no los tiene, se aplica la regla anterior |
| Cualquier otra situación (licencias más cortas, permisos, comisión de servicio, cargo directivo, horas de estudio) | Se evalúa en relación al % de la jornada dedicado a sus funciones |

En la evaluación proporcional, las metas con evidencia se ajustan con el factor de jornada:

$$f = \frac{\%\ \text{de la jornada dedicado a sus funciones}}{100}$$

El excedente sólo se reconoce si lo logrado supera la meta original, no la ajustada. En todos los casos se informa a
la Oficina de Evaluación de Desempeño Académico y a las autoridades correspondientes.

# 10. Funciones de la jerarquía

Además de la calificación, el informe de cierre revisa si las actividades evidenciadas cubren las funciones que el
Reglamento de Carrera Académica asigna a la jerarquía (art. 14, 18-19, 23-24 y 28-29; con perfil único, cada jerarquía
reúne las funciones de los antiguos perfiles). Cada función se
marca como **cumplida**, **sin evidencia** o **no declarada**; las funciones opcionales se indican aparte. Esta
revisión orienta el desarrollo profesional y la jerarquización; no modifica la calificación.

# 11. Ejemplo ilustrativo de cálculo

Ejemplo hipotético, sólo para mostrar el cálculo. Un académico con jornada completa (44 h de contrato,
39 h a justificar) compromete 20 h de docencia, 11 h de investigación, 3 h de vinculación con el medio y 5 h de
gestión. Se usa el valor provisional $p = 0{,}10$.

**Ponderación (sección 7):**

$$w_{\text{Doc}} = \frac{20}{39} = 0{,}513 \quad w_{\text{ICI}} = \frac{11}{39} = 0{,}282 \quad w_{\text{VcM}} = \frac{3}{39} = 0{,}077 \quad w_{\text{Gest}} = \frac{5}{39} = 0{,}128$$

**Tareas y ámbitos (secciones 5 y 6):**

| Ámbito | Tareas | $p_t$ | $S_a$ |
|--------------|----------------------------------------------|----------|--------|
| Docencia | Pauta de estudiantes: 27 cumple, 3 no cumple → 90%; dirección de 3 tesis comprometidas, 3 logradas → 100% | 90; 100 | 95,0 |
| Investigación | Proyecto en ejecución, etapa alcanzada → 100%; 2 artículos comprometidos, 1 enviado → 50% | 100; 50 | 75,0 |
| Vinculación con el Medio | 2 talleres comprometidos, 3 realizados y validados → 150%, cuenta 120% (destacado) | 120 | 120,0 |
| Gestión | Coordinación evidenciada → 100% | 100 | 100,0 |

**Cumplimiento del compromiso y calificación final (sección 8)**, con $AE = 90\%$ y $EE = 88\%$ (los pesos se muestran redondeados; el cálculo usa las fracciones exactas):

$$C = 0{,}513 \cdot 95{,}0 + 0{,}282 \cdot 75{,}0 + 0{,}077 \cdot 120{,}0 + 0{,}128 \cdot 100{,}0 = 91{,}9\%$$

$$F = 0{,}80 \cdot 91{,}9 + 0{,}10 \cdot 90 + 0{,}10 \cdot 88 = 91{,}3\%$$

Resultado: **A** (cumplimiento pleno), escala numérica 7. El taller excedente queda registrado como destacado para el
reconocimiento institucional.

# Anexo. Parámetros del modelo

{{PARAMETROS}}

Los parámetros están en la configuración del sistema (`seja/config/modelo.yaml`) y pueden ajustarse sin modificar el
cálculo.
