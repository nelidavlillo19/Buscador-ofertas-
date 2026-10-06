from pathlib import Path

import pytest
import yaml

from seja import ErrorCompromiso, calificar, informe

EJEMPLOS = Path(__file__).parent.parent / "seja" / "ejemplos"


def tarea(ambito, sub="otra", **kw):
    return {"ambito": ambito, "subcategoria": sub, **kw}


def academico(compromiso, tareas, auto=100, est=100, **kw):
    return {"compromiso": compromiso, "tareas": tareas,
            "autoevaluacion": {"porcentaje": auto}, "estudiantes": {"porcentaje": est}, **kw}


def test_ponderacion_80_compromiso_10_auto_10_estudiantes():
    r = calificar(academico({"docencia": 50, "investigacion": 50},
                            [tarea("docencia", evidencia={"estado": "cumplido"}),
                             tarea("investigacion", evidencia={"estado": "no_cumplido"})],
                            auto=50, est=0))
    assert [a.ponderacion for a in r.ambitos] == [0.4, 0.4]
    # 100·0,4 + 0·0,4 + 50·0,1 + 0·0,1
    assert r.puntaje == 45.0
    assert r.letra == "D"


def test_tareas_se_promedian_dentro_del_ambito_y_ambito_se_califica():
    r = calificar(academico({"docencia": 100}, [
        tarea("docencia", "cursos_pregrado", instrumento={"puntaje": 3, "min": 1, "max": 4}),
        tarea("docencia", "practicas", evidencia={"comprometido": 4, "logrado": 2}),
        tarea("docencia", "tutoria", evidencia={"estado": "cumplido"}, peso=2),
    ]))
    docencia = r.ambitos[0]
    assert [t.puntaje for t in docencia.tareas] == [66.67, 50.0, 100.0]
    assert docencia.puntaje == round((66.67 + 50 + 200) / 4, 2)
    assert docencia.letra == "B"


def test_pauta_cumple_no_cumple_ignora_no_aplica():
    r = calificar(academico({"docencia": 100}, [
        tarea("docencia", "cursos_pregrado", instrumento={"cumple": 9, "no_cumple": 1, "no_aplica": 3})]))
    assert r.ambitos[0].puntaje == 90


@pytest.mark.parametrize("puntaje, nota", [(100, 7), (90, 7), (89.9, 6), (80, 6), (70, 5), (60, 4), (50, 3), (40, 2), (39, 1)])
def test_escala_numerica_segun_tabla_de_equivalencia(puntaje, nota):
    r = calificar(academico({"docencia": 100}, [tarea("docencia", instrumento={"porcentaje": puntaje})],
                            auto=puntaje, est=puntaje))
    assert r.nota == nota


def test_instrumento_y_evidencia_en_la_misma_tarea_se_promedian():
    r = calificar(academico({"gestion": 100}, [
        tarea("gestion", instrumento={"porcentaje": 80}, evidencia={"estado": "cumplido"})]))
    assert r.ambitos[0].puntaje == 90


@pytest.mark.parametrize("puntaje, letra", [(100, "A"), (90, "A"), (89.9, "B"), (75, "B"), (74.9, "C"), (55, "C"), (54.9, "D"), (0, "D")])
def test_umbrales_de_clasificacion_sin_letra_e(puntaje, letra):
    r = calificar(academico({"docencia": 100}, [tarea("docencia", instrumento={"porcentaje": puntaje})],
                            auto=puntaje, est=puntaje))
    assert r.letra == letra


def test_a_mas_desde_101_por_ciento_con_excedente_validado():
    def final(logrado, validado=True):
        return calificar(academico({"docencia": 100}, [tarea("docencia", evidencia={
            "comprometido": 100, "logrado": logrado, "validado": validado})]))

    assert final(101).ambitos[0].puntaje == 101
    assert (final(101).puntaje, final(101).letra) == (100.8, "A")   # 101·0,8 + 100·0,2
    assert (final(102).puntaje, final(102).letra) == (101.6, "A+")
    assert final(102).ambitos[0].letra == "A+"
    assert final(102).nota == 7.0


