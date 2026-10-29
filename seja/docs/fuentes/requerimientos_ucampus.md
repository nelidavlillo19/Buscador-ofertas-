---
title: "Requerimientos para UCampus: Evaluación Académica SEJA"
subtitle: "Qué se necesita para aplicar las evaluaciones, recoger y analizar los resultados y entregar la calificación · Oficina de Evaluación de Desempeño Académico · Vicerrectoría Académica"
date: "{{FECHA}}"
lang: es
---

# 1. Objetivo

Definir lo que UCampus debe incorporar para que la evaluación académica SEJA funcione de principio a fin:

1. registrar el Compromiso de Desempeño con los datos que el modelo necesita;
2. aplicar los instrumentos y recoger las evidencias;
3. calcular la calificación con las fórmulas del documento *Modelo de Calificación Académica SEJA*;
4. analizar los resultados y entregar el informe a cada persona, a su jefatura y a la Comisión Central.

**Por qué hace falta.** El formulario 2024 no permite calcular la calificación:

- no pide jerarquía ni jornada;
- no tiene horas por actividad ni un área de gestión;
- su resumen acepta "horas o porcentaje", lo que mezcla unidades;
- los informes de cierre se elaboran a mano, a partir de documentos distintos.

Los requerimientos de este documento corrigen esas brechas.

# 2. Actores y responsabilidades

| Actor | Qué hace en UCampus |
|---|---|
| Académico/a | Declara el compromiso, sube evidencias, responde la autoevaluación, revisa su informe y puede apelar |
| Dirección de unidad académica | Orienta y aprueba el compromiso, aplica la pauta de la dirección, valida evidencias de su unidad |
| Estudiantes | Responden la evaluación de cada actividad curricular (anónima) |
| Direcciones de Investigación, VcM, Docencia y otras | Aplican sus pautas y validan las evidencias de su área |
| Oficina de Evaluación de Desempeño Académico | Administra calendario, catálogo y parámetros; revisa evidencias; ejecuta el cálculo; elabora expedientes e informes |
| Comisión Central de Calificación y Jerarquización | Revisa expedientes, decide la calificación y firma el acta |
| Comisión de Apelación | Resuelve las apelaciones |

# 3. Datos maestros

## 3.1 Ficha académica

UCampus debe disponer, para cada persona y período, de estos datos, sin que la persona tenga que escribirlos:

| Dato | Uso en el modelo |
|---|---|
| Unidad académica y facultad | Reportes por unidad y asignación de la jefatura que aprueba |
| Jerarquía (instructor/a, asistente, asociado/a, titular) | Rango de carga docente y funciones de la jerarquía |
| Jornada: completa (44 h de contrato, 39 h a justificar) o media (22 h de contrato, 20 h a justificar) | Validación de la suma de horas (se descuenta 1 hora diaria de almuerzo) |
| Tipo de contrato y año de ingreso | Elegibilidad (art. 35: al menos dos semestres de ejercicio) |
| Carga académica asignada por la Dirección de Docencia | Precarga de las actividades curriculares y sus horas |
| Situación especial vigente (sección 7) | Suspensión o evaluación proporcional |

## 3.2 Catálogo SEJA

Tablas administradas por la Oficina, que el formulario usa como listas desplegables:

- **Ámbitos** (4) y **subcategorías** (roles y funciones), con el instrumento o la evidencia que corresponde a cada una
  y su periodicidad (semestral, anual, bianual).
- **Secuencias de etapas**:
  - proyecto: formulación → postulación → adjudicación → ejecución → cierre;
  - publicación: en preparación → enviada → aceptada → publicada;
  - actividad: planificación → ejecución → finalizada.
- **Instrumentos**, con sus afirmaciones y el formato Cumple / No cumple / No aplica.
- **Funciones por jerarquía** del Reglamento de Carrera Académica (perfil único).

## 3.3 Parámetros del modelo

Configurables por la Oficina, con historial de cambios. Cada período queda calculado con los parámetros vigentes en
ese período.

