# Compromisos de Desempeño: qué registran los académicos y cómo se pondera cada ámbito

Revisión del formulario de Compromiso de Desempeño Académico 2024 (UCampus) y de tres compromisos
2023 reales, anonimizados, para probar la flexibilidad del modelo SEJA y fijar cómo se calcula la
ponderación de cada ámbito.

## 1. Qué puede registrar un académico/a

| Área | Formulario 2023 (Word) | Formulario 2024 (UCampus) |
|---|---|---|
| Datos | Facultad, departamento, jornada, relación contractual, jerarquía | RUT y correo (el resto viene de UCampus) |
| Docencia | Tipo de actividad, nombre, código, departamento, **horas** | Tipo de actividad, nombre, código, departamento, tipo de interacción (presencial o virtual), modalidad (sincrónica o asincrónica), archivo de carga. **Sin horas** |
| Investigación | Proyectos (título, tipo, financiamiento, fechas, participación, **horas**), publicaciones (**horas**), patentes | Proyectos (además, línea de tributación al plan de desarrollo), publicaciones con su **estado** (por enviar, enviada, aceptada, publicada), otros productos (patentes, licencias, registros de autoría), postulaciones a fondos. **Sin horas** |
| Vinculación con el Medio | Iniciativas, proyectos y programas (**horas**), ponencias, asesorías externas | Iniciativas, proyectos y programas, obras artísticas, congresos y seminarios. **Sin horas** |
| Gestión | Sección propia, con tareas, productos y **horas** | No tiene sección: se describe en texto libre dentro de cada área (coordinaciones, secretaría académica, dirección, coordinación de investigación o de VcM) |
| Perfeccionamiento | Sección propia | No está |
| Resumen | Horas de docencia, investigación, VcM, gestión y perfeccionamiento | "Horas o porcentaje de jornada" de docencia, investigación y VcM (**sin gestión**) |

Tipos de actividad de docencia que admite el formulario: docencia de pregrado, tutoría de prácticas
profesionales, dirección de tesis, seminarios de título, memorias o tesinas, educación continua y docencia
de postgrado.

## 2. Los tres sujetos

Los casos están en [`ejemplos/compromisos_2023/`](../ejemplos/compromisos_2023). Las horas son las declaradas.
Los resultados de evaluación son ficticios y sólo sirven para probar el cálculo.

| | Sujeto 07 | Sujeto 08 | Sujeto 09 |
|---|---|---|---|
| Jerarquía | Asistente | Asociado/a | Asociado/a |
| Perfil de carga | Centrado en gestión (coordinación de prácticas) | Docencia, creación y VcM | Docencia e investigación |
| Horas declaradas (semanales) | 42 | 50 (1.er sem.) y 48,75 (2.º) | 38 |
| **Ponderación tal como se declaró** | Doc 35,7 · Gest 64,3 | Doc 34,0 · Inv 16,0 · VcM 32,0 · Gest 18,0 | Doc 47,4 · Inv 32,9 · VcM 5,3 · Gest 14,5 |
| **Ponderación ordenada** | Doc 21,7 · VcM 5,8 · Gest 72,5 | Doc 33,8 · Inv 16,0 · VcM 32,1 · Gest 18,0 | Doc 47,4 · Inv 38,2 · VcM 10,5 · Gest 3,9 |
| Docencia según el reglamento | 60–70% (vinculador/a) → **bajo el rango** | 40–60% (investigador/a) → **bajo el rango** | 40–60% → dentro |
| Resultado con evaluaciones ficticias | A (96,2%) | A (98,3%), con advertencia de horas | B (83,6%) |

El modelo resuelve los tres sujetos, aunque no se parecen entre sí: uno con 4 tareas en 2 ámbitos y otro con
12 tareas en los 4. Cada ámbito pesa lo que la persona comprometió, así que la gestión vale 72,5% en el sujeto 07
y 3,9% en el sujeto 09.

## 3. Problemas encontrados en lo que se registra

1. **Las horas de docencia no se registran igual.** El sujeto 07 sumó los dos semestres (15 h, en realidad 7,5 h
   semanales). El sujeto 09 anotó "4,5 + 4,5" por curso y en el resumen puso un solo semestre. El sujeto 08 anotó
   cada semestre por separado. Sin una regla común, la docencia del sujeto 07 parece pesar 35,7% cuando pesa 21,7%.
2. **Formato de horas ambiguo.** "16.45" y "3.45" parecen horas y minutos (16 h 45 min), no decimales.
3. **Actividades en el ámbito equivocado.** En Gestión se declaró una representación internacional (que es VcM),
   una revisión de artículos (Investigación) y la organización de un evento académico (VcM). Si se pondera con lo
   declarado, la gestión del sujeto 09 pesa 14,5% en vez de 3,9%.
4. **Actividades sin horas.** Ponencias, asesorías externas, postulaciones a fondos y patentes se declaran sin
   horas. Se pueden evaluar como tareas, pero no aportan ponderación al ámbito.
5. **Horas sobre la jornada.** El sujeto 08 declara unas 50 h semanales en una jornada completa de 44 h.
6. **Carga docente fuera del rango del reglamento.** En dos de los tres sujetos la docencia queda bajo el mínimo
   que fija el reglamento para la jerarquía (art. 18, 19, 23 y 24).
7. **El formulario 2024 no permite ponderar 4 ámbitos.** Quitó las horas por actividad y la sección de gestión,
   y el resumen acepta "horas o porcentaje", lo que mezcla unidades.

## 4. Cómo se calcula la ponderación de cada ámbito

**Regla:** % del ámbito = horas semanales del ámbito ÷ total de horas semanales comprometidas.

- **Horas semanales.** Se ingresan por ámbito. Si la docencia cambia de un semestre a otro, se ingresa una lista
  por semestre (`docencia: [17, 16.75]`) y se promedia.
- **Ámbito.** Cada actividad pertenece al ámbito de su subcategoría en el catálogo SEJA, no a la sección del
  formulario donde se escribió.
- **Ingreso directo.** También se puede ingresar el % de cada ámbito si ya viene calculado (`compromiso:`).
- **Advertencias.** El informe avisa si las horas superan la jornada (44 h completa, 22 h media) o si la docencia
  queda fuera del rango de la jerarquía y el perfil. No bloquea la calificación: deja la observación para la
  comisión.
- **Rango de docencia** (% del compromiso, según el Reglamento de Carrera Académica):

| Jerarquía | Perfil investigador/a | Perfil vinculador/a |
|---|---|---|
| Instructor/a | 60–80 | 60–80 |
| Asistente | 50–70 | 60–70 |
| Asociado/a | 40–60 | 50–60 |
| Titular | 30–50 | 40–60 |

## 5. Recomendaciones para el formulario en UCampus

1. Pedir **horas semanales por semestre** en cada actividad de docencia y **horas semanales** en las demás, y
   calcular el resumen automáticamente en lugar de pedirlo.
2. Agregar **Gestión Académica** como cuarta área, con horas, en el formulario y en el resumen.
3. Elegir el **tipo de actividad desde el catálogo** de subcategorías, para que cada actividad caiga en su ámbito.
4. Usar campos numéricos con decimales (0,5 = media hora), no texto libre.
5. Mostrar al llenar el formulario el **rango de docencia** de la jerarquía y el perfil, y el total frente a la jornada.
6. Pedir el **perfil** (investigador/a o vinculador/a), que el formulario 2023 no tenía.
