"""Datos simulados para previsualizar el panel antes de tener historial real."""
from __future__ import annotations

import random
import zlib
from datetime import date, timedelta

from . import db
from .modelos import Producto

EJEMPLOS = {
    "pelicula_instax_mini": [("Película Instax Mini pack 20 fotos", 16990), ("Película Instax Mini 10 fotos", 8990)],
    "alimento_mascotas": [("Alimento perro adulto 15 kg", 42990), ("Alimento gato adulto 7,5 kg", 32990)],
    "juguetes_mascotas": [("Pelota de goma para perro", 5990), ("Rascador para gato 60 cm", 24990)],
    "juguetes_ninos": [("Bloques de madera 50 piezas", 15990), ("Puzzle encaje animales", 8990)],
    "compotas": [("Compota manzana pouch 90 g", 890), ("Compota pera-plátano 4 un.", 2990)],
    "jugos_sin_azucar": [("Jugo manzana sin azúcar 200 ml x6", 3290)],
    "cereales_infantiles": [("Cereal avena infantil 400 g", 3990), ("Cereal aros sin azúcar 300 g", 3490)],
    "barritas": [("Barrita de fruta 5 un.", 2890), ("Barra cereal avena-miel 6 un.", 2590)],
    "galletas_colacion": [("Galletas de arroz 100 g", 1590), ("Galletas avena integrales 6 un.", 2190)],
    "calzado_mujer": [("Zapatillas running mujer", 59990), ("Botín de cuero mujer", 69990)],
    "ropa_nina_t2": [("Vestido algodón niña", 14990), ("Pijama polar niña", 16990)],
    "ropa_nino_t6": [("Polerón con capucha niño", 19990), ("Pantalón buzo niño", 12990)],
    "traje_bano_nina_t2": [("Traje de baño UV niña", 17990)],
    "traje_bano_nino_t6": [("Short de baño niño", 12990)],
    "crema_cuerpo_ninos": [("Crema corporal infantil 400 ml", 6490)],
    "calzado_ergonomico": [("Zapato barefoot infantil", 39990)],
    "organizacion_hogar": [("Cajonera organizadora 4 cajones", 29990), ("Repisa modular 3 niveles", 34990)],
    "robot_cocina": [("Robot de cocina multifunción", 399990)],
    "cafe_grano": [("Café de grano tostado 1 kg", 18990), ("Café de grano orgánico 500 g", 11990)],
    "cafeteras": [("Cafetera espresso con molinillo", 499990), ("Cafetera espresso 15 bar", 189990)],
}


def generar(con, config: dict, dias: int = 90, semilla: int = 7) -> str:
    rnd = random.Random(semilla)
    tiendas = [t for t in config["tiendas"] if t.get("activa", True)]
    fin = date.today()
    for cid, ejemplos in EJEMPLOS.items():
        candidatas = [t for t in tiendas if cid in (t.get("categorias") or [cid])] or tiendas[:1]
        for nombre, base in ejemplos:
            for tienda in rnd.sample(candidatas, k=min(2, len(candidatas))):
                sku = f"demo-{cid}-{zlib.crc32((nombre + tienda['id']).encode()) % 10**6}"
                normal = round(base * rnd.uniform(0.9, 1.1), -1)
                promo_hasta = -1
                for i in range(dias):
                    dia = fin - timedelta(days=dias - 1 - i)
                    if i > promo_hasta and rnd.random() < 0.04:
                        promo_hasta, corte = i + rnd.randint(2, 6), rnd.choice([0.1, 0.2, 0.3, 0.4, 0.5])
                    if rnd.random() < 0.02:
                        normal = round(normal * rnd.uniform(1.0, 1.08), -1)  # alza de precio
                    en_promo = i <= promo_hasta
                    precio = round(normal * (1 - corte), -1) if en_promo else normal
                    db.guardar(con, Producto(
                        tienda=tienda["id"], sku=sku, nombre=nombre, url=tienda["url"], precio=precio,
                        precio_lista=normal if en_promo else None, categoria=cid,
                    ), dia.isoformat())
    con.commit()
    return fin.isoformat()
