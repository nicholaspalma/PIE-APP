import streamlit as st
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import google.generativeai as genai
from io import BytesIO
import os
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="PACI Pro: Edición Infantil", page_icon="🎨", layout="wide")

# --- FUNCIONES DE FORMATO VISUAL ---

def set_cell_border(cell, **kwargs):
    """ Función técnica para poner bordes a las celdas de las grillas """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for edge in ('top', 'start', 'bottom', 'end'):
        if edge in kwargs:
            tag = 'w:{}'.format(edge)
            element = tcPr.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcPr.append(element)
            for key, val in kwargs[edge].items():
                element.set(qn('w:{}'.format(key)), str(val))

def crear_grilla_escritura(doc):
    """ Crea una fila de cuadritos estilo caligrafía """
    table = doc.add_table(rows=1, cols=15)
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for cell in table.rows[0].cells:
        cell.width = Inches(0.3)
        set_cell_border(cell, top={"sz": 4, "val": "single", "color": "D1D5DB"},
                              bottom={"sz": 4, "val": "single", "color": "D1D5DB"},
                              start={"sz": 4, "val": "single", "color": "D1D5DB"},
                              end={"sz": 4, "val": "single", "color": "D1D5DB"})
    doc.add_paragraph("") # Espacio después de la grilla

def crear_marco_dibujo(doc, titulo="Dibuja aquí"):
    """ Crea un recuadro grande para dibujos """
    p = doc.add_paragraph(f"🎨 {titulo}:")
    p.runs[0].bold = True
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cell = table.rows[0].cells[0]
    cell.width = Inches(5)
    # Hacer la celda alta para el dibujo
    p_interno = cell.paragraphs[0]
    for _ in range(8): p_interno.add_run("\n")
    set_cell_border(cell, top={"sz": 12, "val": "single", "color": "3B82F6"},
                          bottom={"sz": 12, "val": "single", "color": "3B82F6"},
                          start={"sz": 12, "val": "single", "color": "3B82F6"},
                          end={"sz": 12, "val": "single", "color": "3B82F6"})

# --- LÓGICA PRINCIPAL ---

def crear_docx_adaptado(texto_adaptado):
    if os.path.exists("plantilla.docx"): doc = docx.Document("plantilla.docx")
    else: doc = docx.Document()

    lineas = [l.strip() for l in texto_adaptado.split('\n') if l.strip()]
    titulo_ia = lineas[0].replace('#', '').strip() if lineas else "Evaluación"
    
    # Reemplazo de título
    for p in doc.paragraphs:
        if "{titulo}" in p.text:
            p.text = p.text.replace("{titulo}", titulo_ia)
            for run in p.runs: run.bold = True; run.font.size = Pt(16)

    abc = ["a)", "b)", "c)", "d)"]
    letra_idx = 0

    for linea in lineas[1:]:
        # Filtro de redundancia
        if any(x in linea.upper() for x in ["NOMBRE:", "CURSO:", "FECHA:"]): continue
        
        linea_limpia = linea.replace('|', '').replace('**', '').strip()
        
        # DETECTAR SI ES DIBUJO
        if "DIBUJA" in linea_limpia.upper() or "[IMAGEN" in linea_limpia.upper():
            crear_marco_dibujo(doc, linea_limpia)
            continue

        # DETECTAR SI REQUIERE ESCRIBIR (Para poner la grilla)
        if "ESCRIBE" in linea_limpia.upper() or "COMPLETA" in linea_limpia.upper():
            p = doc.add_paragraph(f"✏️ {linea_limpia}")
            p.runs[0].bold = True
            crear_grilla_escritura(doc)
            continue

        # FORMATO DE ALTERNATIVAS
        if linea_limpia.startswith(('*', '-')):
            p = doc.add_paragraph(f"      {abc[letra_idx % 4]} {linea_limpia[1:].strip()}")
            letra_idx += 1
            continue
        
        # TEXTO NORMAL
        letra_idx = 0
        p = doc.add_paragraph(linea_limpia)
        p.paragraph_format.space_after = Pt(10)
        
        if "PARTE" in linea_limpia.upper():
            p.runs[0].bold = True; p.runs[0].font.size = Pt(13)
            p.paragraph_format.space_before = Pt(15)

    buf = BytesIO(); doc.save(buf); buf.seek(0)
    return buf

def adaptar_prueba_con_ia(texto_original, curso, asignatura, necesidad, api_key):
    genai.configure(api_key=api_key)
    modelo = genai.GenerativeModel('gemini-3-flash-preview')
    prompt = f"""
    Eres una Educadora Diferencial experta en Chile. Adapta esta prueba de {asignatura} para {curso} ({necesidad}).
    USA UN LENGUAJE INFANTIL Y CLARO.
    
    INSTRUCCIONES DE CONTENIDO:
    1. Usa la palabra 'Dibuja' cuando quieras que el niño realice un dibujo.
    2. Usa la palabra 'Escribe' cuando deba completar una palabra.
    3. Organiza todo en PARTE I, PARTE II.
    4. Usa alternativas con viñetas *.
    5. Prohibido saludos y datos personales. Solo la prueba.
    
    TEXTO: {texto_original}
    """
    return modelo.generate_content(prompt).text

# --- INTERFAZ UI (CENTRALIZADA) ---

# [Aquí va el código CSS de fondo que ya teníamos...]
# [Para ahorrar espacio, asumimos que mantienes el diseño de 'item-card' y 'top-header']

st.markdown('<div class="top-header"><h1>🎨 PACI Pro: Edición Infantil</h1></div>', unsafe_allow_html=True)

st.markdown('<div class="item-card">', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1: asignatura = st.selectbox("Asignatura:", ["Lenguaje", "Matemáticas", "Ciencias"])
with c2: curso = st.selectbox("Curso:", ["1ro Básico", "2do Básico"])
with c3: necesidad = st.selectbox("Necesidad:", ["TEA", "TDAH", "Dificultad de Aprendizaje"])
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="item-card">', unsafe_allow_html=True)
archivo = st.file_uploader("Sube el archivo .docx", type=["docx"])
if archivo and st.button("🚀 Crear Prueba Bonita"):
    with st.spinner("Diseñando material educativo..."):
        try:
            res_ia = adaptar_prueba_con_ia(leer_docx(archivo), curso, asignatura, necesidad, api_key_configurada)
            word = crear_docx_adaptado(res_ia)
            st.success("¡Prueba terminada con formato profesional!")
            st.download_button("⬇️ Descargar Material", data=word, file_name=f"Prueba_Infantil_{curso}.docx", use_container_width=True)
        except Exception as e: st.error(f"Error: {e}")
st.markdown('</div>', unsafe_allow_html=True)
