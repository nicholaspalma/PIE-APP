import streamlit as st
import docx
from docx.shared import Pt
import google.generativeai as genai
from io import BytesIO
import os
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="PACI Pro: Nivel Gemini 3", 
    page_icon="👩‍🏫", 
    layout="wide"
)

# --- DISEÑO CSS AVANZADO ---
def apply_pro_design(image_file):
    with open(image_file, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode()
    
    st.markdown(
        f"""
        <style>
        /* Fondo de pantalla completo */
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_string}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        /* Renglón Blanco Superior para el Título */
        .top-header {{
            background-color: white;
            border-radius: 50px;
            padding: 10px 40px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }}
        .top-header h1 {{
            color: #1E3A8A !important;
            margin: 0;
            font-size: 2.2rem;
            font-weight: 800;
        }}

        /* Renglones/Tarjetas Blancas para cada sección */
        .item-card {{
            background-color: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            border: 1px solid #E2E8F0;
            max-width: 1000px;
            margin-left: auto;
            margin-right: auto;
        }}

        /* Estilo de etiquetas y texto */
        .stMarkdown, .stSelectbox label, .stFileUploader label {{
            color: #1E293B !important;
            font-weight: 600 !important;
        }}
        
        h3 {{
            color: #2563EB !important;
            margin-top: 0;
            border-bottom: 2px solid #DBEAFE;
            padding-bottom: 10px;
        }}

        /* Ocultar elementos innecesarios */
        [data-testid="stSidebar"] {{ display: none; }}
        </style>
        """,
        unsafe_allow_html=True
    )

if os.path.exists("fondo.png"):
    apply_pro_design('fondo.png')

# --- LÓGICA DE PROCESAMIENTO ---
api_key_configurada = st.secrets.get("GEMINI_API_KEY", None)

def leer_docx(archivo):
    doc = docx.Document(archivo)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def crear_docx_adaptado(texto_adaptado):
    if os.path.exists("plantilla.docx"): doc = docx.Document("plantilla.docx")
    else: doc = docx.Document()
    lineas = [l.strip() for l in texto_adaptado.split('\n') if l.strip()]
    titulo_ia = lineas[0].replace('#', '').strip() if lineas else "Evaluación Adecuada"
    for p in doc.paragraphs:
        if "{titulo}" in p.text:
            p.text = p.text.replace("{titulo}", titulo_ia)
            for run in p.runs: run.bold = True
    letra_opcion, abc, dibujo_listo = 0, ["a)", "b)", "c)", "d)", "e)"], False
    prohibidas = ["NOMBRE", "CURSO", "FECHA", "APELLIDO", "RUT", "PUNTAJE"]
    for linea in lineas[1:]:
        if any(p in linea.upper() for p in prohibidas) and len(linea) < 50: continue
        linea_limpia = linea.replace('|', '').replace('---', '').replace('**', '').replace('\\_', '').strip()
        if linea_limpia:
            if linea_limpia.startswith(('*', '-', '•')):
                texto_final = f"{abc[letra_opcion % 5]} {linea_limpia[1:].strip()}"
                letra_opcion += 1
            else:
                texto_final = linea_limpia
                if not any(texto_final.startswith(x) for x in abc): letra_opcion = 0
            p = doc.add_paragraph(texto_final)
            p.paragraph_format.space_after = Pt(12)
            if any(x in texto_final.upper() for x in ["PARTE", "INSTRUCCIÓN"]):
                if p.runs: p.runs[0].bold = True
                p.paragraph_format.space_before = Pt(18)
            if ("DIBUJA" in texto_final.upper() or "DIBUJO" in texto_final.upper()) and not dibujo_listo:
                for _ in range(10): doc.add_paragraph("")
                dibujo_listo = True 
    buf = BytesIO(); doc.save(buf); buf.seek(0)
    return buf

def adaptar_prueba_con_ia(texto_original, curso, asignatura, necesidad, api_key):
    genai.configure(api_key=api_key)
    modelo = genai.GenerativeModel('gemini-3-flash-preview')
    prompt = f"Actúa como Educadora Diferencial experta. Adapta esta prueba de {asignatura} para {curso} con {necesidad}. Reglas: Primera línea título, viñetas * para alternativas, ______ para V/F, sin tablas, sin encabezados de datos personales. Texto: {texto_original}"
    return modelo.generate_content(prompt).text

# --- INTERFAZ ORGANIZADA ---

# 1. TÍTULO EN EL RENGLÓN SUPERIOR
st.markdown('<div class="top-header"><h1>👩‍🏫 PACI Pro: Nivel Gemini 3</h1></div>', unsafe_allow_html=True)

# 2. BLOQUE DE CONFIGURACIÓN (Renglón Blanco 1)
st.markdown('<div class="item-card">', unsafe_allow_html=True)
st.markdown("### 🛠️ 1. Configura la adecuación")
col1, col2, col3 = st.columns(3)
with col1:
    asignatura_sel = st.selectbox("Asignatura:", ["Lenguaje", "Matemáticas", "Historia", "Ciencias", "Inglés"])
with col2:
    curso_sel = st.selectbox("Curso:", ["1ro Básico", "2do Básico", "3ro Básico", "4to Básico", "5to Básico", "6to Básico", "7mo Básico", "8vo Básico"])
with col3:
    necesidad_sel = st.selectbox("Necesidad (PIE):", ["TEA", "TDAH", "Trastorno del Lenguaje"])
st.markdown('</div>', unsafe_allow_html=True)

# 3. BLOQUE DE CARGA (Renglón Blanco 2)
st.markdown('<div class="item-card">', unsafe_allow_html=True)
st.markdown("### 📂 2. Sube tu archivo")
archivo = st.file_uploader("Arrastra aquí tu prueba original en formato .docx", type=["docx"])

if not api_key_configurada:
    final_api_key = st.text_input("Ingresa tu API Key para activar la IA:", type="password")
else:
    final_api_key = api_key_configurada

if archivo and st.button("🚀 Generar Adecuación Profesional", use_container_width=True):
    if not final_api_key:
        st.error("Por favor ingresa la API Key.")
    else:
        with st.spinner("Gemini 3 está procesando tu archivo con cuidado..."):
            try:
                texto_paci = adaptar_prueba_con_ia(leer_docx(archivo), curso_sel, asignatura_sel, necesidad_sel, final_api_key)
                archivo_word = crear_docx_adaptado(texto_paci)
                st.balloons()
                st.success("✨ ¡Adecuación generada con éxito!")
                st.download_button("⬇️ Descargar Word Adaptado", data=archivo_word, file_name=f"PACI_{curso_sel}.docx", use_container_width=True)
            except Exception as e:
                st.error(f"Error técnico: {e}")
st.markdown('</div>', unsafe_allow_html=True)
