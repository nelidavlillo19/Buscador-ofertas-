"""Motor de calificación académica SEJA-UMCE.

Flujo (Reglamento de Carrera Académica, Título III):

1. Cada TAREA del Compromiso de Desempeño se evalúa con un instrumento estandarizado
   y/o con la evidencia del compromiso → puntaje 0–100.
2. Las tareas se PROMEDIAN dentro de su ámbito → puntaje del ámbito, que se califica (A+–D).
3. Los ámbitos se ponderan según el % declarado en el compromiso y ocupan el 80% del total;
   la autoevaluación y la evaluación de estudiantes aportan un 10% fijo cada una.
4. El % de cumplimiento final se clasifica en A+ (desde 101%, sobresaliente), A, B, C o D.

Los excedentes validados (logrado > comprometido) cuentan sobre 100% hasta un tope por tarea, y quedan
registrados como destacados para el reconocimiento institucional; sin validar, se topan en 100%.

Situaciones especiales (art. 37): una ausencia justificada de más de 5 meses continuos suspende la
evaluación; en los demás casos las metas se ajustan al % de la jornada dedicado a sus funciones. En ambos
casos se informa a la Oficina de Evaluación de Desempeño Académico y a las autoridades correspondientes.
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
    puntaje: float  # el que se promedia (con el tope de excedente aplicado)
    peso: float
    excedente: bool
    detalle: str
    cumplimiento_real: float  # sin tope: es el que se registra para el reconocimiento
    destaca: bool = False  # excedente validado o avance validado más allá de la etapa comprometida
    mecanismo: str = ""  # mecanismo de evidencia (declarado o el del catálogo)
    comprometido: str = ""  # lo comprometido y lo evidenciado, en texto (etapa, meta o instrumento)
    evidenciado: str = ""


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
class Destacado:
    """Tarea con excedente validado: se registra para el reconocimiento institucional."""
    ambito: str
    subcategoria: str
    descripcion: str
    detalle: str
    cumplimiento_real: float


@dataclass
class Resultado:
    academico: str
    periodo: str
    estado: str  # "calificada" o "suspendida"
    puntaje: float | None
    letra: str | None
    descripcion: str
    nota: int | None  # escala numérica 1–7 según la tabla de equivalencia
    observaciones: list[str]
    ambitos: list[ResultadoAmbito] = field(default_factory=list)
    autoevaluacion: float | None = None
    ponderacion_autoevaluacion: float = 0.0
    estudiantes: float | None = None
    ponderacion_estudiantes: float = 0.0
    destacados: list[Destacado] = field(default_factory=list)
    situacion_especial: str | None = None
    informar_a: str | None = None

    def como_dict(self) -> dict:
        return {
            "academico": self.academico,
            "periodo": self.periodo,
            "estado": self.estado,
            "puntaje": self.puntaje,
            "nota": self.nota,
            "letra": self.letra,
            "descripcion": self.descripcion,
            "situacion_especial": self.situacion_especial,
            "informar_a": self.informar_a,
            "autoevaluacion": {"puntaje": self.autoevaluacion,
                               "ponderacion": self.ponderacion_autoevaluacion},
            "estudiantes": {"puntaje": self.estudiantes,
                            "ponderacion": self.ponderacion_estudiantes},
            "ambitos": [
                {"ambito": a.ambito, "nombre": a.nombre, "declarado": round(a.declarado, 2),
                 "ponderacion": a.ponderacion, "puntaje": a.puntaje, "letra": a.letra,
                 "excedente": a.excedente,
                 "tareas": [t.__dict__ for t in a.tareas]}
                for a in self.ambitos
            ],
            "reconocimiento_institucional": [d.__dict__ for d in self.destacados],
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


def evaluar_evidencia(datos: dict, modelo: dict, contexto: str,
                      factor: float = 1.0) -> tuple[float, bool, str, dict]:
    """% de cumplimiento según la evidencia y si hay un excedente validado sobre lo comprometido.

    ``factor`` ajusta la meta al % de la jornada dedicado a las funciones (art. 37). El excedente
    se cuenta sólo cuando lo logrado supera la meta original, no la ajustada.
    """
    validado = bool(datos.get("validado", False))
    if "etapa_comprometida" in datos:
        return evaluar_etapa(datos, modelo, contexto, validado)
    if "comprometido" in datos:
        comprometido, logrado = float(datos["comprometido"]), float(datos.get("logrado", 0))
        if comprometido <= 0 or logrado < 0:
            raise ErrorCompromiso(f"{contexto}: 'comprometido' debe ser mayor que 0 y 'logrado' no negativo")
        meta = comprometido * factor
        excedente = logrado > comprometido and validado
        puntaje = (logrado / meta if excedente else min(logrado / meta, 1)) * 100
        detalle = f"evidencia {logrado:g}/{comprometido:g}"
        if factor != 1:
            detalle += f" (meta ajustada a {meta:g} por jornada al {factor:.0%})"
        if logrado > comprometido and not validado:
            detalle += ", excedente sin validar: se considera 100"
        return puntaje, excedente, detalle, {"destaca": excedente, "comprometido": f"{comprometido:g}",
                                             "evidenciado": f"{logrado:g}"}
    estado = datos.get("estado")
    estados = modelo["estados_evidencia"]
    if estado not in estados:
        raise ErrorCompromiso(f"{contexto}: estado de evidencia '{estado}' no válido ({', '.join(estados)})")
    excedente = bool(datos.get("excedente")) and validado
    return float(estados[estado]), excedente, f"evidencia {estado}", {
        "destaca": excedente, "comprometido": "Cumplimiento", "evidenciado": estado.replace("_", " ").capitalize()}


def evaluar_etapa(datos: dict, modelo: dict, contexto: str, validado: bool) -> tuple[float, bool, str, dict]:
    """Compara la etapa comprometida con la evidenciada dentro de su secuencia (proyecto, publicación…)."""
    reglas = modelo["etapas"]
    comprometida, evidenciada = datos["etapa_comprometida"], datos.get("etapa_evidenciada")
    nombres = reglas["nombres"]
    extra = {"destaca": False, "comprometido": nombres.get(comprometida, comprometida),
             "evidenciado": nombres.get(evidenciada, evidenciada) if evidenciada else "Sin evidencia"}
    if not evidenciada:
        return 0.0, False, "sin evidencia", extra
    secuencia = next((sec for sec in reglas["secuencias"].values()
                      if comprometida in sec and evidenciada in sec), None)
    if secuencia is None:
        validas = "; ".join(f"{k}: {', '.join(v)}" for k, v in reglas["secuencias"].items())
        raise ErrorCompromiso(f"{contexto}: las etapas '{comprometida}' y '{evidenciada}' no están en una misma "
                              f"secuencia ({validas})")
    avance = secuencia.index(evidenciada) - secuencia.index(comprometida)
    detalle = f"etapa {extra['comprometido']} → {extra['evidenciado']}"
    if avance < 0:
        return float(reglas["etapa_anterior"]), False, detalle + " (etapa anterior a la comprometida)", extra
    extra["destaca"] = avance > 0 and validado
    return 100.0, False, detalle, extra


def nombre_subcategoria(datos: str | dict) -> str:
    return datos["nombre"] if isinstance(datos, dict) else datos


def a_escala_numerica(puntaje: float, modelo: dict) -> int:
    for minimo, nota in modelo["escala_numerica"]:
        if puntaje >= minimo:
            return nota
    return modelo["escala_numerica"][-1][1]


def evaluar_tarea(tarea: dict, modelo: dict, n: int, factor: float = 1.0) -> ResultadoTarea:
    ambito, sub = tarea.get("ambito"), tarea.get("subcategoria")
    contexto = f"Tarea {n} ({tarea.get('descripcion', sub)})"
    if ambito not in modelo["ambitos"]:
        raise ErrorCompromiso(f"{contexto}: ámbito '{ambito}' no existe ({', '.join(modelo['ambitos'])})")
    subcategorias = modelo["ambitos"][ambito]["subcategorias"]
    if sub not in subcategorias:
        raise ErrorCompromiso(f"{contexto}: subcategoría '{sub}' no existe en {ambito} ({', '.join(subcategorias)})")

    # La tarea se evalúa por instrumento y/o evidencia: si hay ambos, se promedian.
    puntajes, detalles, excedente, extra = [], [], False, {}
    if "instrumento" in tarea:
        puntajes.append(escalar(tarea["instrumento"], contexto))
        detalles.append(f"instrumento {tarea['instrumento'].get('nombre', '')}".strip())
    if "evidencia" in tarea:
        puntaje, excedente, detalle, extra = evaluar_evidencia(tarea["evidencia"], modelo, contexto, factor)
        puntajes.append(puntaje)
        detalles.append(detalle)
    if not puntajes:
        raise ErrorCompromiso(f"{contexto}: debe tener 'instrumento' y/o 'evidencia'")

    peso = float(tarea.get("peso", 1))
    if peso <= 0:
        raise ErrorCompromiso(f"{contexto}: el peso debe ser mayor que 0")
    real = sum(puntajes) / len(puntajes)
    tope = modelo["tope_excedente"]
    detalle = " + ".join(detalles)
    if real > tope:
        detalle += f"; cumplimiento real {real:.0f}%, cuenta con tope de {tope:g}%"
    catalogo = subcategorias[sub] if isinstance(subcategorias[sub], dict) else {}
    mecanismo = (tarea.get("evidencia") or {}).get("mecanismo") or (tarea.get("instrumento") or {}).get("nombre") \
        or catalogo.get("instrumento", "")
    return ResultadoTarea(ambito, sub, tarea.get("descripcion", nombre_subcategoria(subcategorias[sub])),
                          round(min(real, tope), 2), peso, excedente, detalle, round(real, 2),
                          extra.get("destaca", excedente), mecanismo,
                          extra.get("comprometido", "Instrumento"), extra.get("evidenciado", f"{real:.0f}%"))


def clasificar(puntaje: float, modelo: dict) -> str:
    letras = list(modelo["umbrales"])
    for letra in letras:
        if puntaje >= modelo["umbrales"][letra]:
            return letra
    return letras[-1]


def horas_semanales(valor, contexto: str) -> float:
    """Horas semanales de un ámbito: un número, o una lista por semestre (se promedia)."""
    valores = valor if isinstance(valor, list) else [valor]
    try:
        horas = [float(v) for v in valores]
    except (TypeError, ValueError):
        raise ErrorCompromiso(f"{contexto}: las horas deben ser números (o una lista por semestre)")
    if not horas or any(h < 0 for h in horas):
        raise ErrorCompromiso(f"{contexto}: las horas no pueden ser negativas")
    return sum(horas) / len(horas)


def ponderacion_compromiso(datos: dict, modelo: dict, observaciones: list[str]) -> dict[str, float]:
    """% de cada ámbito: declarado directamente (``compromiso``) o calculado desde ``horas``."""
    if datos.get("compromiso") and datos.get("horas"):
        raise ErrorCompromiso("Indica la ponderación en 'compromiso' (%) o en 'horas', no en ambos")
    if datos.get("horas"):
        horas = {k: horas_semanales(v, f"Horas de {k}") for k, v in datos["horas"].items()}
        horas = {k: h for k, h in horas.items() if h > 0}
        total = sum(horas.values())
        declarado = {k: h / total * 100 for k, h in horas.items()} if total else {}
        jornada = modelo["horas_jornada"].get(str(datos.get("jornada", "")).lower())
        if jornada and total > jornada:
            observaciones.append(f"Las horas declaradas ({total:.1f} h semanales) superan la jornada "
                                 f"{datos['jornada']} ({jornada} h).")
    else:
        declarado = {k: float(v) for k, v in (datos.get("compromiso") or {}).items() if float(v) > 0}
    for ambito in declarado:
        if ambito not in modelo["ambitos"]:
            raise ErrorCompromiso(f"Compromiso: ámbito '{ambito}' no existe ({', '.join(modelo['ambitos'])})")
    if not declarado:
        raise ErrorCompromiso("El compromiso debe declarar el % o las horas de al menos un ámbito")
    if abs(sum(declarado.values()) - 100) > 0.01:
        raise ErrorCompromiso(f"Los % declarados en el compromiso suman {sum(declarado.values()):g}, deben sumar 100")

    # Carga docente esperada según jerarquía y perfil (Reglamento de Carrera Académica, Título II).
    jerarquia, perfil = str(datos.get("jerarquia", "")).lower(), str(datos.get("perfil", "")).lower()
    rango = modelo["carga_docente"].get(jerarquia, {})
    rango = rango.get(perfil) or rango.get("todos")
    docencia = declarado.get("docencia", 0)
    if rango and not rango[0] <= round(docencia, 1) <= rango[1]:
        observaciones.append(f"La docencia pesa {docencia:.1f}% del compromiso; para {jerarquia} "
                             f"{perfil} el reglamento indica entre {rango[0]}% y {rango[1]}%.")
    return declarado


def situacion_especial(datos: dict, modelo: dict) -> tuple[bool, float, str | None]:
    """Art. 37: (¿se suspende la evaluación?, factor de jornada, descripción de la situación)."""
    sit = datos.get("situacion_especial")
    if not sit:
        return False, 1.0, None
    reglas = modelo["situaciones_especiales"]
    motivo = str(sit.get("motivo", "")).lower()
    if motivo not in reglas["motivos"]:
        raise ErrorCompromiso(f"Situación especial: motivo '{motivo}' no válido ({', '.join(reglas['motivos'])})")
    meses = float(sit.get("meses_ausencia", 0))
    texto = reglas["motivos"][motivo] + (f", {meses:g} meses" if meses else "")
    if sit.get("detalle"):
        texto += f" ({sit['detalle']})"
    if meses > reglas["meses_suspension"]:
        return True, 1.0, texto
    pct = sit.get("porcentaje_jornada")
    if pct is None or not 0 < float(pct) <= 100:
        raise ErrorCompromiso("Situación especial: indica 'porcentaje_jornada' (mayor que 0 y hasta 100), "
                              "el % de la jornada comprometida que dedicó al cumplimiento de sus funciones")
    return False, float(pct) / 100, texto + f"; evaluada en relación al {float(pct):g}% de la jornada"


def calificar(datos: dict, modelo: dict | None = None) -> Resultado:
    modelo = modelo or cargar_modelo()
    observaciones: list[str] = []
    academico, periodo = str(datos.get("academico", "")), str(datos.get("periodo", ""))

    # 0. Situaciones especiales (art. 37).
    suspendida, factor, situacion = situacion_especial(datos, modelo)
    informar_a = modelo["situaciones_especiales"]["informar_a"] if situacion else None
    if suspendida:
        return Resultado(academico, periodo, "suspendida", None, None,
                         modelo["situaciones_especiales"]["descripcion_suspension"], None,
                         [f"Informar a {informar_a}."], situacion_especial=situacion, informar_a=informar_a)
    if situacion:
        observaciones.append(f"Situación especial (art. 37): {situacion}. Informar a {informar_a}.")

    # 1. Ponderación declarada en el compromiso (% de la carga por ámbito, o calculada desde las horas).
    declarado = ponderacion_compromiso(datos, modelo, observaciones)

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
    tareas = [evaluar_tarea(t, modelo, i, factor) for i, t in enumerate(datos.get("tareas") or [], 1)]
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

    # 5. Lo que destaca (excedentes validados), para el reconocimiento institucional.
    destacados = [Destacado(t.ambito, t.subcategoria, t.descripcion, t.detalle, t.cumplimiento_real)
                  for a in ambitos for t in a.tareas if t.destaca]
    if letra == "A+":
        observaciones.append("Desempeño sobresaliente: candidato/a a reconocimiento institucional.")

    return Resultado(academico, periodo, "calificada", total, letra, modelo["descripcion_letras"][letra],
                     a_escala_numerica(total, modelo), observaciones, ambitos,
                     round(auto, 2), p_auto, None if est is None else round(est, 2), p_est,
                     destacados, situacion, informar_a)


def texto_destacado(d: Destacado) -> str:
    if d.detalle.startswith("etapa "):
        return f"avanzó más allá de lo comprometido ({d.detalle.removeprefix('etapa ')})"
    return f"{d.cumplimiento_real:.0f}% de lo comprometido"


def informe(r: Resultado) -> str:
    """Informe en texto para revisar o adjuntar al expediente académico."""
    lineas = [f"Calificación académica SEJA — {r.academico} ({r.periodo})", "=" * 60]
    if r.estado == "suspendida":
        lineas += [f"EVALUACIÓN SUSPENDIDA — {r.descripcion}", f"Situación: {r.situacion_especial}"]
        lineas += ["", "Observaciones:"] + [f"  - {o}" for o in r.observaciones]
        return "\n".join(lineas)
    for a in r.ambitos:
        lineas.append(f"\n{a.nombre}  [declarado {a.declarado:.1f}% → pondera {a.ponderacion:.1%}]")
        for t in a.tareas:
            extra = " ★ destaca" if t.destaca else ""
            peso = f" ×{t.peso:g}" if t.peso != 1 else ""
            lineas.append(f"  · [{t.subcategoria}] {t.descripcion}: {t.puntaje:.1f}{peso} ({t.detalle}){extra}")
        lineas.append(f"  Promedio del ámbito: {a.puntaje:.1f} → {a.letra}")
    lineas.append(f"\nAutoevaluación: {r.autoevaluacion:.1f}  [pondera {r.ponderacion_autoevaluacion:.0%}]")
    if r.estudiantes is not None:
        lineas.append(f"Evaluación de estudiantes: {r.estudiantes:.1f}  [pondera {r.ponderacion_estudiantes:.0%}]")
    lineas += ["-" * 60, f"CUMPLIMIENTO FINAL: {r.puntaje:.1f}%  (escala numérica {r.nota})",
               f"CLASIFICACIÓN: {r.letra} — {r.descripcion}"]
    if r.destacados:
        lineas += ["", "Reconocimiento institucional — destaca en:"]
        lineas += [f"  ★ {d.descripcion} ({d.subcategoria}): {texto_destacado(d)}" for d in r.destacados]
    if r.observaciones:
        lineas += ["", "Observaciones:"] + [f"  - {o}" for o in r.observaciones]
    return "\n".join(lineas)
