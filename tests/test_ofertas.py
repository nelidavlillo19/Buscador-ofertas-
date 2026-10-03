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


def test_traje_bano_exige_tipo_y_genero_y_talla():
    import yaml
    cats = yaml.safe_load(open("config/productos.yaml", encoding="utf-8"))["categorias"]
    traje = Producto("t", "1", "Traje de Baño UV Niña Flores", "u", 9990,
                     variantes=[Variante("2", 9990), Variante("4", 8990)])
    assert clasificar(traje, cats, None) == "traje_bano_nina_t2"
    polera = Producto("t", "2", "Polera niña manga corta", "u", 5990, variantes=[Variante("2", 5990)])
    assert clasificar(polera, cats, None) == "ropa_nina_t2"
    crema = Producto("t", "3", "Crema hidratante corporal infantil 400 ml", "u", 5990)
    assert clasificar(crema, cats, None) == "crema_cuerpo_ninos"


def test_instax_avisa_cualquier_oferta(tmp_path):
    import yaml
    cats = yaml.safe_load(open("config/productos.yaml", encoding="utf-8"))["categorias"]
    film = Producto("t", "f", "Fujifilm Instax Mini Film Pack 20 fotos", "u", 15990, precio_lista=16990)
    camara = Producto("t", "c", "Cámara Instax Mini 12", "u", 69990)
    assert clasificar(film, cats, None) == "pelicula_instax_mini"
    assert clasificar(camara, cats, None) is None
    con = db.conectar(tmp_path / "x.sqlite")
    film.categoria = "pelicula_instax_mini"
    db.guardar(con, film, "2026-09-30")
    db.guardar(con, Producto("t", "g", "Galletas", "u", 900, precio_lista=1000, categoria="galletas_colacion"),
               "2026-09-30")
    res = alertas.detectar(con, "2026-09-30", 30, 60, cats)
    assert [(a.producto_id, a.descuento) for a in res] == [("t:f", 5.9)]  # galletas -10% no alcanza el 30%


def test_talla_no_confunde_meses_con_anios():
    from ofertas.filtros import _talla_coincide
    seis = ["6", "6A", "6 años", "6T"]
    assert _talla_coincide("5-6A", seis) and _talla_coincide("6-7A", seis) and _talla_coincide("6 años", seis)
    assert not _talla_coincide("6-9M", seis) and not _talla_coincide("3-6M", seis) and not _talla_coincide("6M", seis)


def test_aviso_limita_por_categoria_y_un_aviso_por_producto():
    muchas = [alertas.Alerta(f"t:{i}", "declarado", 50, 1, 2, categoria="calzado") for i in range(20)]
    muchas += [alertas.Alerta("t:x", "declarado", 40, 1, 2, categoria="cafe"),
               alertas.Alerta("t:x", "historico", 45, 1, 2, categoria="cafe")]
    elegidas = alertas.seleccionar_para_aviso(muchas)
    assert len(elegidas) == 6 and [a.tipo for a in elegidas if a.producto_id == "t:x"] == ["historico"]


def test_sfcc_superzoo_oferta_y_rango():
    from ofertas.adapters.sfcc import extraer
    tarjeta = '''<div class="product" data-pid="{pid}" data-url="x"><div class="product-tile">
      <img class="tile-image" src="/img.jpg"/><span class="product-brand text-micro">Marca</span>
      <div class="pdp-link"><a class="link" href="/p/{pid}.html"><h2 class="text-base">Alimento perro {pid}</h2></a></div>
      <div class="price">{precio}</div><!-- END_dwmarker -->'''
    oferta = ('<span><del><span class="strike-through list"><span class="value" content="64990">$64.990</span>'
              '</span></del><span class="sales"><span class="value" content="39990">$39.990</span></span></span>')
    rango = ('<span class="range"><span class="sales"><span class="value" content="26341"></span></span> - '
             '<span class="sales"><span class="value" content="59990"></span></span></span>')
    a, b = extraer(tarjeta.format(pid="A", precio=oferta) + tarjeta.format(pid="B", precio=rango), "sz", "https://s.cl")
    assert (a.precio, a.precio_lista, a.url) == (39990, 64990, "https://s.cl/p/A.html")
    assert (b.precio, b.precio_lista) == (26341, None)


def test_falabella_next_data_ignora_precio_cmr():
    import json
    from ofertas.adapters.falabella import extraer
    datos = {"props": {"pageProps": {"results": [{
        "skuId": "9", "displayName": "Pack de 20 Film Instax Mini", "url": "https://f/9", "brand": "FUJIFILM",
        "sellerName": "Dust2", "mediaUrls": ["https://img"],
        "prices": [{"type": "cmrPrice", "price": ["19.990"], "crossed": False},
                   {"type": "eventPrice", "price": ["21.990"], "crossed": False},
                   {"type": "normalPrice", "price": ["29.490"], "crossed": True}]}]}}}
    [p] = extraer(f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(datos)}</script>', "falabella")
    assert (p.precio, p.precio_lista, p.nombre) == (21990, 29490, "Pack de 20 Film Instax Mini (vende Dust2)")


def test_cencosud_render_data():
    import json
    from ofertas.adapters.cencosud import productos_render
    datos = {"plp": {"plp_products": {"products": [{"productId": "1", "productName": "Compota"}]}}}
    pagina = f"<script>window.__renderData = {json.dumps(json.dumps(datos))};</script>"
    assert productos_render(pagina)[0]["productName"] == "Compota"


def test_ikea_avisa_productos_bajo_10000_y_peluches_primero(tmp_path):
    import yaml
    cats = yaml.safe_load(open("config/productos.yaml", encoding="utf-8"))["categorias"]
    con = db.conectar(tmp_path / "x.sqlite")
    peluche = Producto("ikea", "p", "DJUNGELSKOG Peluche oso", "u", 9990)
    caja = Producto("ikea", "c", "Caja organizadora", "u", 4990)
    mueble = Producto("ikea", "m", "Estante", "u", 59990)
    assert clasificar(peluche, cats, None) == "peluches"
    peluche.categoria, caja.categoria, mueble.categoria = "peluches", "organizacion_hogar", "organizacion_hogar"
    for p in (caja, peluche, mueble):
        db.guardar(con, p, "2026-10-03")
    res = alertas.detectar(con, "2026-10-03", 30, 60, cats, {"ikea": {"alerta_precio_maximo": 10000}})
    assert sorted((a.producto_id, a.tipo) for a in res) == [("ikea:c", "precio_bajo"), ("ikea:p", "precio_bajo")]
    assert alertas.seleccionar_para_aviso(res, cats)[0].producto_id == "ikea:p"
