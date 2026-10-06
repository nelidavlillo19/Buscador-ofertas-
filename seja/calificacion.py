"""Motor de calificación académica SEJA-UMCE.

Flujo (Reglamento de Carrera Académica, Título III):

1. Cada TAREA del Compromiso de Desempeño se evalúa con un instrumento estandarizado
   y/o con la evidencia del compromiso → puntaje 0–100.
2. Las tareas se PROMEDIAN dentro de su ámbito → puntaje del ámbito, que se califica (A–E).
3. Los ámbitos se ponderan según el % declarado en el compromiso y ocupan el 80% del total;
   la autoevaluación y la evaluación de estudiantes aportan un 10% fijo cada una.
4. El % de cumplimiento final se clasifica en A+ (desde 101%, sobresaliente), A, B, C o D.

Los excedentes validados (logrado > comprometido) cuentan sobre 100%; sin validar, se topan en 100%.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

MODELO = Path(__file__).parent / "config" / "modelo.yaml"


class ErrorCompromiso(ValueError):
    """Los datos del compromiso o de las evaluaciones no son válidos."""


def cargar_modelo(ruta: Path | str = MODELO) -> dict:
    return yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))


@dataclass
class ResultadoTarea:
    ambito: str
    subcategoria: str
    descripcion: str
    puntaje: float
    peso: float
    excedente: bool
    detalle: str


@dataclass
class ResultadoAmbito:
    ambito: str
    nombre: str
    ponderacion: float  # fracción del total final (ya incluye el 80%)
    declarado: float  # % declarado en el compromiso
    puntaje: float
    letra: str
    excedente: bool
    tareas: list[ResultadoTarea] = field(default_factory=list)


@dataclass
class Resultado:
    academico: str
    periodo: str
    ambitos: list[ResultadoAmbito]
    autoevaluacion: float
    ponderacion_autoevaluacion: float
    estudiantes: float | None
    ponderacion_estudiantes: float
    puntaje: float
    letra: str
    descripcion: str
    observaciones: list[str]
    nota: int  # escala numérica 1–7 según la tabla de equivalencia

    def como_dict(self) -> dict:
        return {
            "academico": self.academico,
            "periodo": self.periodo,
            "puntaje": self.puntaje,
            "nota": self.nota,
            "letra": self.letra,
            "descripcion": self.descripcion,
            "autoevaluacion": {"puntaje": self.autoevaluacion,
                               "ponderacion": self.ponderacion_autoevaluacion},
            "estudiantes": {"puntaje": self.estudiantes,
                            "ponderacion": self.ponderacion_estudiantes},
            "ambitos": [
                {"ambito": a.ambito, "nombre": a.nombre, "declarado": a.declarado,
                 "ponderacion": a.ponderacion, "puntaje": a.puntaje, "letra": a.letra,
                 "excedente": a.excedente,
                 "tareas": [t.__dict__ for t in a.tareas]}
                for a in self.ambitos
            ],
            "observaciones": self.observaciones,
        }


def escalar(datos: dict, contexto: str) -> float:
    """Lleva un puntaje de instrumento a 0–100.

    Acepta ``{porcentaje: 85}``, ``{puntaje: 6.2, min: 1, max: 7}`` o una pauta de afirmaciones
    ``{cumple: 9, no_cumple: 1, no_aplica: 2}`` (los "no aplica" no cuentan).
    """
    if "cumple" in datos or "no_cumple" in datos:
        cumple, no_cumple = int(datos.get("cumple", 0)), int(datos.get("no_cumple", 0))
        if cumple < 0 or no_cumple < 0 or int(datos.get("no_aplica", 0)) < 0:
            raise ErrorCompromiso(f"{contexto}: las cantidades de la pauta no pueden ser negativas")
        if cumple + no_cumple == 0:
            raise ErrorCompromiso(f"{contexto}: la pauta no tiene afirmaciones aplicables")
        return cumple / (cumple + no_cumple) * 100
    if "porcentaje" in datos:
        valor = float(datos["porcentaje"])
        if not 0 <= valor <= 100:
            raise ErrorCompromiso(f"{contexto}: el porcentaje debe estar entre 0 y 100")
        return valor
    try:
        puntaje, minimo, maximo = float(datos["puntaje"]), float(datos["min"]), float(datos["max"])
    except KeyError as e:
        raise ErrorCompromiso(f"{contexto}: falta '{e.args[0]}' (usa porcentaje, puntaje/min/max o cumple/no_cumple)")
    if maximo <= minimo or not minimo <= puntaje <= maximo:
        raise ErrorCompromiso(f"{contexto}: puntaje {puntaje} fuera de la escala {minimo}–{maximo}")
    return (puntaje - minimo) / (maximo - minimo) * 100


def evaluar_evidencia(datos: dict, modelo: dict, contexto: str) -> tuple[float, bool, str]:
    """% de cumplimiento según la evidencia (sobre 100 sólo con excedente validado) y si hay excedente."""
    validado = bool(datos.get("validado", False))
    if "comprometido" in datos:
        comprometido, logrado = float(datos["comprometido"]), float(datos.get("logrado", 0))
        if comprometido <= 0 or logrado < 0:
            raise ErrorCompromiso(f"{contexto}: 'comprometido' debe ser mayor que 0 y 'logrado' no negativo")
        excedente = logrado > comprometido and validado
        puntaje = (logrado / comprometido if excedente else min(logrado / comprometido, 1)) * 100
        detalle = f"evidencia {logrado:g}/{comprometido:g}"
        if logrado > comprometido and not validado:
            detalle += ", excedente sin validar: se considera 100"
        return puntaje, excedente, detalle
    estado = datos.get("estado")
    estados = modelo["estados_evidencia"]
    if estado not in estados:
        raise ErrorCompromiso(f"{contexto}: estado de evidencia '{estado}' no válido ({', '.join(estados)})")
    return float(estados[estado]), bool(datos.get("excedente")) and validado, f"evidencia {estado}"


def nombre_subcategoria(datos: str | dict) -> str:
    return datos["nombre"] if isinstance(datos, dict) else datos


def a_escala_numerica(puntaje: float, modelo: dict) -> int:
    for minimo, nota in modelo["escala_numerica"]:
        if puntaje >= minimo:
            return nota
    return modelo["escala_numerica"][-1][1]


def evaluar_tarea(tarea: dict, modelo: dict, n: int) -> ResultadoTarea:
    ambito, sub = tarea.get("ambito"), tarea.get("subcategoria")
    contexto = f"Tarea {n} ({tarea.get('descripcion', sub)})"
    if ambito not in modelo["ambitos"]:
        raise ErrorCompromiso(f"{contexto}: ámbito '{ambito}' no existe ({', '.join(modelo['ambitos'])})")
    subcategorias = modelo["ambitos"][ambito]["subcategorias"]
    if sub not in subcategorias:
        raise ErrorCompromiso(f"{contexto}: subcategoría '{sub}' no existe en {ambito} ({', '.join(subcategorias)})")

    # La tarea se evalúa por instrumento y/o evidencia: si hay ambos, se promedian.
    puntajes, detalles, excedente = [], [], False
    if "instrumento" in tarea:
        puntajes.append(escalar(tarea["instrumento"], contexto))
        detalles.append(f"instrumento {tarea['instrumento'].get('nombre', '')}".strip())
    if "evidencia" in tarea:
        puntaje, excedente, detalle = evaluar_evidencia(tarea["evidencia"], modelo, contexto)
        puntajes.append(puntaje)
        detalles.append(detalle)
    if not puntajes:
        raise ErrorCompromiso(f"{contexto}: debe tener 'instrumento' y/o 'evidencia'")

    peso = float(tarea.get("peso", 1))
    if peso <= 0:
        raise ErrorCompromiso(f"{contexto}: el peso debe ser mayor que 0")
    return ResultadoTarea(ambito, sub, tarea.get("descripcion", nombre_subcategoria(subcategorias[sub])),
                          round(sum(puntajes) / len(puntajes), 2), peso, excedente, " + ".join(detalles))


def clasificar(puntaje: float, modelo: dict) -> str:
    letras = list(modelo["umbrales"])
    for letra in letras:
        if puntaje >= modelo["umbrales"][letra]:
            return letra
    return letras[-1]


def calificar(datos: dict, modelo: dict | None = None) -> Resultado:
    modelo = modelo or cargar_modelo()
    observaciones: list[str] = []

    # 1. Ponderación declarada en el compromiso (% de la carga por ámbito).
    declarado = {k: float(v) for k, v in (datos.get("compromiso") or {}).items() if float(v) > 0}
    for ambito in declarado:
        if ambito not in modelo["ambitos"]:
            raise ErrorCompromiso(f"Compromiso: ámbito '{ambito}' no existe ({', '.join(modelo['ambitos'])})")
    if not declarado:
        raise ErrorCompromiso("El compromiso debe declarar el % de al menos un ámbito")
    if abs(sum(declarado.values()) - 100) > 0.01:
        raise ErrorCompromiso(f"Los % declarados en el compromiso suman {sum(declarado.values()):g}, deben sumar 100")

    # 2. Componentes fijos. Si la persona está eximida de docencia (art. 37 a) no hay
    #    evaluación de estudiantes y su 10% se suma a los ámbitos del compromiso.
    fijos = modelo["componentes_fijos"]
    auto = escalar(datos.get("autoevaluacion") or {}, "Autoevaluación")
    p_auto, p_est = fijos["autoevaluacion"], fijos["estudiantes"]
    est = None
    if datos.get("estudiantes") is not None:
        est = escalar(datos["estudiantes"], "Evaluación de estudiantes")
    elif datos.get("exento_estudiantes"):
        observaciones.append("Sin evaluación de estudiantes (eximido/a de docencia): su ponderación se "
                             "redistribuye entre los ámbitos del compromiso.")
        p_est = 0.0
    else:
        raise ErrorCompromiso("Falta la evaluación de estudiantes (o indica exento_estudiantes: true)")
    p_compromiso = 1 - p_auto - p_est

    # 3. Tareas → promedio por ámbito.
    tareas = [evaluar_tarea(t, modelo, i) for i, t in enumerate(datos.get("tareas") or [], 1)]
    ambitos = []
    for clave, pct in declarado.items():
        propias = [t for t in tareas if t.ambito == clave]
        if propias:
            puntaje = sum(t.puntaje * t.peso for t in propias) / sum(t.peso for t in propias)
        else:
            puntaje = 0.0
            observaciones.append(f"{modelo['ambitos'][clave]['nombre']}: declarado en el compromiso "
                                 "pero sin tareas evaluadas (puntaje 0).")
        puntaje = round(puntaje, 2)
        ambitos.append(ResultadoAmbito(clave, modelo["ambitos"][clave]["nombre"],
                                       round(p_compromiso * pct / 100, 4), pct, puntaje,
                                       clasificar(puntaje, modelo), any(t.excedente for t in propias),
                                       propias))
    for t in tareas:
        if t.ambito not in declarado:
            observaciones.append(f"'{t.descripcion}' pertenece a {t.ambito}, que no tiene % en el "
                                 "compromiso: no se considera en la calificación.")

    # 4. Puntaje final y clasificación.
    total = sum(a.puntaje * a.ponderacion for a in ambitos) + auto * p_auto + (est or 0) * p_est
    total = round(total, 1)
    letra = clasificar(total, modelo)
    if letra == "D":
        observaciones.append("Ingresa al programa institucional de acompañamiento y fortalecimiento "
                             "académico (art. 41; también tras dos C consecutivas).")

    return Resultado(str(datos.get("academico", "")), str(datos.get("periodo", "")), ambitos,
                     round(auto, 2), p_auto, None if est is None else round(est, 2), p_est,
                     total, letra, modelo["descripcion_letras"][letra], observaciones,
                     a_escala_numerica(total, modelo))


def informe(r: Resultado) -> str:
    """Informe en texto para revisar o adjuntar al expediente académico."""
    lineas = [f"Calificación académica SEJA — {r.academico} ({r.periodo})", "=" * 60]
    for a in r.ambitos:
        lineas.append(f"\n{a.nombre}  [declarado {a.declarado:g}% → pondera {a.ponderacion:.1%}]")
        for t in a.tareas:
            extra = " ★ excedente validado" if t.excedente else ""
            peso = f" ×{t.peso:g}" if t.peso != 1 else ""
            lineas.append(f"  · [{t.subcategoria}] {t.descripcion}: {t.puntaje:.1f}{peso} ({t.detalle}){extra}")
        lineas.append(f"  Promedio del ámbito: {a.puntaje:.1f} → {a.letra}")
    lineas.append(f"\nAutoevaluación: {r.autoevaluacion:.1f}  [pondera {r.ponderacion_autoevaluacion:.0%}]")
    if r.estudiantes is not None:
        lineas.append(f"Evaluación de estudiantes: {r.estudiantes:.1f}  [pondera {r.ponderacion_estudiantes:.0%}]")
    lineas += ["-" * 60, f"CUMPLIMIENTO FINAL: {r.puntaje:.1f}%  (escala numérica {r.nota})",
               f"CLASIFICACIÓN: {r.letra} — {r.descripcion}"]
    if r.observaciones:
        lineas += ["", "Observaciones:"] + [f"  - {o}" for o in r.observaciones]
    return "\n".join(lineas)
