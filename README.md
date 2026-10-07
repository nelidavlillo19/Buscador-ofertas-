# 🛒 Buscador de Ofertas familiar

Un buscador como kanasta.cl pero sólo con los productos que le interesan a la familia. Todos los días:

1. **Revisa las tiendas** (Pichintun, Colloky, Uma Baby, Casa Ideas, SuperZoo, Jumbo, Santa Isabel, Unimarc…).
2. **Guarda el precio** de cada producto de interés en una base de datos (`data/precios.sqlite`).
3. **Genera alertas** cuando un producto tiene **30% de descuento o más**, de dos maneras:
   - **Según la tienda**: precio oferta vs. precio normal publicado.
   - **Según el historial**: precio de hoy vs. su *precio habitual* (mediana de los últimos 60 días).
     Así se detectan ofertas reales aunque no se anuncien, y se evitan los "precios normales" inflados.
   - **Protección anti ofertas infladas** (útil antes del CyberDay): un descuento anunciado sólo cuenta si el
     precio queda bajo el **precio más bajo de los últimos 30 días**. Las "ofertas" sobre precios que subieron
     hace poco y los productos que subieron 10%+ aparecen en la sección **Vigilancia de precios** del correo
     y del panel.
4. **Respalda** los datos: un CSV comprimido por día (`data/respaldos/AAAA/`) y copias de la base completa
   de los últimos 7 días (`data/respaldos/base/`). Además, cada día queda guardado como commit en GitHub.
5. **Arma un panel web** con las ofertas del día, estadísticas y el gráfico de precio de cada producto.
6. **Avisa** por Telegram y/o correo (sólo ofertas nuevas, o que bajaron todavía más).

## Productos que se siguen

Se configuran en [`config/productos.yaml`](config/productos.yaml):

| Categoría | Ejemplos |
|---|---|
| IKEA | ofertas de 30%+ **y todo lo que cueste $10.000 o menos**; ⭐ peluches destacados |
| Casa Ideas | juguetes, rompecabezas/puzzles, libros de actividades, dinosaurios, organización |
| Hogar | pintura antihongos (Sodimac, Easy) |
| Tecnología | cargador portátil de celular / power bank (Falabella, IKEA, Sodimac, Casa Ideas) |
| Fotos | película **Polaroid i-Type y 600** (cualquier oferta), cubo de fotos giratorio |
| Juegos | autos Mario Kart Hot Wheels, Cuboro, escalera de cuerda / trapecio / columpio / presas de escalada, kits de mostacillas, sillas infantiles |
| Hogar | limpiapiés, muebles de bambú (baño, zapatero) |
| Lácteos niños | Yoguito con y sin bombilla (Jumbo, Santa Isabel) |
| Jugos | jugo de naranja Quillayes (Jumbo, Santa Isabel, Falabella) |
| Colaciones bebé | Kuna Foods, Baby Mum-Mum, Smiley Kids, AMA, NaturNes, Nestum |
| Más juguetes | Mini Color Stack, Nee Doh, sets de Super Mario, muñecas Nenuco, cocina de juguete de madera, FocuSwing |
| Baño y limpieza | set Mr. Bubble, quitamanchas KH-7 |
| 🧳 Viaje (**cada 6 horas, correo propio**) | maleta de cabina, organizadores de equipaje, banano / porta documentos (Falabella, Líder, Tottus, Casa Ideas, IKEA, Casa Royal) |
| 🥾 Trekking | zapatillas y botas de trekking, mochilas y bastones (Falabella, Líder, Tottus, Casa Royal; Decathlon bloquea) |
| Fotografía | película Instax Mini (**avisa cualquier oferta** y todo pack donde **cada foto cueste menos de $1.000**) |
| Mascotas | alimento de perro y gato, juguetes para mascotas |
| Niños | juguetes, ropa de niña **talla 2**, ropa de niño **talla 6**, trajes de baño (niña T2, niño T6), crema de cuerpo para niños, calzado ergonómico tipo Uma Baby |
| Bebé | pañales Pampers talla XXG (supermercados, Falabella y farmacias Cruz Verde, Salcobrand y Ahumada; **cualquier oferta**) |
| Colaciones | compotas, cajitas de jugo sin azúcar, cereales para 2 años, barritas tipo Mizo, galletas |
| Mujer | zapatillas y calzado |
| Hogar | muebles y organización, robot de cocina, café de grano, cafeteras tipo profesional |

