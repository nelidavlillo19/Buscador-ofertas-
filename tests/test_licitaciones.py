from pathlib import Path

import yaml

from ofertas import licitaciones as lic

CONFIG = yaml.safe_load((Path(__file__).resolve().parent.parent / "config" / "licitaciones.yaml")
                        .read_text(encoding="utf-8"))

ACTIVAS = [
    {"CodigoExterno": "1391828-4-LP26", "Nombre": "Auditorías contables SSR 2026", "CodigoEstado": 5,
     "FechaCierre": "2026-11-20T15:00:00"},
    {"CodigoExterno": "2-L126", "Nombre": "Asesoría técnica pedagógica en convivencia escolar",
     "FechaCierre": "2026-11-18T15:00:00"},
    {"CodigoExterno": "3-LE26", "Nombre": "Construcción de sede social y estudio de suelo",
     "FechaCierre": "2026-11-25T15:00:00"},
    {"CodigoExterno": "4-LE26", "Nombre": "Suministro de alimentos para casino", "FechaCierre": None},
]


def detalle(organismo, region="Región de Valparaíso", monto=15000000):
    return {"Comprador": {"NombreOrganismo": organismo, "NombreUnidad": "Unidad de compras",
                          "RegionUnidad": region},
            "Tipo": "LE", "MontoEstimado": monto, "Moneda": "CLP", "Descripcion": "Servicio de asesoría",
            "Fechas": {"FechaCierre": "2026-11-21T16:00:00"}}


def test_candidatas_filtra_por_nombre_sin_tildes_y_excluye_obras():
    codigos = [x.codigo for x in lic.candidatas(ACTIVAS, CONFIG)]
    assert codigos == ["1391828-4-LP26", "2-L126"]


def test_completar_y_organismos_de_interes():
    a = lic.completar(lic.Licitacion("1", "Auditoría"), detalle("MINISTERIO DE OBRAS PUBLICAS"))
    assert (a.region, a.tipo, a.monto, a.cierre) == ("Región de Valparaíso", "LE", 15000000.0, "2026-11-21T16:00")
    assert lic.es_de_interes(a, CONFIG)
    slep = lic.completar(lic.Licitacion("2", "Asesoría"), detalle("Servicio Local de Educación Marga Marga"))
    assert lic.es_de_interes(slep, CONFIG)
    muni = lic.completar(lic.Licitacion("3", "Asesoría"), detalle("I MUNICIPALIDAD DE QUILPUE"))
    assert not lic.es_de_interes(muni, CONFIG)


def test_ordena_regiones_destacadas_primero():
    lejos = lic.completar(lic.Licitacion("a", "x"), detalle("Ministerio", "Región de Aysén"))
    cerca = lic.completar(lic.Licitacion("b", "x"), detalle("Ministerio", "Región de Valparaíso"))
    assert [x.codigo for x in lic.ordenar([lejos, cerca], CONFIG)] == ["b", "a"]


def test_vistas_y_correo(tmp_path):
    ruta = tmp_path / "vistas.json"
    nueva = lic.completar(lic.Licitacion("1-LE26", "Auditoría <externa>"), detalle("Subsecretaría de Educación"))
    lic.guardar_vistas(ruta, {"viejo": "2026-01-01"}, [nueva], "2026-11-09")
    vistas = lic.cargar_vistas(ruta)
    assert vistas == {"1-LE26": "2026-11-09"}  # la de hace más de 120 días se olvida
    asunto, texto, cuerpo = lic.correo([nueva], 1, "2026-11-09")
    assert "1 licitación" in asunto and "1-LE26" in texto
    assert "&lt;externa&gt;" in cuerpo and "$15.000.000" in cuerpo


def test_buscar_completo_con_api_simulada(monkeypatch):
    class Resp:
        status_code = 200

        def __init__(self, datos):
            self._datos = datos

        def json(self):
            return self._datos

    class Sesion:
        headers: dict = {}

        def get(self, url, params, timeout):
            if params.get("estado") == "activas":
                return Resp({"Cantidad": len(ACTIVAS), "Listado": ACTIVAS})
            org = {"1391828-4-LP26": "MINISTERIO DE OBRAS PUBLICAS", "2-L126": "I MUNICIPALIDAD DE QUILPUE"}
            return Resp({"Listado": [detalle(org[params["codigo"]])]})

    import requests
    monkeypatch.setattr(requests, "Session", Sesion)
    vigentes, activas = lic.buscar("ticket", CONFIG, pausa=0)
    assert activas == 4 and [x.codigo for x in vigentes] == ["1391828-4-LP26"]
    assert "1391828-4-LP26" in lic.estado_markdown(vigentes, "2026-11-09", activas)