{{PARAMETROS}}

**Peso de la autoevaluación y de la evaluación de estudiantes.** Su % aún no está definido. Cuando se defina, la
pantalla de parámetros tendrá **un solo campo**, $p$: al seleccionar el % de la autoevaluación, el de la evaluación de
estudiantes toma automáticamente el mismo valor, y viceversa. El peso de los ámbitos se recalcula solo:
$1 - 2p$, o $1 - p$ si la persona está eximida de docencia. El sistema no debe permitir guardar valores distintos
para ambas.

# 4. Módulo 1: Compromiso de Desempeño

## 4.1 Encabezado

Se precarga con la ficha académica (sección 3.1). La persona sólo confirma sus datos o informa un error.

## 4.2 Registro de actividades

Cada actividad es una fila con estos campos:

| Campo | Tipo | Observación |
|---|---|---|
| Ámbito | Lista (4 ámbitos) | Obligatorio |
| Subcategoría | Lista dependiente del ámbito | Obligatorio; define el instrumento y la evidencia esperada |
| Descripción | Texto | Por ejemplo, el nombre del curso, proyecto o comisión |
| Código de actividad curricular | Texto o selección desde la carga | Sólo en docencia; permite enlazar la evaluación de estudiantes |
| Horas semanales, 1.er semestre | Número con decimales (0,5 = media hora) | No se aceptan textos como "4,5 + 4,5" |
| Horas semanales, 2.º semestre | Número con decimales | |
| Forma de evaluación | Lista: instrumento, meta, etapa, estado | Sugerida por la subcategoría |
| Meta comprometida | Número | Si la forma es "meta" (por ejemplo, 2 artículos) |
| Etapa comprometida | Lista según la secuencia | Si la forma es "etapa" (por ejemplo, "enviada") |
| Rol | Lista: responsable, co-investigador/a, colaborador/a, integrante, coordinador/a… | Para la revisión de funciones de la jerarquía |
| Financiamiento | Lista: interno, externo nacional, externo internacional, sin financiamiento | Proyectos y programas |
| Fechas de inicio y término | Mes y año | |
| Línea de tributación | Lista del plan de desarrollo | |

La **gestión académica** es un ámbito más, con sus propias filas y horas, y no un texto libre dentro de otras áreas.
Las actividades sin horas (por ejemplo, una ponencia) se pueden registrar con 0 h: se evalúan, pero no ponderan.

## 4.3 Resumen calculado

UCampus calcula y muestra el resumen; la persona no lo escribe:

$$h_a = \frac{h_{a,1} + h_{a,2}}{2} \qquad w_a = \frac{h_a}{\sum_b h_b}$$

El resumen muestra, por ámbito: horas semanales, % del compromiso ($w_a$) y peso en la calificación final
($\omega_a = 0{,}8\,w_a$).

## 4.4 Validaciones al enviar

| Validación | Acción |
|---|---|
| Suma de horas distinta de las horas a justificar (39 h en jornada completa, 20 h en media jornada) | Alerta a la persona y a la jefatura; requiere justificación |
| Docencia fuera del rango esperado para la jerarquía | Alerta a la jefatura |
| Ámbito con horas y sin actividades, o actividad sin subcategoría | Bloquea el envío |
| Meta o etapa comprometida vacía en una actividad que la requiere | Bloquea el envío |
| Etapa comprometida ya alcanzada al declarar (por ejemplo, un artículo ya publicado) | Sugiere comprometer la etapa siguiente o verificar que corresponda al período |

## 4.5 Aprobación y modificaciones

- La jefatura aprueba o devuelve el compromiso con observaciones.
- Las modificaciones durante el año requieren nueva aprobación y quedan versionadas: el cálculo usa la última versión
  aprobada.
- UCampus registra quién no ha presentado compromiso en la fecha de cierre y avisa a la Oficina y a la jefatura, para
  que nadie quede fuera por falta de inducción.

# 5. Módulo 2: Evidencias

## 5.1 Carpeta individual

