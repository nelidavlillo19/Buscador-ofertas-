# Calificación académica SEJA-UMCE

Motor de cálculo de la calificación académica del **Sistema de Evaluación y Jerarquización Académica (SEJA)**,
según el Reglamento de Carrera Académica UMCE (Título III, art. 31–41).

## Modelo

```
TAREA ──(instrumento estandarizado y/o evidencia)──► puntaje 0–100
   │  se promedian dentro de su ámbito
   ▼
ÁMBITO ──► puntaje del ámbito ──► letra del ámbito (A–E)
   │  ponderado por el % declarado en el Compromiso de Desempeño
   ▼
FINAL = 80% Σ (ámbito × % declarado)  +  10% autoevaluación  +  10% evaluación de estudiantes
   ▼
CLASIFICACIÓN: A+ · A · B · C · D · E
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

Cada ámbito tiene además la subcategoría `otra`, para actividades declaradas que no calcen en las anteriores.

### 2. Evaluación de cada tarea

Como cada académico/a declara su propio compromiso, cada tarea indica **cómo** se evalúa:

| Forma | Ejemplo | Puntaje |
|---|---|---|
| Instrumento con escala | `instrumento: {puntaje: 3.6, min: 1, max: 4}` | (3,6 − 1) / (4 − 1) = 86,7 |
| Instrumento en % | `instrumento: {porcentaje: 95}` | 95 |
| Evidencia con meta | `evidencia: {comprometido: 2, logrado: 3, validado: true}` | 100 (tope) + **excedente** |
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

| Letra | Puntaje final | Significado (art. 39–40) |
|---|---|---|
| **A+** | A + excedente validado en ≥ 2 ámbitos | Cumplimiento pleno más excedente acreditado y validado |
| **A** | ≥ 90 | Cumplimiento pleno |
| **B** | ≥ 75 | Cumplimiento bueno |
| **C** | ≥ 60 | Cumplimiento parcial (requiere mejora) |
| **D** | ≥ 40 | Insuficiente |
| **E** | < 40 | Sin cumplimiento o sin evidencia |

Con D o E (o dos C seguidas) el informe recuerda el ingreso al programa de acompañamiento (art. 41).
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

- Umbrales definitivos de cada letra y si la **A** exige además un mínimo en cada ámbito.
- Qué es exactamente la letra **E** (el reglamento llega hasta D).
- Instrumentos estandarizados de cada subcategoría y su escala.
- Factor de corrección por maternidad, licencias y otros contextos (art. 37).
