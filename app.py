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

# --- ESTILOS CSS PARA FONDO Y TARJETA CENTRAL ---
def apply_custom_design(image_file):
    with open(image_file, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode()
    
    st.markdown(
        f"""
        <style>
        /* Fondo de pantalla */
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_string}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        /* Tarjeta central (Glassmorphism) */
        .main-container {{
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.18);
            max-width: 900px;
            margin: auto;
            text-align: center;
        }}

        /* Ajustes de títulos */
        h1 {{
            color: #1E3A8A !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: 700;
        }}
        
        .stMarkdown {{
            color: #334155;
        }}

        /* Ocultar barra lateral si está vacía */
        [data-testid="stSidebar"] {{
            display: none;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Aplicar diseño si existe la imagen
if os.path.exists("fondo.png"):
    apply_custom_design('fondo.png')

# --- LÓGICA DE IA ---
api_key_configurada = st.secrets.get("GEMINI_API_KEY", None)

def leer_docx(archivo):
    doc = docx.Document(archivo)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def crear_docx_adaptado(texto_adaptado):
    if os.path.exists("plantilla.docx"):
        doc = docx.Document("plantilla.docx")
    else:
        doc = docx.Document()

    lineas = [l.strip() for l in texto_adaptado.split('\n') if l.strip()]
    titulo_ia = lineas[0].replace('#', '').strip() if lineas else "Evaluación Adecuada"
    cuerpo_crudo = lineas[1:] 

    for p in doc.paragraphs:
        if "{titulo}" in p.text:
            p.text = p.text.replace("{titulo}", titulo_ia)
            for run in p.runs: run.bold = True

    letra_opcion, abc, dibujo_listo = 0, ["a)", "b)", "c)", "d)", "e)"], False
    prohibidas = ["NOMBRE", "CURSO", "FECHA", "APELLIDO", "RUT", "PUNTAJE"]

    for linea in cuerpo_crudo:
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
    
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def adaptar_prueba_con_ia(texto_original, curso, asignatura, necesidad, api_key):
    genai.configure(api_key=api_key)
    modelo = genai.GenerativeModel('gemini-3-flash-preview')
    prompt = f"Actúa como Educadora Diferencial experta. Adapta esta prueba de {asignatura} para {curso} con {necesidad}. Reglas: Primera línea título, viñetas * para alternativas, ______ para V/F, sin tablas, sin encabezados de datos personales. Texto: {texto_original}"
    return modelo.generate_content(prompt).text

# --- INTERFAZ CENTRALIZADA ---
# Usamos un contenedor "div" de HTML para aplicar la tarjeta central
st.markdown('<div class="main-container">', unsafe_allow_html=True)

st.title("👩‍🏫 PACI Pro: Nivel Gemini 3")
st.write("Generador de adecuaciones curriculares con inteligencia artificial.")

# SELECTORES EN COLUMNAS (Estilo buscador central)
st.markdown("### 1. Configura la adecuación")
c1, c2, c3 = st.columns(3)
with c1:
    asignatura_sel = st.selectbox("Asignatura:", ["Lenguaje", "Matemáticas", "Historia", "Ciencias", "Inglés"])
with c2:
    curso_sel = st.selectbox("Curso:", ["1ro Básico", "2do Básico", "3ro Básico", "4to Básico", "5to Básico", "6to Básico", "7mo Básico", "8vo Básico"])
with c3:
    necesidad_sel = st.selectbox("Necesidad (PIE):", ["TEA", "TDAH", "Trastorno del Lenguaje"])

st.markdown("---")

# ÁREA DE CARGA (Grande y central)
st.markdown("### 2. Sube tu archivo")
archivo = st.file_uploader("Arrastra aquí tu prueba original (.docx)", type=["docx"])

if not api_key_configurada:
    final_api_key = st.text_input("Ingresa tu API Key para comenzar:", type="password")
else:
    final_api_key = api_key_configurada

if archivo and st.button("🚀 Generar Adecuación Profesional", use_container_width=True):
    if not final_api_key:
        st.error("Por favor ingresa la API Key.")
    else:
        with st.spinner("Gemini 3 está procesando tu archivo..."):
            try:
                texto_paci = adaptar_prueba_con_ia(leer_docx(archivo), curso_sel, asignatura_sel, necesidad_sel, final_api_key)
                archivo_word = crear_docx_adaptado(texto_paci)
                st.balloons()
                st.success("✨ ¡Adecuación generada con éxito!")
                st.download_button("⬇️ Descargar Documento Adaptado", data=archivo_word, file_name=f"PACI_{asignatura_sel}_{curso_sel}.docx", use_container_width=True)
            except Exception as e:
                st.error(f"Error técnico: {e}")

st.markdown('</div>', unsafe_allow_html=True)
