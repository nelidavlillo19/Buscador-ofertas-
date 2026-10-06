# Calificación académica SEJA-UMCE

Motor de cálculo de la calificación académica del **Sistema de Evaluación y Jerarquización Académica (SEJA)**,
según el Reglamento de Carrera Académica UMCE (Título III, art. 31–41).

## Modelo

```
TAREA ──(instrumento estandarizado y/o evidencia)──► % de cumplimiento
   │  se promedian dentro de su ámbito
   ▼
ÁMBITO ──► % del ámbito ──► letra del ámbito (A+–D)
   │  ponderado por el % declarado en el Compromiso de Desempeño
   ▼
FINAL = 80% Σ (ámbito × % declarado)  +  10% autoevaluación  +  10% evaluación de estudiantes
   ▼
CLASIFICACIÓN: A+ · A · B · C · D
```

### 1. Ámbitos y subcategorías (roles y funciones)

Los cuatro ámbitos del art. 34. Cada uno se divide en subcategorías tomadas del reglamento y de las
definiciones del documento de síntesis SEJA (lista completa en [`config/modelo.yaml`](config/modelo.yaml)):

| Ámbito | Subcategorías (ejemplos) |
|---|---|
| `docencia` | cursos de pregrado y postgrado, dirección de tesis/titulación, prácticas, tutoría, ayudantes, formación de académicos, formación continua |
| `investigacion` (ICI) | proyectos, publicaciones, creación artística, innovación, presentaciones en eventos, redes, postulación a fondos, claustros de postgrado |
| `vinculacion` | iniciativas y proyectos VcM, actividades relevantes (EF, deporte, artes), difusión, redes, extensión |
| `gestion` | dirección/coordinación, gestión curricular, de la investigación, de la VcM, del cuerpo académico, aseguramiento de la calidad, comisiones |

Para cada subcategoría, el catálogo indica también con qué instrumento o evidencia se evalúa y cada cuánto
(semestral, anual o bianual), tomado de la *Jornada Modelo de Evaluación SEJA 2024*. Por ejemplo, la docencia de pregrado
se evalúa con la pauta de estudiantes, la de la dirección de la unidad académica y la autoevaluación (semestral);
un artículo indexado, con la constancia de la revista, la indexación y la copia de la publicación (anual).

Cada ámbito tiene además la subcategoría `otra`, para actividades declaradas que no calcen en las anteriores.

### 2. Evaluación de cada tarea

Como cada académico/a declara su propio compromiso, cada tarea indica **cómo** se evalúa:

| Forma | Ejemplo | Puntaje |
|---|---|---|
| Pauta de afirmaciones (Cumple / No cumple / No aplica) | `instrumento: {cumple: 9, no_cumple: 1, no_aplica: 2}` | 9 / (9 + 1) = 90 (los "no aplica" no cuentan) |
| Instrumento con escala | `instrumento: {puntaje: 3.6, min: 1, max: 4}` | (3,6 − 1) / (4 − 1) = 86,7 |
| Instrumento en % | `instrumento: {porcentaje: 95}` | 95 |
| Evidencia con meta | `evidencia: {comprometido: 2, logrado: 3, validado: true}` | 150 (**excedente validado**) |
| Evidencia con meta, sin validar | `evidencia: {comprometido: 2, logrado: 3}` | 100 (tope) |
| Evidencia por estado | `evidencia: {estado: parcial}` | cumplido 100 · parcial 50 · no cumplido / sin evidencia 0 |

Si una tarea tiene instrumento **y** evidencia, se promedian. `peso` (opcional, por defecto 1) permite que una tarea
cuente más dentro de su ámbito; si no se indica, el ámbito es un promedio simple.

### 3. Ponderación

- **80%**: los ámbitos, cada uno según el % declarado en el Compromiso de Desempeño (los % deben sumar 100).
  Ejemplo: docencia 55%, ICI 30%, VcM 5%, gestión 10% → pesan 44%, 24%, 4% y 8% del total.
- El % de cada ámbito se ingresa directo (`compromiso:`) o se calcula desde las **horas semanales** (`horas:`):
  % = horas del ámbito ÷ total de horas. Si la docencia cambia por semestre se ingresa una lista
  (`docencia: [17, 16.75]`) y se promedia. El informe advierte si las horas superan la jornada
  (`jornada: completa` = 44 h, `media` = 22 h) o si la docencia queda fuera del rango del reglamento para la
  jerarquía y el perfil (`jerarquia:`, `perfil:`). Ver [el análisis de los compromisos](docs/analisis_compromisos.md).