Cada actividad comprometida tiene un espacio de evidencia dentro de la carpeta individual: integración con Google
Drive o un repositorio de UCampus. Por actividad se registra:

| Campo | Descripción |
|---|---|
| Archivo(s) o enlace | Constancia, certificado, carta, informe, publicación, afiche, registro |
| Mecanismo | Lista según la subcategoría (por ejemplo, "constancia de la revista", "carta de adjudicación") |
| Etapa evidenciada | Si la actividad se comprometió por etapa |
| Cantidad lograda | Si se comprometió una meta |
| Fecha de la evidencia | Debe estar dentro del período |
| Estado de revisión | Pendiente, validada, observada o rechazada |
| Validado por / fecha | Dirección o Oficina que revisó |
| Excedente | Marca automática cuando lo logrado supera lo comprometido; requiere validación |

## 5.2 Reglas

- **Sólo cuenta la evidencia de la carpeta individual.** UCampus no debe marcar una actividad como cumplida por estar
  en la carga académica: si no hay evidencia, la actividad queda "sin evidencia" ($p_t = 0$).
- Las evidencias se suben durante todo el período; la Oficina fija una fecha de cierre.
- Antes del cierre, UCampus envía recordatorios a quienes tengan actividades sin evidencia.

# 6. Módulo 3: Instrumentos

## 6.1 Aplicación

| Instrumento | Responde | Se asocia a | Periodicidad |
|---|---|---|---|
| Evaluación de la docencia (estudiantes) | Estudiantes de cada sección | Actividad curricular (código y sección) | Semestral |
| Evaluación de la docencia (dirección de unidad) | Dirección | Actividades de docencia de la persona | Semestral |
| Autoevaluación | Académico/a | Persona | Anual |
| Evaluación de investigación, creación e innovación | Dirección de Investigación | Proyectos y productos | Anual |
| Evaluación de vinculación con el medio | Dirección de VcM o de la unidad | Iniciativas, proyectos y programas | Semestral o anual |
| Evaluación a la gestión (coordinaciones) | Decanatura o dirección | Cargo o coordinación | Anual |

## 6.2 Requisitos

- Formato de respuesta **Cumple / No cumple / No aplica** por afirmación, con las afirmaciones administradas en el
  catálogo.
- Resultado por instrumento:

$$p = \frac{C}{C + NC} \times 100$$

- **Anonimato** de las respuestas de estudiantes y número mínimo de respuestas por sección para informar el
  resultado (a definir por la Oficina).
- Seguimiento de la tasa de respuesta por sección y recordatorios automáticos.
- La evaluación de estudiantes ($EE$) de la persona es el promedio de sus secciones, ponderado por el número de
  respuestas.

# 7. Módulo 4: Situaciones especiales (art. 37)

| Campo | Descripción |
|---|---|
| Motivo | Enfermedad, maternidad, parental, permiso sin goce, comisión de servicio, cargo directivo, comisión de estudios, otra |
| Fecha de inicio y de término | Para calcular los meses continuos |
| % de la jornada dedicado a sus funciones | Para el factor $f$ |
| Compromisos asociados | Sólo en comisión de estudios: sí o no, y cuáles |
| Documento de respaldo | Resolución o certificado |

Reglas que UCampus aplica automáticamente:

- **Más de {{MESES}} meses continuos de ausencia justificada:** evaluación suspendida, salvo una comisión de estudios
  con compromisos asociados.
- **Otras situaciones:** evaluación proporcional, con $f = \dfrac{\%\ \text{jornada}}{100}$ aplicado a las metas.
- **Aviso:** notificación automática a la Oficina y a las autoridades correspondientes.

# 8. Módulo 5: Cálculo de la calificación

UCampus ejecuta el cálculo al cierre del período (y en modo de simulación durante el año), en este orden:

1. **Elegibilidad y situación especial:** si la evaluación está suspendida, se registra el estado "suspendida" y no
   se calcula letra.
2. **Cumplimiento de cada tarea** ($p_t$), según su forma de evaluación:

