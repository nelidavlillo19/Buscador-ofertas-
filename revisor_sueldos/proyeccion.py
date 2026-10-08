"""Proyección de costos de un nuevo sistema de jerarquización y evaluación.

Supuestos (todos configurables en el YAML):
- Cada persona se encasilla en un nivel del nuevo sistema según su jerarquía académica, su grado EUS
  o su posición (percentil) dentro de su grupo.
- Remuneración objetivo del nivel = máx(remuneración actual × (1 + incremento), piso del nivel × jornada/44);
  con garantía de no disminución nunca baja de la actual.
- La brecha hacia el objetivo del nivel inicial se cierra gradualmente según 'gradualidad' (fracción acumulada
  por año); la diferencia por ascender a un nivel superior se paga completa desde que ocurre.
- Subir un nivel aumenta al menos el premio de ascenso histórico (o 'premio_ascenso_defecto').
- Cada año una fracción (tasa de ascenso × efecto de la evaluación) pasa al nivel siguiente
  (cálculo en valor esperado, sin azar).
- Incentivo por evaluación = remuneración anual × Σ(distribución × % incentivo).
- Escenario base (sin reforma): sueldos actuales con reajuste y ascensos a la tasa histórica sobre la misma
  escala de niveles, cada uno con el premio histórico (así ambos escenarios tienen el mismo techo).
- Dotación constante (los egresos se reponen en el mismo nivel), salvo 'crecimiento_dotacion'.
"""
from __future__ import annotations

from collections import defaultdict

from .cargar import sin_tildes
from .costeo import factor_empleador, percentil


def _nivel_inicial(p: dict, cfg_grupo: dict, percentiles: dict) -> tuple[int, str]:
    niveles = cfg_grupo["niveles"]
    criterio = cfg_grupo.get("criterio", "percentil")
    if criterio == "jerarquia" and p["jerarquia"]:
        j = sin_tildes(p["jerarquia"])
        for i, n in enumerate(niveles):
            if j in [sin_tildes(x) for x in n.get("jerarquias", [])]:
                return i, "jerarquia"
    if criterio in ("grado", "jerarquia") and p["grado"] is not None:
        for i, n in enumerate(niveles):
            if "grados" in n and min(n["grados"]) <= p["grado"] <= max(n["grados"]):
                return i, "grado"
    # respaldo: posición relativa del sueldo dentro del grupo
    q = percentiles[p["persona"]]
    for i, n in enumerate(niveles):
        desde, hasta = n.get("percentil", [i / len(niveles), (i + 1) / len(niveles)])
        if desde <= q < hasta or (i == len(niveles) - 1 and q >= desde):
            return i, "percentil"
    return 0, "percentil"


def _ascender(dist: list[float], tasa: float) -> list[float]:
    nueva = [0.0] * len(dist)
    for i, prob in enumerate(dist):
        sube = prob * tasa if i < len(dist) - 1 else 0.0
        nueva[i] += prob - sube
        if sube:
            nueva[i + 1] += sube
    return nueva


def _percentiles(personas: list[dict]) -> dict[str, float]:
    orden = sorted(personas, key=lambda p: p["bruto_total"])
    n = len(orden)
    return {p["persona"]: (i / n if n > 1 else 0.5) for i, p in enumerate(orden)}


