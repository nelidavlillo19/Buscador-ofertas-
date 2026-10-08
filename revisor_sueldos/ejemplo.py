"""Genera planillas FICTICIAS en formato Transparencia Activa para probar el revisor.
Los nombres y montos son inventados; no corresponden a ninguna persona real."""
from __future__ import annotations

import csv
import random
from pathlib import Path

NOMBRES = ["Ana", "Luis", "María", "José", "Carmen", "Pedro", "Rosa", "Juan", "Isabel", "Carlos", "Paula",
           "Jorge", "Valentina", "Diego", "Camila", "Andrés", "Javiera", "Felipe", "Daniela", "Rodrigo",
           "Constanza", "Matías", "Francisca", "Ignacio", "Fernanda", "Tomás", "Catalina", "Sebastián"]
APELLIDOS = ["González", "Muñoz", "Rojas", "Díaz", "Pérez", "Soto", "Contreras", "Silva", "Martínez",
             "Sepúlveda", "Morales", "Rodríguez", "López", "Fuentes", "Hernández", "Torres", "Araya",
             "Flores", "Espinoza", "Valenzuela", "Castillo", "Tapia", "Reyes", "Gutiérrez", "Castro",
             "Pizarro", "Álvarez", "Vásquez", "Sánchez", "Fernández", "Ramírez", "Carrasco", "Gómez"]

# grupo: (estamento en planilla, cantidad, rango de grados, sueldo del grado más bajo, prob. ascenso anual)
GRUPOS = {
    "academicos": ("Académico", 260, None, None, 0.07),
    "directivos": ("Directivo", 25, (2, 8), 2900000, 0.05),
    "profesionales": ("Profesional", 150, (6, 16), 1250000, 0.09),
    "tecnicos": ("Técnico", 70, (12, 20), 820000, 0.08),
    "administrativos": ("Administrativo", 90, (14, 23), 720000, 0.07),
    "auxiliares": ("Auxiliar", 60, (18, 27), 600000, 0.06),
}
JERARQUIAS = [("Instructor", 1850000), ("Profesor Asistente", 2450000), ("Profesor Asociado", 3200000),
              ("Profesor Titular", 4100000)]
PERIODOS = ["2024-12"] + [f"2025-{m:02d}" for m in range(1, 13)] + [f"2026-{m:02d}" for m in range(1, 10)]
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
         "Noviembre", "Diciembre"]
ENCABEZADO = ["Año", "Mes", "Estamento", "Apellido paterno", "Apellido materno", "Nombres",
              "Grado EUS o jornada", "Calificación profesional o formación", "Cargo o función", "Región",
              "Asignaciones especiales", "Unidad monetaria", "Remuneración bruta mensualizada",
              "Remuneración líquida mensualizada", "Fecha de inicio", "Fecha de término", "Observaciones"]


def _persona(rnd: random.Random, usados: set, grupo: str) -> dict:
    while True:
        n = (rnd.choice(APELLIDOS), rnd.choice(APELLIDOS), f"{rnd.choice(NOMBRES)} {rnd.choice(NOMBRES)}")
        if n not in usados:
            usados.add(n)
            break
    estamento, _, grados, _, _ = GRUPOS[grupo]
    p = {"nombre": n, "grupo": grupo, "estamento": estamento, "factor": rnd.uniform(0.95, 1.08),
         "tipo": "planta" if rnd.random() < 0.45 else "contrata"}
    if grupo == "academicos":
        p["jerarquia"] = rnd.choices(range(4), weights=[3, 4, 2, 1])[0]
        p["jornada"] = rnd.choice([22, 33, 44, 44, 44])
        p["grado"] = None
    else:
        p["grado"] = rnd.randint(*grados)
    return p


def _bruto(p: dict, reajuste: float) -> float:
    if p["grupo"] == "academicos":
        base = JERARQUIAS[p["jerarquia"]][1] * p["jornada"] / 44
    else:
        _, _, grados, minimo, _ = GRUPOS[p["grupo"]]
        base = minimo * 1.075 ** (grados[1] - p["grado"])
    return round(base * p["factor"] * reajuste)


def generar(destino: Path, semilla: int = 7) -> list[Path]:
    rnd = random.Random(semilla)
    usados: set = set()
    gente = [_persona(rnd, usados, g) for g, d in GRUPOS.items() for _ in range(d[1])]
    honorarios = [_persona(rnd, usados, "profesionales") for _ in range(40)]
    for h in honorarios:
        h["tipo"] = "honorarios"
    destino.mkdir(parents=True, exist_ok=True)
    reajuste = 1.0
    filas = {"planta": [], "contrata": [], "honorarios": []}
    for periodo in PERIODOS:
        anio, mes = int(periodo[:4]), int(periodo[5:])
        if mes == 12 and periodo != PERIODOS[0]:
            reajuste *= 1.045  # reajuste del sector público en diciembre
        if mes == 1:  # ascensos, egresos e ingresos de inicio de año
            for p in list(gente):
                if rnd.random() < 0.05:
                    gente.remove(p)
                    gente.append(_persona(rnd, usados, p["grupo"]))
                    continue
                if rnd.random() < GRUPOS[p["grupo"]][4]:
                    if p["grupo"] == "academicos":
                        p["jerarquia"] = min(p["jerarquia"] + 1, 3)
                    else:
                        p["grado"] = max(p["grado"] - rnd.choice([1, 1, 2]), GRUPOS[p["grupo"]][2][0])
                if p["tipo"] == "contrata" and rnd.random() < 0.04:
                    p["tipo"] = "planta"
        for p in gente + honorarios:
            bruto = _bruto(p, reajuste) if p["tipo"] != "honorarios" else round(1100000 * p["factor"] * reajuste)
            cargo = JERARQUIAS[p["jerarquia"]][0] if p["grupo"] == "academicos" else p["estamento"]
            grado = f"{p['jornada']} horas" if p["grupo"] == "academicos" else (
                p["grado"] if p["tipo"] != "honorarios" else "")
            filas[p["tipo"]].append([
                anio, MESES[mes - 1], p["estamento"] if p["tipo"] != "honorarios" else "Profesional",
                p["nombre"][0], p["nombre"][1], p["nombre"][2], grado, "Título profesional",
                cargo, "Región Metropolitana", "", "Pesos",
                f"{bruto:,}".replace(",", "."), f"{round(bruto * 0.79):,}".replace(",", "."),
                "01/03/2015", "Indefinido", "",
            ])
    # algunas anomalías para que la revisión tenga qué mostrar
    filas["contrata"][5][12] = "0"                                   # bruto en cero
    filas["planta"][10][12] = f"{25_000_000:,}".replace(",", ".")     # monto atípico
    duplicado = list(filas["planta"][20])
    duplicado[12] = "450.000"
    filas["honorarios"].append(duplicado)                             # doble vínculo planta + honorarios
    filas["contrata"][30][2] = "Asesor externo"                       # estamento no reconocido
    rutas = []
    for tipo, fs in filas.items():
        ruta = destino / f"umce_ficticio_{tipo}_2024-2026.csv"
        with ruta.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(ENCABEZADO)
            w.writerows(fs)
        rutas.append(ruta)
    return rutas