- **10%**: autoevaluación.
- **10%**: evaluación de los estudiantes.
- Si la persona está eximida de docencia (art. 37 a), se marca `exento_estudiantes: true` y ese 10% pasa a los ámbitos.

### 4. Clasificación

| Letra | % de cumplimiento final | Significado |
|---|---|---|
| **A+** | ≥ 101% | Sobresaliente: cumplimiento sobre lo comprometido |
| **A** | 90% a 100% | Cumplimiento pleno |
| **B** | 75% a 89% | Cumplimiento bueno |
| **C** | 55% a 74% | Cumplimiento parcial (requiere mejora) |
| **D** | menos de 55% | Insuficiente |

Sobre 100% sólo se llega con excedentes validados (`validado: true`); un excedente sin validar cuenta como 100%.

**Tope y reconocimiento institucional.** Una tarea con excedente validado cuenta como máximo **120%**
(`tope_excedente`). Lo que pase de ahí no sube la calificación, pero queda registrado: el informe lista
**en qué destaca** la persona (tarea, subcategoría y % real de cumplimiento). En el JSON va en
`reconocimiento_institucional`, para el reconocimiento institucional. Con A+ el informe indica además que la
persona es candidata a reconocimiento.
La autoevaluación y la evaluación de estudiantes llegan como máximo a 100%.

El informe entrega además la **escala numérica 1–7** según la tabla de equivalencia de la Jornada 2024:
90–100% → 7 · 80–89% → 6 · 70–79% → 5 · 60–69% → 4 · 50–59% → 3 · 40–49% → 2 · 39% o menos → 1.

Con D (o dos C seguidas) el informe recuerda el ingreso al programa de acompañamiento (art. 41).

### 5. Situaciones especiales (art. 37)

```yaml
situacion_especial:
  motivo: enfermedad        # enfermedad, maternidad, parental, permiso_sin_goce, comision_servicio,
                            # cargo_directivo, estudios u otra
  meses_ausencia: 6
  porcentaje_jornada: 60    # % de la jornada comprometida que dedicó a sus funciones
  detalle: texto libre
```

- **Ausencia de más de 5 meses por enfermedad o maternidad:** la evaluación se **suspende**. No hay letra ni
  puntaje.
- **Cualquier otra situación** (incluidas las ausencias de 5 meses o menos): se evalúa en relación al
  `porcentaje_jornada`. Las metas con evidencia se ajustan a ese % (por ejemplo, 2 publicaciones al 50% → 1).
  El excedente se cuenta sólo si lo logrado supera la meta original.
- **En ambos casos** el informe indica que se debe informar a la Oficina de Evaluación de Desempeño Académico y
  a las autoridades correspondientes (campo `informar_a` en el JSON).
Los umbrales y pesos se cambian en [`config/modelo.yaml`](config/modelo.yaml), sin tocar el código.

## Uso

Cada académico/a es un archivo YAML (ver [`ejemplos/`](ejemplos)):

```bash
python -m seja seja/ejemplos/asistente_investigadora.yaml          # informe en texto
python -m seja seja/ejemplos/*.yaml --json                          # JSON (para UCampus u otro sistema)
```

Desde Python:

```python
from seja import calificar, informe
resultado = calificar(datos)   # datos: dict con compromiso, tareas, autoevaluacion, estudiantes
print(resultado.letra, resultado.puntaje)
```

La **calculadora web** [`web/calculadora.html`](web/calculadora.html) aplica el mismo modelo en el navegador, con
un caso de ejemplo editable.

Pruebas: `python -m pytest -q tests/test_seja.py`

## Definiciones vigentes frente a la Jornada 2024

La Jornada 2024 es anterior a las definiciones actuales. De ella se toman la pauta Cumple / No cumple / No aplica,
la tabla de equivalencia a la escala 1–7 y el catálogo de instrumentos y periodicidad. Prevalecen las
definiciones actuales en:

- **Ámbitos**: son 4, incluida la **Gestión Académica** (la Jornada 2024 evaluaba 3).
- **Ponderación**: 10% autoevaluación + 10% estudiantes + 80% compromiso (la Jornada 2024 indicaba 15/15/70).
- **Letras**: A+ desde 101% de cumplimiento (la Jornada 2024 asignaba A+ a la nota 7, es decir desde 90%).

## Pendiente de definir

- Si la **A** exige además un mínimo en cada ámbito.
- Valor definitivo del tope de excedente (hoy 120%).
- Si el permiso postnatal parental también suspende la evaluación cuando supera los 5 meses (hoy sólo
  enfermedad y maternidad).
- Instrumentos estandarizados de cada subcategoría y su escala.