**Para agregar productos nuevos** copia un bloque en `config/productos.yaml`:

```yaml
  panales:
    nombre: Pañales
    buscar: [pañales talla g, pañal g]   # lo que se escribe en el buscador de cada tienda
    incluir: [pañal]                      # el nombre debe tener alguna de estas palabras
    excluir: [toallitas]                  # y ninguna de éstas
```

y agrega `panales` a la lista `categorias` de las tiendas donde quieras buscarlo en
[`config/tiendas.yaml`](config/tiendas.yaml). Para la ropa y el calzado, `tallas` deja sólo las variantes
de esa talla (y usa su precio).

## Cómo funciona con cada tienda

No hace falta programar un lector por tienda: la mayoría de las tiendas chilenas usa **Shopify** o **VTEX**,
que tienen catálogos públicos en formato JSON. Con `plataforma: auto` el programa lo detecta solo, y si no es
ninguna de las dos lee los datos de producto estándar (schema.org) de la página de búsqueda.

Para comprobar una tienda:

```bash
python -m ofertas probar colloky "polera niña"
```

Si una tienda arma su página sólo con JavaScript, instala Playwright (`pip install playwright &&
playwright install chromium`) y ejecuta con `OFERTAS_NAVEGADOR=1`. Líder viene pausada (`activa: false`)
porque bloquea a los programas automáticos.

## Uso en tu computador

```bash
pip install -r requirements.txt
python -m ofertas rastrear          # revisa todo, alerta, respalda y genera sitio/index.html
python -m ofertas rastrear --tienda superzoo --sin-avisos   # sólo una tienda, sin mandar avisos
python -m ofertas demo              # panel con datos simulados en sitio-demo/
```

Para ver el panel: `python -m http.server -d sitio 8000` y abre http://localhost:8000.

## Ejecución diaria automática (gratis, con GitHub)

El archivo [`.github/workflows/diario.yml`](.github/workflows/diario.yml) lo ejecuta todos los días
a las ~7:17 de Chile, guarda los datos en el repositorio y publica el panel en GitHub Pages.

1. Sube este proyecto a un repositorio de GitHub.
2. En **Settings → Pages**, en *Source* elige **GitHub Actions**.
   (Si el repositorio es privado, Pages requiere un plan pagado; el panel igual se puede ver en local.)
3. Opcional, en **Settings → Secrets and variables → Actions**, agrega los avisos:
   - Telegram: `TELEGRAM_BOT_TOKEN` (créalo con @BotFather) y `TELEGRAM_CHAT_ID`.
   - Correo (Gmail): `GMAIL_USUARIO` (tu correo) y `GMAIL_CLAVE_APP` (una *contraseña de aplicación*
     de Google). Opcional: `CORREO_DESTINO` si quieres recibir las alertas en otro correo.
   - Variable `URL_PANEL` con la dirección del panel para incluirla en los avisos.
4. En **Actions → Rastreo diario de precios → Run workflow** puedes lanzarlo a mano la primera vez.

Las alertas "según el historial" empiezan a aparecer cuando cada producto lleva al menos 7 días de precios.

## Estructura

```
config/            tiendas y productos de interés (lo único que normalmente se edita)
ofertas/adapters/  lectores Shopify, VTEX y schema.org
ofertas/alertas.py detección de ofertas y avisos
ofertas/respaldo.py respaldo diario
ofertas/panel.py   datos del panel;  web/index.html  el panel
data/              base de datos, alertas diarias (data/alertas/) y respaldos
tests/             pruebas (python -m pytest)
```

Buenas prácticas: el programa espera 1,5 s entre peticiones a una misma tienda y consulta una vez al día.

## Calificación académica SEJA

El directorio [`seja/`](seja) contiene el motor de calificación académica SEJA-UMCE (ámbitos, tareas, autoevaluación, evaluación de estudiantes y clasificación A+ a D). Ver [`seja/README.md`](seja/README.md).
