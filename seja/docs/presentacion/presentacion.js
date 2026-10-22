// Presentación del proceso de evaluación y del cálculo de la calificación SEJA.
// Uso: node presentacion.js SALIDA.pptx CARPETA_FORMULAS   (las fórmulas se generan con formulas.py)
const pptxgen = require("pptxgenjs");
const path = require("path");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

// apply_theme.js escribe la paleta en el tema del archivo; sin él, PowerPoint usa los colores de Office.
const SKILL = process.env.PPTX_SKILL_DIR;
const applyTheme = SKILL ? require(path.join(SKILL, "scripts/apply_theme.js")).applyTheme : null;

const [salida, carpetaFormulas] = process.argv.slice(2);

const THEME = {
  name: "SEJA",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2A49", lt1: "FFFFFF", dk2: "3A4A66", lt2: "EEF2F8",
    accent1: "1B2A49", accent2: "D9A21B", accent3: "2E7D8C", accent4: "7E93B3",
    accent5: "B8483E", accent6: "4F8A4C", hlink: "2E7D8C", folHlink: "5B6B85",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13,333 × 7,5 pulgadas
pres.title = "Modelo de Calificación Académica SEJA";
pres.author = "Oficina de Evaluación de Desempeño Académico";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

// ---------- Layouts ----------
pres.defineSlideMaster({
  title: "PORTADA",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.1, w: 8.6, h: 1.8, fontFace: THEME.headFontFace, fontSize: 40, bold: true, color: C.background1, valign: "bottom" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.05, w: 8.6, h: 1.6, fontSize: 18, color: C.background2, valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENIDO",
  background: { color: C.background1 },
  margin: [0.5, 0.6, 0.7, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.95, fontFace: THEME.headFontFace, fontSize: 32, bold: true, color: C.text1, valign: "middle" }, text: "" } },
    { text: { text: "SEJA · Modelo de Calificación Académica", options: { x: 0.6, y: 6.95, w: 6, h: 0.35, fontSize: 10, color: C.accent4 } } },
  ],
  slideNumber: { x: 12.2, y: 6.95, w: 0.6, h: 0.35, fontSize: 10, color: C.accent4, align: "right" },
});
pres.defineSlideMaster({
  title: "CIERRE",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.4, w: 12.1, h: 0.95, fontFace: THEME.headFontFace, fontSize: 32, bold: true, color: C.background1, valign: "middle" }, text: "" } },
  ],
  slideNumber: { x: 12.2, y: 6.95, w: 0.6, h: 0.35, fontSize: 10, color: C.background2, align: "right" },
});

// ---------- Utilidades ----------
async function icono(Icon, hex, px = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Icon, { color: "#" + hex, size: px }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

// Motivo de la presentación: ícono blanco dentro de un círculo de color.
async function circuloIcono(slide, Icon, x, y, d, color, nombre) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color }, line: { color, width: 0 }, objectName: nombre + " círculo" });
  const pad = d * 0.25;
  slide.addImage({ data: await icono(Icon, HEX.lt1), x: x + pad, y: y + pad, w: d - 2 * pad, h: d - 2 * pad, objectName: nombre + " ícono" });
}

function formula(slide, nombre, x, y, h, maxW) {
  const { size } = formulas[nombre];
  let w = (h * size[0]) / size[1];
  if (maxW && w > maxW) { h = (h * maxW) / w; w = maxW; }
  slide.addImage({ path: formulas[nombre].ruta, x, y, w, h, objectName: "Fórmula " + nombre });
  return { w, h };
}

function tarjeta(slide, x, y, w, h, nombre, fill) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: 0.12, fill: { color: fill || C.background2 }, line: { color: fill || C.background2, width: 0 },
    objectName: nombre,
  });
}

function texto(slide, t, opts) {
  slide.addText(t, { isTextBox: true, margin: 0, color: C.text1, fontSize: 15, valign: "top", ...opts });
}

const formulas = {};

