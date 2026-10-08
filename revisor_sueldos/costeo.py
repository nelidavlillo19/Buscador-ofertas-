"""Costeo por período, año, grupo de trabajadores y tipo de contrato."""
from __future__ import annotations

from collections import defaultdict
from statistics import mean, median, pstdev


def percentil(valores: list[float], p: float) -> float:
    v = sorted(valores)
    if not v:
        return 0.0
    k = (len(v) - 1) * p
    i = int(k)
    return v[i] + (v[min(i + 1, len(v) - 1)] - v[i]) * (k - i)


def factor_empleador(tipo: str, config: dict) -> float:
    return config.get("costo_empleador", {}).get(tipo, config.get("costo_empleador", {}).get("defecto", 0.0))


def _resumen(filas: list[dict], config: dict) -> dict:
    brutos = [f["bruto"] for f in filas]
    total = sum(brutos)
    return {
        "dotacion": len({f["persona"] for f in filas}),
        "filas": len(filas),
        "total_bruto": total,
        "costo_empleador": sum(f["bruto"] * (1 + factor_empleador(f["tipo"], config)) for f in filas),
        "promedio": mean(brutos),
        "mediana": median(brutos),
        "p10": percentil(brutos, 0.10),
        "p90": percentil(brutos, 0.90),
        "minimo": min(brutos),
        "maximo": max(brutos),
    }


def por_periodo(registros: list[dict], config: dict) -> list[dict]:
    """Una fila por período × grupo (y una fila 'TOTAL' por período)."""
    grupos = defaultdict(list)
    for r in registros:
        grupos[(r["periodo"], r["grupo"])].append(r)
        grupos[(r["periodo"], "TOTAL")].append(r)
    return [{"periodo": p, "grupo": g, **_resumen(f, config)} for (p, g), f in sorted(grupos.items())]


def por_tipo(registros: list[dict], config: dict) -> list[dict]:
    grupos = defaultdict(list)
    for r in registros:
        grupos[(r["periodo"], r["grupo"], r["tipo"])].append(r)
    return [{"periodo": p, "grupo": g, "tipo": t, **_resumen(f, config)} for (p, g, t), f in sorted(grupos.items())]


def anual(registros: list[dict], config: dict) -> list[dict]:
    """Costo anual por grupo. Si faltan meses, se anualiza con el promedio de los meses disponibles."""
    meses_anio = defaultdict(set)
    datos = defaultdict(lambda: defaultdict(float))
    personas = defaultdict(set)
    for r in registros:
        meses_anio[r["anio"]].add(r["mes"])
        for g in (r["grupo"], "TOTAL"):
            datos[(r["anio"], g)]["bruto"] += r["bruto"]
            datos[(r["anio"], g)]["empleador"] += r["bruto"] * (1 + factor_empleador(r["tipo"], config))
            personas[(r["anio"], g, r["mes"])].add(r["persona"])
    salida = []
    for (anio, g), d in sorted(datos.items()):
        n = len(meses_anio[anio])
        dot = [len(personas[(anio, g, m)]) for m in meses_anio[anio]]
        salida.append({
            "anio": anio, "grupo": g, "meses_con_datos": n,
            "bruto_observado": d["bruto"],
            "bruto_anualizado": d["bruto"] / n * 12,
            "costo_empleador_anualizado": d["empleador"] / n * 12,
            "dotacion_promedio": mean(dot),
            "costo_medio_por_persona_anual": d["bruto"] / n * 12 / max(mean(dot), 1),
        })
    # variación respecto del año anterior
    previo = {(s["anio"], s["grupo"]): s for s in salida}
    for s in salida:
        a = previo.get((s["anio"] - 1, s["grupo"]))
        s["variacion_anual"] = (s["bruto_anualizado"] / a["bruto_anualizado"] - 1) if a else None
    return salida


def hallazgos(registros: list[dict], config: dict) -> list[dict]:
    """Observaciones de revisión: datos faltantes, duplicados y remuneraciones atípicas."""
    umbral = config.get("revision", {}).get("desvios_atipico", 3.0)
    salida = []
    vistos = defaultdict(list)
    for r in registros:
        vistos[(r["periodo"], r["persona"])].append(r)
        if r["bruto"] <= 0:
            salida.append(_obs(r, "remuneración bruta cero o negativa"))
        if r["grupo"] == "sin_clasificar":
            salida.append(_obs(r, f"estamento no reconocido: '{r['estamento']}'"))
        if r["tipo"] in ("planta", "contrata") and r["grupo"] != "academicos" and r["grado"] is None:
            salida.append(_obs(r, "planta/contrata sin grado EUS"))
        if r["liquido"] and r["liquido"] > r["bruto"]:
            salida.append(_obs(r, "líquido mayor que bruto"))
    for (periodo, persona), filas in vistos.items():
        if len(filas) > 1:
            tipos = ", ".join(sorted(f["tipo"] for f in filas))
            salida.append(_obs(filas[0], f"aparece {len(filas)} veces en el período ({tipos}); revisar doble vínculo"))
    # atípicos: dentro del mismo período, grupo, tipo y grado (o jerarquía)
    celdas = defaultdict(list)
    for r in registros:
        celdas[(r["periodo"], r["grupo"], r["tipo"], r["grado"], r["jerarquia"])].append(r)
    for filas in celdas.values():
        if len(filas) < 5:
            continue
        b = [f["bruto"] for f in filas]
        m, d = median(b), pstdev(b)
        if d == 0:
            continue
        for f in filas:
            z = (f["bruto"] - m) / d
            if abs(z) >= umbral:
                salida.append(_obs(f, f"remuneración atípica ({z:+.1f} desv.) frente a pares de igual "
                                      f"grado/jerarquía (mediana {m:,.0f})".replace(",", ".")))
    return salida


def _obs(r: dict, texto: str) -> dict:
    return {"periodo": r["periodo"], "persona": r["nombre"], "grupo": r["grupo"], "tipo": r["tipo"],
            "grado": r["grado"], "jerarquia": r["jerarquia"], "bruto": r["bruto"], "observacion": texto,
            "archivo": r["archivo"]}
