import streamlit as st
import docx
import google.generativeai as genai
from io import BytesIO

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Adecuaciones PACI", page_icon="📘", layout="centered")

# --- LÓGICA DE LA API KEY (SECRETS O MANUAL) ---
# Intentamos obtener la clave de los Secrets de Streamlit
# Si no existe (en local), permitimos entrada manual
api_key_configurada = st.secrets.get("GEMINI_API_KEY", None)

# --- FUNCIONES DE PROCESAMIENTO ---
def leer_docx(archivo):
    doc = docx.Document(archivo)
    texto_completo = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(texto_completo)

def crear_docx_adaptado(texto_adaptado):
    doc = docx.Document()
    for linea in texto_adaptado.split('\n'):
        if linea.strip():
            doc.add_paragraph(linea.replace('**', ''))
    archivo_memoria = BytesIO()
    doc.save(archivo_memoria)
    archivo_memoria.seek(0)
    return archivo_memoria

def adaptar_prueba_con_ia(texto_original, curso, asignatura, necesidad, api_key):
    genai.configure(api_key=api_key)
    modelo = genai.GenerativeModel('gemini-pro')
    
    instrucciones_paci = {
        "TDAH": "Acorta las oraciones, usa viñetas, RESALTA VERBOS DE ACCIÓN y divide preguntas en pasos.",
        "TEA": "Lenguaje literal y directo. Sin metáforas ni ambigüedades. Estructura predecible.",
        "Trastorno del Lenguaje": "Vocabulario simple, párrafos cortos, manteniendo el objetivo de aprendizaje."
    }
    
    prompt = f"Como experto en PACI, adapta esta prueba de {asignatura} ({curso}) para {necesidad}: {instrucciones_paci[necesidad]}\n\nPrueba:\n{texto_original}"
    
    respuesta = modelo.generate_content(prompt)
    return respuesta.text

# --- INTERFAZ ---
st.title("📘 Generador de Pruebas Adaptadas (PACI)")

with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Si la clave ya está en Secrets, avisamos al usuario
    if api_key_configurada:
        st.success("✅ IA conectada automáticamente via Secrets")
        final_api_key = api_key_configurada
    else:
        st.warning("⚠️ Clave no encontrada en Secrets.")
        final_api_key = st.text_input("Ingresa tu API Key manualmente:", type="password")
    
    st.divider()
    curso_sel = st.selectbox("Curso:", ["1ro Básico", "2do Básico", "3ro Básico", "4to Básico", "5to Básico", "6to Básico", "7mo Básico", "8vo Básico", "1ro Medio", "2do Medio", "3ro Medio", "4to Medio"])
    asignatura_sel = st.selectbox("Asignatura:", ["Lenguaje", "Matemáticas", "Historia", "Ciencias", "Inglés", "Otra"])
    necesidad_sel = st.selectbox("Necesidad Educativa:", ["TDAH", "TEA", "Trastorno del Lenguaje"])

archivo_subido = st.file_uploader("Sube la prueba original (.docx)", type=["docx"])

if archivo_subido and st.button("🚀 Generar Adecuación PACI"):
    if not final_api_key:
        st.error("Falta la API Key.")
    else:
        with st.spinner("Procesando..."):
            try:
                texto_prueba = leer_docx(archivo_subido)
                texto_adecuado = adaptar_prueba_con_ia(texto_prueba, curso_sel, asignatura_sel, necesidad_sel, final_api_key)
                nuevo_word = crear_docx_adaptado(texto_adecuado)
                
                st.success("¡Prueba adaptada!")
                st.download_button("⬇️ Descargar", data=nuevo_word, file_name=f"PACI_{necesidad_sel}.docx")
            except Exception as e:
                st.error(f"Error: {e}")
