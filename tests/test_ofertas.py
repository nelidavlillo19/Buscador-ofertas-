from datetime import date, timedelta

from ofertas import alertas, db
from ofertas.adapters.jsonld import extraer_productos
from ofertas.adapters.shopify import Shopify
from ofertas.adapters.vtex import Vtex
from ofertas.filtros import aplicar_filtro, clasificar
from ofertas.modelos import Producto, Variante

TIENDA = {"id": "t", "url": "https://tienda.cl"}


def test_shopify_toma_variante_mas_barata_disponible():
    p = Shopify(TIENDA, None)._producto({
        "id": 1, "title": "Polera niña", "handle": "polera", "vendor": "X",
        "images": [{"src": "//cdn/img.jpg"}],
        "variants": [
            {"title": "2", "price": "9990.00", "compare_at_price": "14990.00", "available": True},
            {"title": "4", "price": "5990.00", "compare_at_price": None, "available": False},
        ],
    })
    assert (p.precio, p.precio_lista) == (9990, 14990)
    assert (p.url, p.imagen) == ("https://tienda.cl/products/polera", "https://cdn/img.jpg")
    assert p.descuento_declarado == 33.4


def test_shopify_js_en_centavos():
    p = Shopify(TIENDA, None)._producto(
        {"id": 2, "title": "Zapato", "handle": "z", "variants": [{"title": "22", "price": 3999000,
                                                                   "compare_at_price": 4999000}]},
        centavos=True)
    assert (p.precio, p.precio_lista) == (39990, 49990)


def test_vtex_lee_price_y_listprice():
    p = Vtex(TIENDA, None)._producto({
        "productId": "55", "productName": "Compota manzana", "brand": "B", "link": "https://tienda.cl/compota/p",
        "items": [{"name": "90 g", "images": [{"imageUrl": "i.jpg"}],
                   "sellers": [{"commertialOffer": {"Price": 690, "ListPrice": 990, "AvailableQuantity": 10}}]}],
    })
    assert (p.sku, p.precio, p.precio_lista, p.disponible) == ("55", 690, 990, True)


def test_jsonld_itemlist():
    html = """<script type="application/ld+json">{"@type":"ItemList","itemListElement":[
      {"@type":"ListItem","item":{"@type":"Product","name":"Café grano 1kg","sku":"A1","url":"/cafe",
       "offers":{"@type":"Offer","price":"15990","availability":"InStock"}}}]}</script>"""
    [p] = extraer_productos(html, "t", "https://tienda.cl")
    assert (p.nombre, p.sku, p.precio, p.url) == ("Café grano 1kg", "A1", 15990, "https://tienda.cl/cafe")


def test_filtro_tallas_ajusta_precio_y_no_confunde_12_con_2():
    cat = {"incluir": ["niña"], "tallas": ["2"]}
    p = Producto("t", "1", "Vestido Nina", "u", 5000, variantes=[
        Variante("12", 5000), Variante("2", 8000, 12000), Variante("24M", 4000)])
    assert aplicar_filtro(p, cat).precio == 8000
    sin_talla = Producto("t", "2", "Vestido niña", "u", 5000, variantes=[Variante("12", 5000)])
    assert aplicar_filtro(sin_talla, cat) is None


def test_clasificar_respeta_excluir():
    cats = {"juguetes_mascotas": {"incluir": ["juguete"], "excluir": []},
            "juguetes_ninos": {"incluir": ["juguete"], "excluir": ["perro"]}}
    p = Producto("t", "1", "Juguete didáctico", "u", 1000)
    assert clasificar(p, cats, ["juguetes_ninos"]) == "juguetes_ninos"
    p2 = Producto("t", "2", "Juguete perro", "u", 1000)
    assert clasificar(p2, cats, ["juguetes_ninos"]) is None


def test_alertas_declarada_e_historica(tmp_path):
    con = db.conectar(tmp_path / "x.sqlite")
    hoy = date(2026, 9, 29)
    for i in range(10, 0, -1):
        dia = (hoy - timedelta(days=i)).isoformat()
        db.guardar(con, Producto("t", "a", "Cafetera", "u", 100000, categoria="cafeteras"), dia)
        db.guardar(con, Producto("t", "b", "Galletas", "u", 1000, categoria="galletas_colacion"), dia)
    # a: baja real 40% sin anuncio; b: "oferta" inflada (lista 2000) que no es real vs historial
    db.guardar(con, Producto("t", "a", "Cafetera", "u", 60000), hoy.isoformat())
    db.guardar(con, Producto("t", "b", "Galletas", "u", 1000, precio_lista=2000), hoy.isoformat())
    res = {(a.producto_id, a.tipo): a.descuento for a in alertas.detectar(con, hoy.isoformat(), 30, 60)}
    assert res == {("t:a", "historico"): 40.0, ("t:b", "declarado"): 50.0}


def test_alerta_no_se_repite_al_dia_siguiente(tmp_path):
    con = db.conectar(tmp_path / "x.sqlite")
    for dia, precio in [("2026-09-28", 500), ("2026-09-29", 500), ("2026-09-30", 400)]:
        db.guardar(con, Producto("t", "a", "Barrita", "u", precio, precio_lista=1000), dia)
    nuevas = [[a.nueva for a in alertas.detectar(con, d, 30, 60)] for d in ("2026-09-28", "2026-09-29", "2026-09-30")]
    assert nuevas == [[True], [False], [True]]  # vuelve a avisar sólo si baja más