| Forma | Fórmula |
|---|---|
| Pauta | $p_t = \dfrac{C}{C+NC} \times 100$ |
| Escala | $p_t = \dfrac{x - x_{\min}}{x_{\max} - x_{\min}} \times 100$ |
| Meta | $p_t = \min\left(\dfrac{L}{M f},\ 1\right) \times 100$; con excedente validado, $\min\left(\dfrac{L}{M f} \times 100,\ {{TOPE}}\right)$ |
| Etapa | 100 si alcanza la etapa comprometida; {{ETAPA_ANTERIOR}} si queda en una anterior; 0 sin evidencia |
| Estado | Cumplido 100; parcial 50; no cumplido o sin evidencia 0 |

3. **Cumplimiento de cada ámbito:**

$$S_a = \frac{\sum_{t \in a} \pi_t\, p_t}{\sum_{t \in a} \pi_t}$$

4. **Ponderación de cada ámbito**, desde las horas del compromiso aprobado: $w_a = h_a / \sum_b h_b$.
5. **Cumplimiento del compromiso y calificación final:**

$$C = \sum_a w_a S_a \qquad F = \alpha\, C + p\, AE + p\, EE, \qquad \alpha = 1 - 2p \ (1 - p \text{ si está eximido/a de docencia})$$

6. **Clasificación** (A+, A, B, C, D) y escala numérica de 1 a 7, con los parámetros del período.
7. **Destacados:** excedentes y avances validados, con su cumplimiento real.
8. **Funciones de la jerarquía:** cumplida, sin evidencia o no declarada, por cada función del reglamento.
9. **Alertas:** horas distintas de las horas a justificar, docencia fuera de rango, D o segunda C consecutiva (art. 41), A en dos procesos
   seguidos (requisito de ascenso, art. 11).

**Trazabilidad.** Cada resultado guarda la versión del compromiso, de los parámetros y de las evidencias con que se
calculó. Un recálculo (por ejemplo, tras una apelación) genera una nueva versión, sin borrar la anterior.

**Implementación de referencia.** El cálculo está implementado y probado en el repositorio del proyecto (`seja/`,
`python -m seja`). Esa implementación puede usarse para validar los resultados de UCampus con casos de prueba.

# 9. Módulo 6: Resultados

## 9.1 Qué debe arrojar el sistema por persona

| Campo | Ejemplo de valor |
|---|---|
| Estado | Calificada / Suspendida |
| Cumplimiento final $F$ | 91,8% |
| Clasificación | A (cumplimiento pleno) |
| Escala numérica | 7 |
| Por ámbito | Horas, $w_a$, $\omega_a$, $S_a$ y letra del ámbito |
| Por tarea | Comprometido, evidenciado, mecanismo, $p_t$, validación |
| Autoevaluación y evaluación de estudiantes | % y número de respuestas |
| Destacados | Tarea, subcategoría y cumplimiento real |
| Funciones de la jerarquía | Cumplida, sin evidencia o no declarada |
| Situación especial | Motivo, factor $f$, aviso enviado |
| Observaciones y alertas | Jornada, rango docente, programa de acompañamiento |

## 9.2 Documentos que genera

- **Reporte del compromiso** (al aprobarse el compromiso): distribución de horas, actividades por ámbito, evidencia
  esperada y alertas para la jefatura.
- **Informe de cierre** (al cierre del período): cumplimiento por actividad y por ámbito, calificación, destacados,
  funciones de la jerarquía, y oportunidades y fortalezas.
- **Expediente para la Comisión Central:** informe de cierre, evidencias y alertas; espacio para la decisión y el
  acta.
- **Notificación escrita** a la persona, con el plazo de apelación.

Los documentos se generan desde los mismos datos, para evitar diferencias entre el reporte, el informe y el acta.

## 9.3 Exportación

Exportar los resultados en formato tabular (Excel o CSV) y estructurado (JSON), por persona, unidad y período, para
análisis institucional y para la acreditación.

# 10. Análisis de resultados