def test_tope_de_excedente_y_registro_de_lo_que_destaca():
    r = calificar(academico({"docencia": 100}, [
        tarea("docencia", "direccion_titulacion", descripcion="Tesis dirigidas",
              evidencia={"comprometido": 2, "logrado": 5, "validado": True})]))
    t = r.ambitos[0].tareas[0]
    assert (t.puntaje, t.cumplimiento_real) == (120, 250)
    assert r.puntaje == 116.0 and r.letra == "A+"
    assert [(d.descripcion, d.cumplimiento_real) for d in r.destacados] == [("Tesis dirigidas", 250)]
    assert any("reconocimiento institucional" in o for o in r.observaciones)
    assert r.como_dict()["reconocimiento_institucional"][0]["subcategoria"] == "direccion_titulacion"
    assert "destaca en" in informe(r)


def test_excedente_sin_validar_se_considera_100():
    r = calificar(academico({"docencia": 100},
                            [tarea("docencia", evidencia={"comprometido": 2, "logrado": 5})]))
    assert r.ambitos[0].puntaje == 100
    assert r.letra == "A"
    assert "sin validar" in r.ambitos[0].tareas[0].detalle


def test_eximido_de_docencia_redistribuye_el_10_de_estudiantes():
    datos = academico({"gestion": 100}, [tarea("gestion", evidencia={"estado": "cumplido"})], auto=0)
    datos["estudiantes"] = None
    datos["exento_estudiantes"] = True
    r = calificar(datos)
    assert r.ambitos[0].ponderacion == 0.9
    assert r.puntaje == 90


def test_ambito_declarado_sin_tareas_vale_cero():
    r = calificar(academico({"docencia": 80, "vinculacion": 20}, [tarea("docencia", evidencia={"estado": "cumplido"})]))
    assert r.ambitos[1].puntaje == 0
    assert any("sin tareas" in o for o in r.observaciones)


@pytest.mark.parametrize("cambio, mensaje", [
    ({"compromiso": {"docencia": 60, "gestion": 30}}, "suman 90"),
    ({"compromiso": {"docencia": 100, "deporte": 0.0001}}, "no existe"),
    ({"tareas": [tarea("docencia", "clases")]}, "subcategoría 'clases'"),
    ({"tareas": [tarea("docencia")]}, "instrumento"),
    ({"tareas": [tarea("docencia", instrumento={"puntaje": 8, "min": 1, "max": 7})]}, "fuera de la escala"),
    ({"tareas": [tarea("docencia", evidencia={"estado": "casi"})]}, "no válido"),
    ({"tareas": [tarea("docencia", instrumento={"cumple": 0, "no_cumple": 0, "no_aplica": 5})]}, "no tiene afirmaciones"),
    ({"estudiantes": None}, "estudiantes"),
])
def test_errores_de_datos(cambio, mensaje):
    datos = academico({"docencia": 100}, [tarea("docencia", evidencia={"estado": "cumplido"})])
    datos.update(cambio)
    with pytest.raises(ErrorCompromiso, match=mensaje):
        calificar(datos)


def test_ponderacion_desde_horas_promedia_semestres():
    datos = academico(None, [tarea("docencia", evidencia={"estado": "cumplido"}),
                             tarea("gestion", evidencia={"estado": "cumplido"})])
    del datos["compromiso"]
    datos["horas"] = {"docencia": [10, 20], "gestion": 15, "vinculacion": 0}
    r = calificar(datos)
    assert [(a.ambito, a.declarado) for a in r.ambitos] == [("docencia", 50), ("gestion", 50)]


