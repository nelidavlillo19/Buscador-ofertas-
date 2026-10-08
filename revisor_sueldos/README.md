# Revisor de planillas de sueldo universitarias

Herramienta para revisar las planillas de remuneraciones que las universidades estatales publican en
**Transparencia Activa** (planta, contrata, honorarios y Código del Trabajo) y:

1. **Costear** cada grupo de trabajadores — académicos, directivos, profesionales, técnicos, administrativos
   y auxiliares — por mes, por año y por tipo de contrato (dotación, masa bruta, costo empleador,
   promedio, mediana, P10/P90).
2. **Revisar hacia atrás**: sigue a cada persona entre cortes anuales y calcula **tasas de ascenso**
   (grado EUS, jerarquía académica o cambio a un estamento superior), el **premio** salarial del ascenso,
   pasos a planta, ingresos y egresos.
3. **Proyectar** la implementación de un **nuevo sistema de jerarquización y evaluación**: encasillamiento en
   niveles, nivelación gradual a pisos, ascensos según evaluación e incentivos, comparado año a año con el
   escenario sin reforma.
4. Marcar **hallazgos de revisión**: brutos en cero, doble vínculo, estamentos no reconocidos, planta/contrata
   sin grado y remuneraciones atípicas frente a pares de igual grado.

## Uso

```bash
pip install PyYAML openpyxl

# 1) ver cómo funciona con planillas ficticias
python -m revisor_sueldos ejemplo

# 2) con las planillas reales (archivos o carpetas; CSV o Excel)
python -m revisor_sueldos analizar planillas_sueldos/ --salida informe_sueldos
```

Salidas en la carpeta indicada:

- `informe.html` — informe navegable (KPIs, gráficos, tablas).
- `revision_sueldos.xlsx` — todas las tablas: costeo anual/mensual/por contrato, tasas de ascenso,
  movimientos individuales, proyección por grupo y por nivel, supuestos, encasillamiento y hallazgos.

`planillas_sueldos/` e `informe_sueldos*/` están en `.gitignore` para que los datos personales no se suban al repositorio.

## Formato de las planillas

Se reconocen automáticamente los encabezados habituales del Portal de Transparencia (aunque vengan con filas de
título antes): *Año, Mes, Estamento, Apellido paterno, Apellido materno, Nombres, Grado EUS o jornada,
Calificación profesional, Cargo o función, Remuneración bruta mensualizada, Remuneración líquida…*

- Si la planilla no trae Año/Mes, se toman del nombre del archivo u hoja: `planta_marzo_2025.csv`,
  `contrata_2026-07.xlsx`.
- El tipo de contrato se toma de una columna "tipo/calidad jurídica" o del nombre del archivo
  (`planta`, `contrata`, `honorarios`, `codigo_del_trabajo`).
- Montos en formato chileno (`$ 1.234.567`) o numérico; CSV con `;` o `,`, UTF-8 o Latin-1.

## Configuración (`config/revisor_sueldos.yaml`)

| Sección | Para qué |
|---|---|
| `grupos` | Patrones que asignan cada estamento/cargo a un grupo (el orden importa). |
| `jerarquias_academicas` | Jerarquías reconocidas y su rango (instructor < asistente < asociado < titular). |
| `costo_empleador` | % de aportes del empleador por tipo de contrato. |
| `trayectorias` | Mes de corte anual y orden de estamentos para considerar un cambio como ascenso. |
| `proyeccion` | Horizonte, reajuste, gradualidad, garantía de no disminución, tasas de ascenso (históricas o fijas). |
| `proyeccion.evaluacion` | Distribución esperada de calificaciones, % de incentivo y efecto sobre la tasa de ascenso. |
| `proyeccion.jerarquizacion` | Niveles del nuevo sistema por grupo, criterio de encasillamiento (jerarquía, grado o percentil) y piso de cada nivel. |

Los pisos, porcentajes y factores del archivo son **valores de ejemplo** que deben reemplazarse por la propuesta
institucional y validarse con Finanzas y Recursos Humanos.

## Cómo se calcula

- **Tasa de ascenso** = ascendidos / personas presentes en ambos cortes, anualizada si los cortes no distan 12 meses.
  Las personas se siguen por nombre completo normalizado (Transparencia no publica RUT).
- **Proyección** (valor esperado, dotación constante): cada persona parte en su nivel; su remuneración objetivo es
  `máx(actual × (1 + incremento), piso × jornada/44)`; la brecha se cierra según `gradualidad`; cada año una fracción
  `tasa de ascenso × efecto de la evaluación` sube un nivel (con al menos el premio histórico); el incentivo por
  evaluación se suma sobre la masa anual. El escenario **sin reforma** usa la misma escala de niveles con la tasa y el
  premio históricos, para que la diferencia refleje sólo el nuevo sistema.