async function main() {
  for (const n of ["pauta", "escala", "meta", "excedente", "ambito", "horas", "peso", "compromiso", "final", "factor"]) {
    const ruta = path.join(carpetaFormulas, n + ".png");
    const meta = await sharp(ruta).metadata();
    formulas[n] = { ruta, size: [meta.width, meta.height] };
  }

  // 1. Portada
  pres.addSection({ title: "Introducción" });
  let s = pres.addSlide({ masterName: "PORTADA", sectionTitle: "Introducción" });
  s.addText("Modelo de Calificación Académica SEJA", { placeholder: "title" });
  s.addText([
    { text: "Cómo se evalúa el desempeño académico y cómo se determina la calificación final", options: { breakLine: true } },
    { text: "Oficina de Evaluación de Desempeño Académico · Vicerrectoría Académica", options: { fontSize: 14, color: C.accent4 } },
  ], { placeholder: "body" });
  await circuloIcono(s, fa.FaBalanceScale, 10.0, 2.35, 2.4, C.accent2, "Portada");
  s.addNotes("Presentación del modelo con que el SEJA califica el desempeño académico a partir del Compromiso de Desempeño.");

  // 2. Tres niveles
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Introducción" });
  s.addText("De la tarea a la calificación final", { placeholder: "title" });
  const niveles = [
    [fa.FaTasks, "Tarea", "Cada actividad comprometida: un curso, un proyecto, una publicación, una coordinación.", "Se evalúa con un instrumento o con la evidencia de la carpeta individual.", "pₜ"],
    [fa.FaLayerGroup, "Ámbito", "Docencia · Investigación, Creación e Innovación · Vinculación con el Medio · Gestión Académica.", "Promedio de las tareas del ámbito.", "Sₐ"],
    [fa.FaFlagCheckered, "Calificación final", "80% ámbitos ponderados por horas, 10% autoevaluación y 10% evaluación de estudiantes.", "Se clasifica en A+, A, B, C o D.", "F"],
  ];
  for (let i = 0; i < 3; i++) {
    const x = 0.6 + i * 4.2;
    tarjeta(s, x, 1.65, 3.7, 4.0, "Nivel " + niveles[i][1]);
    await circuloIcono(s, niveles[i][0], x + 0.35, 1.95, 0.9, i === 2 ? C.accent2 : C.text1, "Nivel " + niveles[i][1]);
    texto(s, niveles[i][4], { x: x + 2.2, y: 2.0, w: 1.2, h: 0.8, fontFace: "Cambria", fontSize: 32, italic: true, color: C.accent3, align: "right" });
    texto(s, niveles[i][1], { x: x + 0.35, y: 3.05, w: 3.0, h: 0.5, fontSize: 22, bold: true });
    texto(s, niveles[i][2], { x: x + 0.35, y: 3.6, w: 3.0, h: 1.2, fontSize: 15 });
    texto(s, niveles[i][3], { x: x + 0.35, y: 4.8, w: 3.0, h: 0.75, fontSize: 15, color: C.accent3, bold: true });
    if (i < 2) s.addShape(pres.shapes.CHEVRON, { x: x + 3.8, y: 3.4, w: 0.3, h: 0.5, fill: { color: C.accent4 }, line: { color: C.accent4, width: 0 }, objectName: "Flecha " + i });
  }
  texto(s, "Cada persona compromete sus propias actividades y horas: no hay una ponderación única.", { x: 0.6, y: 6.0, w: 12.1, h: 0.5, fontSize: 16, italic: true, color: C.text2 });
  s.addNotes("La calificación se construye en tres niveles. La flexibilidad está en que cada compromiso define sus propias tareas y horas.");

  // 3. Ciclo
  pres.addSection({ title: "Proceso" });
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Proceso" });
  s.addText("El ciclo de evaluación", { placeholder: "title" });
  const pasos = [
    [fa.FaFileSignature, "Compromiso", "Actividades, horas y metas; visto bueno de la jefatura"],
    [fa.FaFolderOpen, "Evidencias", "Se suben a la carpeta individual (Drive)"],
    [fa.FaClipboardCheck, "Instrumentos", "Estudiantes, dirección, autoevaluación y direcciones"],
    [fa.FaCalculator, "Calificación", "La Oficina calcula tareas, ámbitos y resultado final"],
    [fa.FaUsers, "Comisión Central", "Revisa el expediente y registra el acta"],
    [fa.FaEnvelopeOpenText, "Notificación", "Informe escrito y plazo de apelación"],
  ];
  s.addShape(pres.shapes.LINE, { x: 1.4, y: 2.55, w: 10.6, h: 0, line: { color: C.accent4, width: 2 }, objectName: "Línea del ciclo" });
  for (let i = 0; i < pasos.length; i++) {
    const cx = 0.6 + i * 2.05;
    await circuloIcono(s, pasos[i][0], cx + 0.4, 1.85, 1.4, i === 3 ? C.accent2 : C.text1, "Paso " + (i + 1));
    texto(s, `${i + 1}. ${pasos[i][1]}`, { x: cx, y: 3.45, w: 2.2, h: 0.5, fontSize: 17, bold: true, align: "center" });
    texto(s, pasos[i][2], { x: cx + 0.05, y: 4.0, w: 2.1, h: 1.4, fontSize: 14, color: C.text2, align: "center" });
  }
  tarjeta(s, 0.6, 5.6, 12.1, 0.95, "Nota del ciclo");
  texto(s, "Durante el año, el compromiso puede modificarse con nueva aprobación de la jefatura. El cálculo usa la última versión aprobada.", { x: 0.9, y: 5.75, w: 11.5, h: 0.65, fontSize: 15, valign: "middle" });
  s.addNotes("Seis etapas, desde la declaración del compromiso hasta la notificación. La Oficina coordina instrumentos y cálculo; la Comisión Central decide.");

  // 4. Ámbitos
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Proceso" });
  s.addText("Cuatro ámbitos de desempeño", { placeholder: "title" });
  const ambitos = [
    [fa.FaChalkboardTeacher, "Docencia", "Pregrado y postgrado, dirección de tesis y memorias, prácticas, tutoría, ayudantes, formación continua"],
    [fa.FaFlask, "Investigación, Creación e Innovación", "Proyectos, artículos, libros, obra artística, patentes, ponencias, redes, postulación a fondos, claustros"],
    [fa.FaHandshake, "Vinculación con el Medio y Extensión", "Programas, proyectos e iniciativas de VcM, educación continua, difusión, representación institucional"],
    [fa.FaSitemap, "Gestión Académica", "Dirección y coordinaciones, gestión curricular, comisiones, aseguramiento de la calidad"],
  ];
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + (i % 2) * 6.15, y = 1.6 + Math.floor(i / 2) * 2.55;
    tarjeta(s, x, y, 5.95, 2.3, "Ámbito " + ambitos[i][1]);
    await circuloIcono(s, ambitos[i][0], x + 0.3, y + 0.35, 1.0, C.text1, "Ámbito " + ambitos[i][1]);
    texto(s, ambitos[i][1], { x: x + 1.55, y: y + 0.3, w: 4.2, h: 0.75, fontSize: 19, bold: true, valign: "middle" });
    texto(s, ambitos[i][2], { x: x + 1.55, y: y + 1.05, w: 4.2, h: 1.1, fontSize: 14, color: C.text2 });
  }
  s.addNotes("Cada actividad se registra en una subcategoría de un ámbito. La subcategoría define con qué instrumento o evidencia se evalúa.");

  // 5. Ponderación por horas
  pres.addSection({ title: "Cálculo" });
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Cálculo" });
  s.addText("Las horas del compromiso definen la ponderación", { placeholder: "title" });
  tarjeta(s, 0.6, 1.6, 5.7, 4.95, "Fórmulas de ponderación");
  texto(s, "Horas semanales del ámbito (promedio de semestres)", { x: 0.9, y: 1.8, w: 5.1, h: 0.4, fontSize: 15, bold: true });
  formula(s, "horas", 0.9, 2.25, 0.85);
  texto(s, "Peso del ámbito", { x: 0.9, y: 3.3, w: 5.1, h: 0.4, fontSize: 15, bold: true });
  formula(s, "peso", 0.9, 3.75, 1.0);
  texto(s, [
    { text: "Se alerta si las horas superan la jornada (44 h o 22 h).", options: { bullet: true, breakLine: true } },
    { text: "Y si la docencia queda fuera del rango de la jerarquía y el perfil.", options: { bullet: true } },
  ], { x: 0.9, y: 5.0, w: 5.2, h: 1.3, fontSize: 14, color: C.text2, paraSpaceAfter: 4 });
  s.addChart(pres.charts.BAR, [{ name: "Peso del ámbito", labels: ["Docencia (22 h)", "Investigación (12 h)", "Vinculación (4 h)", "Gestión (6 h)"], values: [50.0, 27.3, 9.1, 13.6] }], {
    x: 6.6, y: 1.6, w: 6.1, h: 4.95, barDir: "bar", showTitle: true, title: "Ejemplo: 44 h comprometidas → peso de cada ámbito (%)",
    titleFontSize: 14, titleColor: HEX.dk1, titleFontFace: "+mn-lt", chartColors: [HEX.accent3], showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: '0.0"%"', dataLabelFontSize: 13, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt",
    catAxisLabelColor: HEX.dk2, catAxisLabelFontSize: 13, catAxisLabelFontFace: "+mn-lt", catAxisOrientation: "maxMin",
    valAxisHidden: true, valAxisMaxVal: 60, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false,
  });
  s.addNotes("La ponderación no es fija: sale de las horas semanales de cada ámbito. Las actividades sin horas se evalúan, pero no ponderan.");

  // 6. Evaluación de tareas
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Cálculo" });
  s.addText("Cada tarea se evalúa según su forma", { placeholder: "title" });
  const formas = [
    ["Pauta Cumple / No cumple / No aplica", "Instrumentos de estudiantes, dirección, autoevaluación y direcciones. Los «no aplica» no cuentan.", "pauta"],
    ["Instrumento con escala", "Puntaje x en una escala, por ejemplo una rúbrica de 1 a 4.", "escala"],
    ["Evidencia con meta", "M comprometido y L logrado; f es el factor de jornada (art. 37).", "meta"],
  ];
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + (i % 2) * 6.15, y = 1.6 + Math.floor(i / 2) * 2.55;
    tarjeta(s, x, y, 5.95, 2.3, "Forma " + i);
    if (i < 3) {
      texto(s, formas[i][0], { x: x + 0.3, y: y + 0.2, w: 5.4, h: 0.45, fontSize: 17, bold: true });
      texto(s, formas[i][1], { x: x + 0.3, y: y + 0.65, w: 5.4, h: 0.6, fontSize: 13, color: C.text2 });
      formula(s, formas[i][2], x + 0.3, y + 1.35, 0.75, 5.3);
    } else {
      texto(s, "Evidencia por etapa", { x: x + 0.3, y: y + 0.2, w: 5.4, h: 0.45, fontSize: 17, bold: true });
      texto(s, "Proyecto: postulación → adjudicación → ejecución → cierre. Publicación: enviada → aceptada → publicada.", { x: x + 0.3, y: y + 0.65, w: 5.4, h: 0.6, fontSize: 13, color: C.text2 });
      const etapas = [["100%", "Llega a la etapa", C.accent6], ["50%", "Etapa anterior", C.accent2], ["0%", "Sin evidencia", C.accent5]];
      for (let j = 0; j < 3; j++) {
        texto(s, etapas[j][0], { x: x + 0.3 + j * 1.8, y: y + 1.35, w: 1.7, h: 0.5, fontSize: 24, bold: true, color: etapas[j][2] });
        texto(s, etapas[j][1], { x: x + 0.3 + j * 1.8, y: y + 1.85, w: 1.7, h: 0.35, fontSize: 12, color: C.text2 });
      }
    }
  }
  s.addNotes("La subcategoría de cada actividad sugiere su forma de evaluación. Si una tarea tiene instrumento y evidencia, se promedian.");

  // 7. Evidencia válida y excedente
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Cálculo" });
  s.addText("Evidencia válida, excedente y destacados", { placeholder: "title" });
  tarjeta(s, 0.6, 1.6, 5.95, 4.95, "Evidencia válida");
  await circuloIcono(s, fa.FaFolderOpen, 0.9, 1.9, 0.9, C.text1, "Evidencia");
  texto(s, "Sólo cuenta la carpeta individual (Drive)", { x: 2.0, y: 1.9, w: 4.3, h: 0.9, fontSize: 19, bold: true, valign: "middle" });
  texto(s, "La información que la Oficina recoge de la carga académica es un trabajo adicional y no acredita cumplimiento.", { x: 0.9, y: 3.0, w: 5.4, h: 1.0, fontSize: 15, color: C.text2 });
  texto(s, "0%", { x: 0.9, y: 4.2, w: 1.9, h: 1.0, fontSize: 54, bold: true, color: C.accent5 });
  texto(s, "para la actividad sin evidencia en la carpeta. Quien no provee evidencias obtiene la calificación mínima.", { x: 2.9, y: 4.3, w: 3.4, h: 1.9, fontSize: 14, color: C.text2 });
  tarjeta(s, 6.75, 1.6, 5.95, 4.95, "Excedente");
  await circuloIcono(s, fa.FaAward, 7.05, 1.9, 0.9, C.accent2, "Excedente");
  texto(s, "Excedente validado: hasta 120%", { x: 8.15, y: 1.9, w: 4.3, h: 0.9, fontSize: 19, bold: true, valign: "middle" });
  formula(s, "excedente", 7.05, 3.0, 0.8, 5.4);
  texto(s, "Lo que supera el tope no sube la calificación, pero queda registrado como destacado (tarea, subcategoría y cumplimiento real) para el reconocimiento institucional. Un excedente sin validar cuenta como 100%.", { x: 7.05, y: 4.1, w: 5.4, h: 2.2, fontSize: 14, color: C.text2 });
  s.addNotes("Dos reglas clave: la evidencia sólo se acepta desde la carpeta individual, y el excedente se reconoce pero con tope.");

  // 8. Ámbito y compromiso
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Cálculo" });
  s.addText("Del cumplimiento de las tareas al del compromiso", { placeholder: "title" });
  tarjeta(s, 0.6, 1.6, 5.6, 4.95, "Cumplimiento del ámbito");
  texto(s, "Cumplimiento de cada ámbito", { x: 0.9, y: 1.85, w: 5.0, h: 0.45, fontSize: 18, bold: true });
  formula(s, "ambito", 0.9, 2.45, 1.75);
  texto(s, "Promedio de las tareas del ámbito. πₜ es un peso opcional (por defecto 1). Cada ámbito recibe también su letra.", { x: 0.9, y: 4.5, w: 5.0, h: 1.6, fontSize: 14, color: C.text2 });
  s.addShape(pres.shapes.CHEVRON, { x: 6.35, y: 3.75, w: 0.45, h: 0.7, fill: { color: C.accent4 }, line: { color: C.accent4, width: 0 }, objectName: "Flecha ámbito-compromiso" });
  tarjeta(s, 6.95, 1.6, 5.75, 4.95, "Cumplimiento del compromiso");
  texto(s, "Cumplimiento del compromiso", { x: 7.25, y: 1.85, w: 5.2, h: 0.45, fontSize: 18, bold: true });
  formula(s, "compromiso", 7.25, 2.75, 1.0);
  texto(s, "Promedio de los ámbitos ponderado por las horas. Es el 80% de la calificación final.", { x: 7.25, y: 4.5, w: 5.2, h: 1.6, fontSize: 14, color: C.text2 });
  s.addNotes("S de cada ámbito y C del compromiso. La letra no exige mínimos por ámbito ni combinaciones entre ámbitos.");

  // 9. Calificación final
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Cálculo" });
  s.addText("La calificación final", { placeholder: "title" });
  tarjeta(s, 0.6, 1.55, 12.1, 1.3, "Fórmula final");
  formula(s, "final", 1.0, 1.85, 0.7, 11.3);
  s.addChart(pres.charts.DOUGHNUT, [{ name: "Composición", labels: ["Ámbitos del compromiso", "Autoevaluación", "Evaluación de estudiantes"], values: [80, 10, 10] }], {
    x: 0.6, y: 3.05, w: 5.4, h: 3.6, holeSize: 55, chartColors: [HEX.dk1, HEX.accent2, HEX.accent3], showPercent: true, showValue: false,
    dataLabelColor: HEX.lt1, dataLabelFontSize: 13, dataLabelFontFace: "+mn-lt", showLegend: true, legendPos: "r", legendFontSize: 12,
    legendColor: HEX.dk2, legendFontFace: "+mn-lt", showTitle: false,
  });
  const comp = [
    ["C · cumplimiento del compromiso", "80%: ámbitos ponderados por horas."],
    ["AE · autoevaluación", "10%: pauta Cumple / No cumple / No aplica."],
    ["EE · evaluación de estudiantes", "10%: promedio de sus secciones."],
    ["Eximido/a de docencia", "Sin EE: los ámbitos pesan 90% y AE 10%."],
  ];
  for (let i = 0; i < comp.length; i++) {
    texto(s, comp[i][0], { x: 6.4, y: 3.1 + i * 0.88, w: 6.3, h: 0.4, fontSize: 16, bold: true });
    texto(s, comp[i][1], { x: 6.4, y: 3.48 + i * 0.88, w: 6.3, h: 0.4, fontSize: 14, color: C.text2 });
  }
  s.addNotes("Fórmula final: 80% compromiso, 10% autoevaluación y 10% estudiantes. Si está eximido de docencia, 90% y 10%.");

  // 10. Clasificación
  pres.addSection({ title: "Resultados" });
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Resultados" });
  s.addText("Clasificación del resultado", { placeholder: "title" });
  const letras = [
    ["A+", "101% o más", "Sobresaliente: supera lo comprometido", C.accent3],
    ["A", "90% a 100%", "Cumplimiento pleno", C.accent6],
    ["B", "75% a 89%", "Cumplimiento bueno", C.accent4],
    ["C", "55% a 74%", "Cumplimiento parcial, requiere mejora", C.accent2],
    ["D", "menos de 55%", "Insuficiente", C.accent5],
  ];
  for (let i = 0; i < letras.length; i++) {
    const x = 0.6 + i * 2.44;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.6, w: 2.3, h: 1.5, rectRadius: 0.12, fill: { color: letras[i][3] }, line: { color: letras[i][3], width: 0 }, objectName: "Letra " + letras[i][0] });
    texto(s, letras[i][0], { x, y: 1.65, w: 2.3, h: 0.9, fontFace: "Cambria", fontSize: 40, bold: true, color: C.background1, align: "center", valign: "middle" });
    texto(s, letras[i][1], { x, y: 2.55, w: 2.3, h: 0.45, fontSize: 15, bold: true, color: C.background1, align: "center" });
    texto(s, letras[i][2], { x: x + 0.05, y: 3.25, w: 2.2, h: 0.9, fontSize: 14, color: C.text2, align: "center" });
  }
  texto(s, "Equivalencia con la escala de 1 a 7", { x: 0.6, y: 4.45, w: 6, h: 0.45, fontSize: 17, bold: true });
  const escala = [["90–100%", "7"], ["80–89%", "6"], ["70–79%", "5"], ["60–69%", "4"], ["50–59%", "3"], ["40–49%", "2"], ["< 40%", "1"]];
  s.addTable([
    escala.map((e) => ({ text: e[0], options: { bold: true, color: C.background1, fill: { color: C.text1 }, align: "center" } })),
    escala.map((e) => ({ text: e[1], options: { align: "center", fontSize: 18, bold: true, color: C.text1, fill: { color: C.background2 } } })),
  ], { x: 0.6, y: 5.0, w: 12.1, colW: Array(7).fill(12.1 / 7), fontSize: 14, border: { type: "solid", pt: 1, color: HEX.lt1 }, rowH: [0.45, 0.6], objectName: "Escala numérica" });
  texto(s, "La letra depende sólo del cumplimiento final F.", { x: 0.6, y: 6.2, w: 12.1, h: 0.4, fontSize: 14, italic: true, color: C.text2 });
  s.addNotes("Umbrales definitivos: A+ desde 101%, A 90 a 100, B 75 a 89, C 55 a 74, D bajo 55.");

  // 11. Ejemplo
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Resultados" });
  s.addText("Ejemplo de cálculo", { placeholder: "title" });
  const cab = ["Ámbito", "Horas", "wₐ", "Sₐ", "wₐ · Sₐ"].map((t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text1 } } }));
  const filas = [
    ["Docencia", "22", "50,0%", "95,0", "47,5"],
    ["Investigación, Creación e Innovación", "12", "27,3%", "75,0", "20,5"],
    ["Vinculación con el Medio", "4", "9,1%", "120,0 ★", "10,9"],
    ["Gestión Académica", "6", "13,6%", "100,0", "13,6"],
  ].map((f) => f.map((t, j) => ({ text: t, options: { align: j === 0 ? "left" : "right", fill: { color: C.background2 } } })));
  filas.push(["Compromiso (C)", "44", "100%", "", "92,5"].map((t, j) => ({ text: t, options: { bold: true, align: j === 0 ? "left" : "right", fill: { color: C.background1 } } })));
  s.addTable([cab, ...filas], { x: 0.6, y: 1.6, w: 7.6, colW: [3.4, 0.9, 1.1, 1.1, 1.1], fontSize: 14, color: C.text1, border: { type: "solid", pt: 1, color: HEX.lt1 }, rowH: 0.55, objectName: "Tabla ejemplo" });
  texto(s, "Hipotético. ★ Dos talleres comprometidos, tres realizados y validados: 150%, cuenta 120% y queda como destacado.", { x: 0.6, y: 5.15, w: 7.6, h: 0.8, fontSize: 13, color: C.text2 });
  tarjeta(s, 8.6, 1.6, 4.1, 4.95, "Resultado ejemplo", C.text1);
  texto(s, "Con AE = 90% y EE = 88%", { x: 8.9, y: 1.85, w: 3.5, h: 0.4, fontSize: 14, color: C.background2 });
  texto(s, "F = 0,8 · 92,5 + 0,1 · 90 + 0,1 · 88", { x: 8.9, y: 2.3, w: 3.5, h: 0.8, fontSize: 16, color: C.background1 });
  texto(s, "91,8%", { x: 8.9, y: 3.15, w: 3.5, h: 1.1, fontSize: 54, bold: true, color: C.accent2 });
  texto(s, "Calificación A", { x: 8.9, y: 4.3, w: 3.5, h: 0.55, fontSize: 24, bold: true, color: C.background1 });
  texto(s, "Cumplimiento pleno · escala 7", { x: 8.9, y: 4.85, w: 3.5, h: 0.45, fontSize: 15, color: C.background2 });
  s.addNotes("Ejemplo hipotético con 44 horas. El taller excedente cuenta con tope y queda registrado para reconocimiento.");

  // 12. Situaciones especiales
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Resultados" });
  s.addText("Situaciones especiales (art. 37)", { placeholder: "title" });
  const sit = [
    [fa.FaHourglassHalf, "Ausencia justificada de más de 5 meses continuos", "Por cualquier motivo: la evaluación del período se suspende.", C.accent5],
    [fa.FaGraduationCap, "Comisión de estudios", "Depende del período y las condiciones con que se otorgó. Si tiene compromisos asociados, se evalúan en proporción a la jornada.", C.accent2],
    [fa.FaPercentage, "Otras situaciones", "Licencias más cortas, permisos, comisión de servicio, cargo directivo u horas de estudio: las metas se ajustan con el factor f.", C.accent3],
  ];
  for (let i = 0; i < sit.length; i++) {
    const y = 1.6 + i * 1.45;
    await circuloIcono(s, sit[i][0], 0.6, y + 0.1, 1.0, sit[i][3], "Situación " + i);
    texto(s, sit[i][1], { x: 1.85, y: y + 0.05, w: 6.6, h: 0.5, fontSize: 18, bold: true });
    texto(s, sit[i][2], { x: 1.85, y: y + 0.55, w: 6.6, h: 0.8, fontSize: 14, color: C.text2 });
  }
  tarjeta(s, 8.85, 1.6, 3.85, 4.2, "Factor de jornada");
  texto(s, "Factor de jornada", { x: 9.15, y: 1.85, w: 3.3, h: 0.45, fontSize: 17, bold: true });
  formula(s, "factor", 9.15, 2.5, 0.8, 3.3);
  texto(s, "Se aplica a las metas: 2 publicaciones con 50% de jornada pasan a ser 1. En todos los casos se informa a la Oficina y a las autoridades.", { x: 9.15, y: 3.6, w: 3.3, h: 2.0, fontSize: 13, color: C.text2 });
  s.addNotes("Regla de suspensión y evaluación proporcional. La comisión de estudios requiere definir sus compromisos asociados.");

  // 13. Consecuencias
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Resultados" });
  s.addText("Qué significa cada resultado", { placeholder: "title" });
  const cons = [
    [fa.FaAward, "A+", "Desempeño sobresaliente. Candidato/a a reconocimiento institucional, con el registro de lo que destaca.", C.accent3],
    [fa.FaArrowCircleUp, "A en dos procesos", "Requisito para ascender de jerarquía (art. 11). A o B en los dos últimos, para cambiar de perfil (art. 8).", C.accent6],
    [fa.FaHandsHelping, "D, o C dos veces seguidas", "Ingreso obligatorio al programa institucional de acompañamiento y fortalecimiento académico (art. 41).", C.accent5],
  ];
  for (let i = 0; i < 3; i++) {
    const x = 0.6 + i * 4.1;
    tarjeta(s, x, 1.6, 3.85, 3.6, "Consecuencia " + i);
    await circuloIcono(s, cons[i][0], x + 0.3, 1.9, 1.0, cons[i][3], "Consecuencia " + i);
    texto(s, cons[i][1], { x: x + 0.3, y: 3.05, w: 3.3, h: 0.5, fontSize: 20, bold: true });
    texto(s, cons[i][2], { x: x + 0.3, y: 3.6, w: 3.3, h: 1.5, fontSize: 14, color: C.text2 });
  }
  tarjeta(s, 0.6, 5.45, 12.1, 1.1, "Funciones de la jerarquía");
  texto(s, "El informe de cierre revisa también las funciones de la jerarquía y el perfil (cumplida, sin evidencia o no declarada). Orienta el desarrollo profesional; no cambia la calificación.", { x: 0.9, y: 5.55, w: 11.5, h: 0.9, fontSize: 14, valign: "middle" });
  s.addNotes("Consecuencias según el reglamento: reconocimiento, ascenso y acompañamiento.");

  // 14. Próximos pasos
  pres.addSection({ title: "Cierre" });
  s = pres.addSlide({ masterName: "CIERRE", sectionTitle: "Cierre" });
  s.addText("Próximos pasos: implementación en UCampus", { placeholder: "title" });
  const fases = [
    ["Compromiso", "Formulario con horas, subcategorías, metas y etapas; resumen y validaciones automáticas"],
    ["Evidencias", "Carpeta individual por actividad, validación y situaciones especiales"],
    ["Instrumentos", "Pautas Cumple / No cumple / No aplica enlazadas a actividades y secciones"],
    ["Cálculo e informes", "Calificación automática, informe de cierre, expediente y notificación"],
    ["Análisis", "Tablero institucional, exportaciones y comparación entre períodos"],
  ];
  for (let i = 0; i < fases.length; i++) {
    const y = 1.65 + i * 1.0;
    s.addShape(pres.shapes.OVAL, { x: 0.8, y, w: 0.7, h: 0.7, fill: { color: C.accent2 }, line: { color: C.accent2, width: 0 }, objectName: "Fase " + (i + 1) });
    texto(s, String(i + 1), { x: 0.8, y, w: 0.7, h: 0.7, fontSize: 20, bold: true, color: C.text1, align: "center", valign: "middle" });
    texto(s, fases[i][0], { x: 1.8, y: y + 0.02, w: 3.2, h: 0.66, fontSize: 19, bold: true, color: C.background1, valign: "middle" });
    texto(s, fases[i][1], { x: 5.0, y: y + 0.02, w: 7.6, h: 0.66, fontSize: 15, color: C.background2, valign: "middle" });
  }
  s.addNotes("Las cinco fases del documento de requerimientos para UCampus.");

  await pres.writeFile({ fileName: salida });
  if (applyTheme) await applyTheme(salida, THEME);
  else console.warn("PPTX_SKILL_DIR no definido: la paleta SEJA no se aplicó al tema.");
  console.log("Guardado en " + salida);
}

main().catch((e) => { console.error(e); process.exit(1); });
