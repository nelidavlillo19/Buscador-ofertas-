"""Revisión hacia atrás: compara a cada persona entre cortes (fin de cada año) para medir
ascensos, cambios de estamento, paso a planta, ingresos y egresos."""
from __future__ import annotations

from collections import defaultdict
from statistics import median


def consolidar(registros: list[dict]) -> dict[str, dict[str, dict]]:
    """periodo -> persona -> fila principal (la de mayor bruto) con 'bruto_total' de todos sus vínculos."""
    salida: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in registros:
        actual = salida[r["periodo"]].get(r["persona"])
        if actual is None:
            salida[r["periodo"]][r["persona"]] = {**r, "bruto_total": r["bruto"]}
        else:
            total = actual["bruto_total"] + r["bruto"]
            if r["bruto"] > actual["bruto"]:
                actual = {**r}
            actual["bruto_total"] = total
            salida[r["periodo"]][r["persona"]] = actual
    return salida


def cortes(periodos: list[str], mes_corte: int | None = None) -> list[str]:
    """Último período de cada año (o el mes indicado si existe). Con un solo año: primero y último."""
    por_anio = defaultdict(list)
    for p in sorted(periodos):
        por_anio[p[:4]].append(p)
    elegidos = []
    for anio, ps in sorted(por_anio.items()):
        preferido = f"{anio}-{mes_corte:02d}" if mes_corte else None
        elegidos.append(preferido if preferido in ps else ps[-1])
    if len(elegidos) == 1 and len(periodos) > 1:
        elegidos = [min(periodos), max(periodos)]
    return elegidos


def meses_entre(a: str, b: str) -> int:
    return (int(b[:4]) - int(a[:4])) * 12 + int(b[5:]) - int(a[5:])


def movimiento(antes: dict, despues: dict, orden_grupos: list[str]) -> dict:
    m = {"ascenso_grado": 0, "ascenso_jerarquia": 0, "cambio_estamento": None, "paso_a_planta": False,
         "descenso": False}
    if antes["grado"] is not None and despues["grado"] is not None:
        diferencia = antes["grado"] - despues["grado"]  # en la EUS el grado menor es el más alto
        if diferencia > 0:
            m["ascenso_grado"] = diferencia
        elif diferencia < 0:
            m["descenso"] = True
    if antes["rango_jerarquia"] is not None and despues["rango_jerarquia"] is not None:
        m["ascenso_jerarquia"] = max(despues["rango_jerarquia"] - antes["rango_jerarquia"], 0)
    if antes["grupo"] != despues["grupo"]:
        pos = lambda g: orden_grupos.index(g) if g in orden_grupos else -1  # noqa: E731
        m["cambio_estamento"] = "ascendente" if pos(despues["grupo"]) > pos(antes["grupo"]) else "otro"
    m["paso_a_planta"] = antes["tipo"] in ("contrata", "honorarios", "codigo_trabajo") and despues["tipo"] == "planta"
    m["ascendido"] = bool(m["ascenso_grado"] or m["ascenso_jerarquia"] or m["cambio_estamento"] == "ascendente")
    return m