Tablero de la Oficina, con filtros por período, facultad, unidad, jerarquía y jornada:

| Indicador | Para qué sirve |
|---|---|
| Distribución de letras (A+, A, B, C, D) y de cumplimiento final | Visión general del período |
| Cumplimiento promedio por ámbito ($S_a$) | Detectar ámbitos débiles por unidad |
| Distribución de horas por ámbito ($w_a$) frente al rango de la jerarquía | Revisar la asignación de carga |
| % de actividades con evidencia validada / sin evidencia | Medir la adhesión a la carpeta individual |
| Tasa de respuesta de los instrumentos | Confiabilidad de la evaluación de estudiantes |
| Compromisos no presentados o incompletos | Seguimiento de la inducción |
| Destacados por ámbito y subcategoría | Insumo para el reconocimiento institucional |
| Personas en D o con dos C seguidas | Ingreso al programa de acompañamiento |
| Personas con A en dos procesos | Candidatas a ascenso |
| Comparación entre períodos por persona y por unidad | Evolución y mejora continua |

# 11. Roles, permisos y privacidad

- Cada persona ve su compromiso, sus evidencias y su resultado; la jefatura, los de su unidad; la Oficina y la
  Comisión, todos.
- Las respuestas de estudiantes son anónimas y se informan agregadas.
- Los informes para análisis institucional se publican sin nombres.
- Registro de accesos y de cambios sobre compromisos, evidencias, parámetros y resultados.

# 12. Calendario del proceso

| Etapa | Período sugerido |
|---|---|
| Inducción y apertura del compromiso | Marzo |
| Envío y aprobación del compromiso | Abril |
| Reporte del compromiso a la jefatura | Mayo |
| Aplicación de instrumentos del 1.er semestre | Junio–julio |
| Revisión de mitad de año y modificaciones del compromiso | Agosto |
| Aplicación de instrumentos del 2.º semestre | Noviembre–diciembre |
| Cierre de evidencias | Enero |
| Cálculo, informe de cierre y expediente | Febrero |
| Comisión Central, notificación y apelación | Marzo |

Las fechas definitivas las fija la Oficina en el calendario oficial aprobado por la Vicerrectoría Académica.

# 13. Implementación por etapas

| Fase | Alcance |
|---|---|
| 1 | Ficha académica, catálogo y nuevo formulario de compromiso con horas, subcategorías, metas y etapas; resumen y validaciones automáticas |
| 2 | Carpeta individual por actividad, revisión y validación de evidencias, situaciones especiales |
| 3 | Instrumentos en formato Cumple / No cumple / No aplica, enlazados a actividades y secciones |
| 4 | Cálculo automático, informe de cierre, expediente y notificación |
| 5 | Tablero de análisis, exportaciones y comparación entre períodos |

# Anexo. Estructura de datos

| Entidad | Campos principales |
|---|---|
| Académico | id, unidad, facultad, jerarquía, jornada, horas de contrato, horas a justificar, contrato, ingreso |
| Período | año, fechas del calendario, versión de parámetros |
| Compromiso | id, académico, período, versión, estado (borrador, enviado, aprobado), fecha de aprobación, jefatura |
| Actividad | id, compromiso, ámbito, subcategoría, descripción, código curricular, horas 1.er y 2.º semestre, forma de evaluación, meta, etapa comprometida, rol, financiamiento, fechas |
| Evidencia | id, actividad, archivo o enlace, mecanismo, etapa evidenciada, cantidad lograda, fecha, estado de revisión, validado por, excedente |
| Instrumento | id, nombre, afirmaciones, responde, periodicidad |
| Respuesta | id, instrumento, actividad o persona, cumple, no cumple, no aplica, fecha (anónima para estudiantes) |
| Situación especial | id, académico, motivo, inicio, término, % jornada, compromisos asociados, respaldo |
| Resultado | id, académico, período, estado, F, letra, escala, C, AE, EE, por ámbito (h, w, ω, S, letra), destacados, funciones, alertas, versión de cálculo |