def proyectar(por_periodo: dict, resumen_historico: dict, config: dict) -> dict:
    cfg = config["proyeccion"]
    periodo_base = cfg.get("periodo_base") or max(por_periodo)
    anio_base = int(periodo_base[:4])
    horizonte = cfg.get("horizonte_anios", 5)
    reajuste = cfg.get("reajuste_anual", 0.0)
    crecimiento = cfg.get("crecimiento_dotacion", 0.0)
    gradualidad = cfg.get("gradualidad", [1.0])
    garantia = cfg.get("garantia_no_disminucion", True)
    tipos = set(cfg.get("tipos_incluidos", ["planta", "contrata", "codigo_trabajo"]))
    jornada_completa = cfg.get("jornada_completa", 44)
    ev = cfg.get("evaluacion", {})
    dist = ev.get("distribucion", {})
    incentivo_medio = sum(dist.get(k, 0) * v for k, v in ev.get("incentivo", {}).items())
    efecto_ascenso = (sum(dist.get(k, 0) * v for k, v in ev.get("multiplicador_ascenso", {}).items())
                      if ev.get("multiplicador_ascenso") else 1.0)
    tasas_cfg = cfg.get("tasas_ascenso", "historicas")
    premio_defecto = cfg.get("premio_ascenso_defecto", 0.05)

    personas = [p for p in por_periodo[periodo_base].values() if p["tipo"] in tipos]
    por_grupo = defaultdict(list)
    for p in personas:
        por_grupo[p["grupo"]].append(p)

    filas, niveles_salida, encasillamiento, supuestos = [], [], [], []
    for grupo, gente in sorted(por_grupo.items()):
        cfg_grupo = cfg.get("jerarquizacion", {}).get(grupo)
        hist = resumen_historico.get(grupo, {})
        if isinstance(tasas_cfg, dict):
            tasa = tasas_cfg.get(grupo, cfg.get("tasa_ascenso_defecto", 0.05))
            origen_tasa = "configurada"
        elif hist.get("observaciones"):
            tasa, origen_tasa = hist["tasa_ascenso_anual"], "histórica"
        else:
            tasa, origen_tasa = cfg.get("tasa_ascenso_defecto", 0.05), "por defecto"
        premio = hist.get("premio_ascenso")
        premio = premio if premio is not None and premio > 0 else premio_defecto
        tasa_reforma = min(tasa * efecto_ascenso, 1.0)
        supuestos.append({"grupo": grupo, "personas": len(gente), "tasa_ascenso_historica": tasa,
                          "origen_tasa": origen_tasa, "tasa_ascenso_con_evaluacion": tasa_reforma,
                          "premio_ascenso": premio, "incentivo_medio": incentivo_medio if cfg_grupo else 0.0,
                          "con_nuevo_sistema": bool(cfg_grupo)})
        niveles = (cfg_grupo or {}).get("niveles") or [{"nombre": "único", "piso": 0}]
        pct = _percentiles(gente)
        estado = []
        for p in gente:
            k0, via = _nivel_inicial(p, cfg_grupo, pct) if cfg_grupo else (0, "-")
            fj = (p.get("jornada") or jornada_completa) / jornada_completa
            objetivos = []
            for n in niveles:
                obj = max(p["bruto_total"] * (1 + n.get("incremento", 0.0)), n.get("piso", 0) * fj)
                if not garantia:
                    obj = n.get("piso", 0) * fj or p["bruto_total"]
                objetivos.append(obj)
            for i in range(k0 + 1, len(objetivos)):  # subir de nivel nunca vale menos que el premio histórico
                objetivos[i] = max(objetivos[i], objetivos[i - 1] * (1 + premio))
            inicio = [1.0 if i == k0 else 0.0 for i in range(len(niveles))]
            estado.append({"p": p, "k0": k0, "objetivos": objetivos, "dist": inicio, "dist_base": list(inicio)})
            encasillamiento.append({
                "persona": p["nombre"], "grupo": grupo, "tipo": p["tipo"], "grado": p["grado"],
                "jerarquia": p["jerarquia"], "nivel_asignado": niveles[k0]["nombre"], "criterio": via,
                "bruto_actual": p["bruto_total"], "bruto_objetivo": objetivos[k0],
                "brecha_mensual": objetivos[k0] - p["bruto_total"],
            })
        for t in range(0, horizonte + 1):
            r = (1 + reajuste) ** t
            d = (1 + crecimiento) ** t
            g = gradualidad[min(t, len(gradualidad)) - 1] if t > 0 else 0.0
            if t > 0 and cfg_grupo:
                for e in estado:  # ascensos esperados del año, con y sin el efecto de la evaluación
                    e["dist"] = _ascender(e["dist"], tasa_reforma)
                    e["dist_base"] = _ascender(e["dist_base"], tasa)
            base = reforma = empleador_base = empleador_reforma = 0.0
            por_nivel = defaultdict(lambda: [0.0, 0.0])
            for e in estado:
                actual = e["p"]["bruto_total"]
                f = 1 + factor_empleador(e["p"]["tipo"], config)
                if cfg_grupo:
                    # sin reforma: misma escala de niveles, cada ascenso vale el premio histórico
                    b = sum(prob * actual * (1 + premio) ** max(i - e["k0"], 0)
                            for i, prob in enumerate(e["dist_base"])) * r * 12 * d
                else:
                    b = actual * r * (1 + tasa * premio) ** t * 12 * d
                if cfg_grupo:
                    # la nivelación inicial se aplica gradualmente; los ascensos posteriores, completos
                    inicial = actual + (e["objetivos"][e["k0"]] - actual) * g
                    sueldos = [inicial + max(obj - e["objetivos"][e["k0"]], 0) for obj in e["objetivos"]]
                    esperado = sum(prob * s for prob, s in zip(e["dist"], sueldos))
                    m = esperado * r * 12 * d
                    for i, prob in enumerate(e["dist"]):
                        por_nivel[i][0] += prob * d
                        por_nivel[i][1] += prob * d * sueldos[i] * r
                else:
                    m = b
                base += b
                reforma += m
                empleador_base += b * f
                empleador_reforma += m * f
            incentivo = reforma * incentivo_medio if (cfg_grupo and t > 0) else 0.0
            total = reforma + incentivo
            filas.append({
                "anio": anio_base + t, "grupo": grupo, "dotacion": len(estado) * d,
                "costo_base": base, "costo_reforma_remuneraciones": reforma,
                "incentivo_evaluacion": incentivo, "costo_reforma_total": total,
                "diferencia": total - base, "diferencia_pct": (total / base - 1) if base else 0.0,
                "costo_empleador_base": empleador_base,
                "costo_empleador_reforma": empleador_reforma + incentivo,
            })
            if cfg_grupo:
                for i, (n_esp, masa) in sorted(por_nivel.items()):
                    niveles_salida.append({"anio": anio_base + t, "grupo": grupo, "nivel": niveles[i]["nombre"],
                                           "personas_esperadas": n_esp,
                                           "remuneracion_media": masa / n_esp if n_esp else 0.0})
    totales = defaultdict(lambda: defaultdict(float))
    for f in filas:
        for k, v in f.items():
            if k not in ("anio", "grupo", "diferencia_pct"):
                totales[f["anio"]][k] += v
    for anio, v in sorted(totales.items()):
        filas.append({"anio": anio, "grupo": "TOTAL", **v,
                      "diferencia_pct": (v["costo_reforma_total"] / v["costo_base"] - 1) if v["costo_base"] else 0.0})
    return {"periodo_base": periodo_base, "filas": filas, "niveles": niveles_salida,
            "encasillamiento": encasillamiento, "supuestos": supuestos,
            "brecha_total_mensual": sum(e["brecha_mensual"] for e in encasillamiento)}
