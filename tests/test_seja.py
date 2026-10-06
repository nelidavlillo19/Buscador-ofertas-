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


@pytest.mark.parametrize("puntaje, letra", [(90, "A"), (89.9, "B"), (75, "B"), (60, "C"), (59.9, "D"), (0, "D")])
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


def test_ejemplos():
    resultados = {p.stem: calificar(yaml.safe_load(p.read_text(encoding="utf-8")))
                  for p in EJEMPLOS.glob("*.yaml")}
    assert resultados["asistente_investigadora"].letra == "A+"
    assert resultados["asistente_investigadora"].puntaje == 104.2
    assert resultados["instructor_vinculador"].letra == "C"
    assert "CLASIFICACIÓN: A+" in informe(resultados["asistente_investigadora"])
