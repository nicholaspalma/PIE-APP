import streamlit as st
import docx
import google.generativeai as genai
from io import BytesIO

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Adecuaciones PACI", page_icon="📘", layout="centered")

# --- LÓGICA DE LA API KEY (SECRETS) ---
api_key_configurada = st.secrets.get("GEMINI_API_KEY", None)

# --- FUNCIONES ---
def leer_docx(archivo):
    doc = docx.Document(archivo)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def crear_docx_adaptado(texto_adaptado):
    doc = docx.Document()
    for linea in texto_adaptado.split('\n'):
        if linea.strip(): doc.add_paragraph(linea.replace('**', ''))
    archivo_memoria = BytesIO()
    doc.save(archivo_memoria)
    archivo_memoria.seek(0)
    return archivo_memoria

def adaptar_prueba_con_ia(texto_original, curso, asignatura, necesidad, api_key):
    genai.configure(api_key=api_key)
    modelo = genai.GenerativeModel('gemini-pro')
    instrucciones = {
        "TDAH": "Acorta oraciones, usa viñetas, resalta verbos.",
        "TEA": "Lenguaje literal, estructura predecible.",
        "Trastorno del Lenguaje": "Vocabulario simple, párrafos cortos."
    }
    prompt = f"Como experto PACI, adapta esta prueba de {asignatura} ({curso}) para {necesidad}: {instrucciones[necesidad]}\n\n{texto_original}"
    return modelo.generate_content(prompt).text

# --- INTERFAZ ---
st.title("📘 Generador PACI Profesional")

with st.sidebar:
    st.header("⚙️ Configuración")
    if api_key_configurada:
        st.success("✅ IA conectada vía Secrets")
        final_api_key = api_key_configurada
    else:
        final_api_key = st.text_input("Ingresa API Key manualmente:", type="password")
    
    curso_sel = st.selectbox("Curso:", ["1ro Básico", "2do Básico", "3ro Básico", "4to Básico", "5to Básico", "6to Básico", "7mo Básico", "8vo Básico", "1ro Medio", "2do Medio", "3ro Medio", "4to Medio"])
    asignatura_sel = st.selectbox("Asignatura:", ["Lenguaje", "Matemáticas", "Historia", "Ciencias", "Inglés"])
    necesidad_sel = st.selectbox("Necesidad:", ["TDAH", "TEA", "Trastorno del Lenguaje"])

archivo_subido = st.file_uploader("Sube la prueba (.docx)", type=["docx"])

if archivo_subido and st.button("🚀 Generar Adecuación"):
    if not final_api_key:
        st.error("Falta la API Key.")
    else:
        with st.spinner("La IA está trabajando..."):
            texto_paci = adaptar_prueba_con_ia(leer_docx(archivo_subido), curso_sel, asignatura_sel, necesidad_sel, final_api_key)
            st.download_button("⬇️ Descargar Word Adaptado", data=crear_docx_adaptado(texto_paci), file_name="PACI_Adaptado.docx")
