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
(semestral, anual o bianual), tomado de la *Jornada Modelo de Evaluación SEJA 2025*. Por ejemplo, la docencia de pregrado
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
- **10%**: autoevaluación.
- **10%**: evaluación de los estudiantes.
- Si la persona está eximida de docencia (art. 37 a), se marca `exento_estudiantes: true` y ese 10% pasa a los ámbitos.

### 4. Clasificación (umbrales provisorios)

| Letra | % de cumplimiento final | Significado |
|---|---|---|
| **A+** | ≥ 101% | Sobresaliente: cumplimiento sobre lo comprometido |
| **A** | ≥ 90% | Cumplimiento pleno |
| **B** | ≥ 75% | Cumplimiento bueno |
| **C** | ≥ 60% | Cumplimiento parcial (requiere mejora) |
| **D** | < 60% | Insuficiente |

Sobre 100% sólo se llega con excedentes validados (`validado: true`); un excedente sin validar cuenta como 100%.
La autoevaluación y la evaluación de estudiantes llegan como máximo a 100%.

El informe entrega además la **escala numérica 1–7** según la tabla de equivalencia de la Jornada 2025:
90–100% → 7 · 80–89% → 6 · 70–79% → 5 · 60–69% → 4 · 50–59% → 3 · 40–49% → 2 · 39% o menos → 1.

Con D (o dos C seguidas) el informe recuerda el ingreso al programa de acompañamiento (art. 41).
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

## Pendiente de definir

- **Ponderación de los componentes fijos**: este modelo usa 10% autoevaluación + 10% estudiantes + 80% compromiso;
  la Jornada 2025 indica 15% + 15% + 70% (unidad académica y otras unidades). Se cambia en `componentes_fijos`.
- **Letras según la escala numérica**: la Jornada 2025 asigna A+ = 7, A = 6, B = 5, C = 4 y D = 1–3
  (A+ desde 90%), mientras que este modelo usa A+ desde 101%.

- Umbrales definitivos de A, B y C, y si la **A** exige además un mínimo en cada ámbito.
- Si el excedente de una tarea tiene un tope (hoy 3 publicaciones sobre 2 comprometidas valen 150%).
- Instrumentos estandarizados de cada subcategoría y su escala.
- Factor de corrección por maternidad, licencias y otros contextos (art. 37).