def analizar(registros: list[dict], config: dict) -> dict:
    cfg = config.get("trayectorias", {})
    orden = cfg.get("orden_grupos", ["auxiliares", "administrativos", "tecnicos", "profesionales",
                                     "academicos", "directivos"])
    contar_planta = cfg.get("paso_a_planta_cuenta_como_ascenso", False)
    por_periodo = consolidar(registros)
    sel = cortes(list(por_periodo), cfg.get("mes_corte"))
    tasas, movimientos = [], []
    for desde, hasta in zip(sel, sel[1:]):
        a, b = por_periodo[desde], por_periodo[hasta]
        meses = max(meses_entre(desde, hasta), 1)
        acumulado = defaultdict(lambda: defaultdict(list))
        for persona, fa in a.items():
            g = fa["grupo"]
            acc = acumulado[g]
            acc["inicio"].append(persona)
            fb = b.get(persona)
            if fb is None:
                acc["egresos"].append(persona)
                continue
            m = movimiento(fa, fb, orden)
            if contar_planta and m["paso_a_planta"]:
                m["ascendido"] = True
            variacion = fb["bruto_total"] / fa["bruto_total"] - 1 if fa["bruto_total"] else None
            acc["permanecen"].append(persona)
            if m["ascendido"]:
                acc["ascendidos"].append(persona)
                acc["grados"].append(m["ascenso_grado"])
                if variacion is not None:
                    acc["var_asc"].append(variacion)
            elif variacion is not None:
                acc["var_no_asc"].append(variacion)
            if m["paso_a_planta"]:
                acc["a_planta"].append(persona)
            if m["descenso"]:
                acc["descensos"].append(persona)
            if m["ascendido"] or m["paso_a_planta"] or m["descenso"] or m["cambio_estamento"]:
                movimientos.append({
                    "desde": desde, "hasta": hasta, "persona": fa["nombre"],
                    "grupo_inicial": g, "grupo_final": fb["grupo"],
                    "tipo_inicial": fa["tipo"], "tipo_final": fb["tipo"],
                    "grado_inicial": fa["grado"], "grado_final": fb["grado"],
                    "jerarquia_inicial": fa["jerarquia"], "jerarquia_final": fb["jerarquia"],
                    "bruto_inicial": fa["bruto_total"], "bruto_final": fb["bruto_total"],
                    "variacion_bruto": variacion,
                    "movimiento": _describir(m),
                })
        for persona, fb in b.items():
            if persona not in a:
                acumulado[fb["grupo"]]["ingresos"].append(persona)
        for g, acc in sorted(acumulado.items()):
            n_perm = len(acc["permanecen"])
            tasa = len(acc["ascendidos"]) / n_perm if n_perm else 0.0
            var_asc = median(acc["var_asc"]) if acc["var_asc"] else None
            var_no = median(acc["var_no_asc"]) if acc["var_no_asc"] else None
            tasas.append({
                "desde": desde, "hasta": hasta, "meses": meses, "grupo": g,
                "dotacion_inicial": len(acc["inicio"]), "permanecen": n_perm,
                "ingresos": len(acc["ingresos"]), "egresos": len(acc["egresos"]),
                "ascendidos": len(acc["ascendidos"]), "tasa_ascenso": tasa,
                "tasa_ascenso_anual": 1 - (1 - tasa) ** (12 / meses) if tasa < 1 else 1.0,
                "grados_promedio_por_ascenso": (sum(acc["grados"]) / len(acc["grados"])) if acc["grados"] else 0.0,
                "aumento_mediano_ascendidos": var_asc,
                "aumento_mediano_resto": var_no,
                "premio_ascenso": (var_asc - var_no) if var_asc is not None and var_no is not None else None,
                "pasos_a_planta": len(acc["a_planta"]), "descensos": len(acc["descensos"]),
                "tasa_egreso_anual": _anual(len(acc["egresos"]) / len(acc["inicio"]), meses) if acc["inicio"] else 0.0,
            })
    return {"cortes": sel, "tasas": tasas, "movimientos": movimientos, "resumen": resumir(tasas)}


def _anual(tasa: float, meses: int) -> float:
    return 1.0 if tasa >= 1 else 1 - (1 - tasa) ** (12 / meses)


def _describir(m: dict) -> str:
    partes = []
    if m["ascenso_grado"]:
        partes.append(f"sube {m['ascenso_grado']} grado(s)")
    if m["ascenso_jerarquia"]:
        partes.append("sube jerarquía académica")
    if m["cambio_estamento"]:
        partes.append(f"cambio de estamento ({m['cambio_estamento']})")
    if m["paso_a_planta"]:
        partes.append("pasa a planta")
    if m["descenso"]:
        partes.append("baja de grado")
    return "; ".join(partes)


def resumir(tasas: list[dict]) -> dict[str, dict]:
    """Promedio ponderado (por personas que permanecen) de las tasas anuales de cada grupo."""
    salida = {}
    por_grupo = defaultdict(list)
    for t in tasas:
        por_grupo[t["grupo"]].append(t)
    for g, ts in por_grupo.items():
        peso = sum(t["permanecen"] for t in ts) or 1
        premios = [t["premio_ascenso"] for t in ts if t["premio_ascenso"] is not None]
        salida[g] = {
            "tasa_ascenso_anual": sum(t["tasa_ascenso_anual"] * t["permanecen"] for t in ts) / peso,
            "tasa_egreso_anual": sum(t["tasa_egreso_anual"] * t["dotacion_inicial"] for t in ts)
            / (sum(t["dotacion_inicial"] for t in ts) or 1),
            "premio_ascenso": median(premios) if premios else None,
            "observaciones": sum(t["permanecen"] for t in ts),
        }
    return salida