def test_advierte_horas_sobre_la_jornada_y_docencia_fuera_de_rango():
    datos = academico(None, [tarea("docencia", evidencia={"estado": "cumplido"}),
                             tarea("vinculacion", evidencia={"estado": "cumplido"})],
                      jerarquia="Asociado", perfil="investigador", jornada="completa")
    del datos["compromiso"]
    datos["horas"] = {"docencia": 15, "vinculacion": 35}
    obs = " ".join(calificar(datos).observaciones)
    assert "superan la jornada completa (44 h)" in obs
    assert "docencia pesa 30.0%" in obs and "entre 40% y 60%" in obs


def test_docencia_dentro_de_rango_no_advierte():
    r = calificar(academico({"docencia": 70, "gestion": 30},
                            [tarea("docencia", evidencia={"estado": "cumplido"}),
                             tarea("gestion", evidencia={"estado": "cumplido"})],
                            jerarquia="instructor"))
    assert not any("docencia pesa" in o for o in r.observaciones)


def test_no_se_puede_declarar_porcentaje_y_horas():
    datos = academico({"docencia": 100}, [tarea("docencia", evidencia={"estado": "cumplido"})])
    datos["horas"] = {"docencia": 10}
    with pytest.raises(ErrorCompromiso, match="no en ambos"):
        calificar(datos)


def test_casos_de_compromisos_2023():
    casos = {p.stem: calificar(yaml.safe_load(p.read_text(encoding="utf-8")))
             for p in (EJEMPLOS / "compromisos_2023").glob("*.yaml")}
    pesos = {k: [round(a.declarado, 1) for a in r.ambitos] for k, r in casos.items()}
    assert pesos == {"caso1_asistente_gestion": [21.7, 72.5, 5.8],
                     "caso2_asociado_creacion": [33.8, 16.0, 32.1, 18.0],
                     "caso3_asociado_docencia": [47.4, 38.2, 10.5, 3.9]}


@pytest.mark.parametrize("motivo", ["enfermedad", "maternidad", "parental", "permiso_sin_goce", "comision_servicio"])
def test_ausencia_justificada_de_mas_de_5_meses_suspende_la_evaluacion(motivo):
    datos = academico({"docencia": 100}, [])
    datos["situacion_especial"] = {"motivo": motivo, "meses_ausencia": 6}
    r = calificar(datos)
    assert (r.estado, r.letra, r.puntaje) == ("suspendida", None, None)
    assert "Oficina de Evaluación de Desempeño Académico" in r.informar_a
    assert "SUSPENDIDA" in informe(r)


def test_otras_situaciones_se_evaluan_segun_el_porcentaje_de_jornada():
    datos = academico({"investigacion": 100}, [
        tarea("investigacion", "publicaciones", evidencia={"comprometido": 2, "logrado": 1})])
    datos["situacion_especial"] = {"motivo": "enfermedad", "meses_ausencia": 3, "porcentaje_jornada": 50}
    r = calificar(datos)
    assert r.estado == "calificada"
    assert r.ambitos[0].puntaje == 100          # meta de 2 ajustada a 1
    assert "meta ajustada a 1" in r.ambitos[0].tareas[0].detalle
    assert any("Informar a la Oficina" in o for o in r.observaciones)


def test_meta_ajustada_no_genera_excedente_si_no_supera_la_original():
    datos = academico({"investigacion": 100}, [
        tarea("investigacion", "publicaciones", evidencia={"comprometido": 2, "logrado": 2, "validado": True})])
    datos["situacion_especial"] = {"motivo": "comision_servicio", "porcentaje_jornada": 50}
    r = calificar(datos)
    assert r.ambitos[0].puntaje == 100 and not r.destacados


@pytest.mark.parametrize("situacion, mensaje", [
    ({"motivo": "vacaciones"}, "no válido"),
    ({"motivo": "permiso_sin_goce", "meses_ausencia": 3}, "porcentaje_jornada"),
    ({"motivo": "maternidad", "meses_ausencia": 5}, "porcentaje_jornada"),   # 5 meses no supera el límite
])
def test_errores_de_situacion_especial(situacion, mensaje):
    datos = academico({"docencia": 100}, [tarea("docencia", evidencia={"estado": "cumplido"})])
    datos["situacion_especial"] = situacion
    with pytest.raises(ErrorCompromiso, match=mensaje):
        calificar(datos)


def test_ejemplos():
    resultados = {p.stem: calificar(yaml.safe_load(p.read_text(encoding="utf-8")))
                  for p in EJEMPLOS.glob("*.yaml")}
    assert resultados["asistente_investigadora"].letra == "A+"
    assert resultados["asistente_investigadora"].puntaje == 102.4
    assert resultados["instructor_vinculador"].letra == "C"
    assert "CLASIFICACIÓN: A+" in informe(resultados["asistente_investigadora"])


@pytest.mark.parametrize("evidencia, puntaje, destaca", [
    ({"etapa_comprometida": "ejecucion", "etapa_evidenciada": "finalizada"}, 100, False),
    ({"etapa_comprometida": "enviada", "etapa_evidenciada": "enviada"}, 100, False),
    ({"etapa_comprometida": "enviada", "etapa_evidenciada": "publicada", "validado": True}, 100, True),
    ({"etapa_comprometida": "enviada", "etapa_evidenciada": "publicada"}, 100, False),
    ({"etapa_comprometida": "publicada", "etapa_evidenciada": "enviada"}, 50, False),
    ({"etapa_comprometida": "ejecucion"}, 0, False),
])
def test_evidencia_por_etapa(evidencia, puntaje, destaca):
    r = calificar(academico({"investigacion": 100}, [tarea("investigacion", "publicaciones", evidencia=evidencia)]))
    t = r.ambitos[0].tareas[0]
    assert (t.puntaje, t.destaca) == (puntaje, destaca)
    assert bool(r.destacados) == destaca


def test_etapas_de_secuencias_distintas_es_error():
    with pytest.raises(ErrorCompromiso, match="misma secuencia"):
        calificar(academico({"investigacion": 100}, [tarea("investigacion", evidencia={
            "etapa_comprometida": "postulacion", "etapa_evidenciada": "publicada"})]))


def test_reporte_del_compromiso():
    from seja.reportes import reporte_compromiso
    datos = yaml.safe_load((EJEMPLOS / "informes_2023" / "caso4_titular_cierre.yaml").read_text(encoding="utf-8"))
    texto = reporte_compromiso(datos)
    assert "# Reporte: Compromiso de Desempeño Académico 2023" in texto
    assert "| Investigación, Creación e Innovación | 14 | 31,8% | 25,5% |" in texto
    assert "## Alertas para la jefatura" in texto and "entre 30% y 50%" in texto


def test_informe_de_cierre():
    from seja.reportes import informe_cierre
    datos = yaml.safe_load((EJEMPLOS / "informes_2023" / "caso4_titular_cierre.yaml").read_text(encoding="utf-8"))
    texto = informe_cierre(datos)
    assert "Calificación A" in texto and "## Reconocimiento institucional" in texto
    assert "| Liderar proyectos de investigación, innovación o creación competitivos | Sí |" in texto
    assert "| Acreditar formación continua | No declarada |" in texto
    datos["situacion_especial"] = {"motivo": "estudios", "meses_ausencia": 8}
    assert "## Evaluación suspendida" in informe_cierre(datos)


def test_informe_del_ejercicio_2023_es_anonimo():
    from seja.ejercicio_2023.generar import generar
    texto = generar()
    assert "### Sujeto 01" in texto and "### Sujeto 09" in texto
    assert "C_{E1}" in texto and r"w_a = \frac{h_a}{\sum_{b} h_b}" in texto
    for nombre in ["Matemática", "Artes Visuales", "Kinesiología", "Música", "DIUMCE", "FONDECYT"]:
        assert nombre not in texto
