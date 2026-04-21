import streamlit as st
import docx
import google.generativeai as genai
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="PACI Experto", page_icon="👩‍🏫", layout="centered")

# Carga de API Key desde Secrets
api_key_configurada = st.secrets.get("GEMINI_API_KEY", None)

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
    # Modelo 1.5 Flash: El más rápido y capaz para textos educativos
    modelo = genai.GenerativeModel('gemini-1.5-flash')
    
    # --- TU PROMPT PERSONALIZADO ---
    prompt = f"""
    Actúa como una Educadora Diferencial altamente capacitada, con más de 20 años de experiencia trabajando en el Programa de Integración Escolar (PIE) en Chile y experta en el Decreto 83.
    
    Tu tarea es ejecutar una adecuación curricular profunda de la siguiente prueba de {asignatura} para un estudiante de {curso}. 
    El estudiante presenta la siguiente condición: {necesidad}.
    
    Basado en tu vasta trayectoria, aplica estos criterios:
    1. Graduación de la complejidad: Simplifica el vocabulario sin perder el objetivo pedagógico.
    2. Adaptación de acceso: Fragmenta instrucciones largas en pasos numerados simples.
    3. Formato: Prioriza preguntas directas, usa negritas para conceptos clave y elimina distractores.
    4. Si es TEA: Usa lenguaje literal y evita metáforas. Si es TDAH: Resalta los verbos de las instrucciones.
    
    Entrega la prueba completa y lista para copiar a Word. No saludes ni des explicaciones, solo el contenido adaptado.
    
    TEXTO ORIGINAL:
    {texto_original}
    """
    
    response = modelo.generate_content(prompt)
    return response.text

# --- INTERFAZ ---
st.title("👩‍🏫 Generador PACI: Nivel Experto")
st.markdown("Plataforma profesional para especialistas PIE.")

with st.sidebar:
    st.header("⚙️ Configuración")
    if api_key_configurada:
        st.success("✅ IA Conectada")
        final_api_key = api_key_configurada
    else:
        final_api_key = st.text_input("Ingresa API Key:", type="password")
    
    curso_sel = st.selectbox("Curso:", ["1ro Básico", "2do Básico", "3ro Básico", "4to Básico", "5to Básico", "6to Básico", "7mo Básico", "8vo Básico", "1ro Medio", "2do Medio", "3ro Medio", "4to Medio"])
    asignatura_sel = st.selectbox("Asignatura:", ["Lenguaje", "Matemáticas", "Historia", "Ciencias", "Inglés"])
    necesidad_sel = st.selectbox("Necesidad:", ["TEA", "TDAH", "Trastorno del Lenguaje"])

archivo = st.file_uploader("Sube la prueba (.docx)", type=["docx"])

if archivo and st.button("🚀 Ejecutar Adecuación Experta"):
    try:
        with st.spinner("La educadora virtual está adaptando el material..."):
            texto_paci = adaptar_prueba_con_ia(leer_docx(archivo), curso_sel, asignatura_sel, necesidad_sel, final_api_key)
            st.success("✨ ¡Adecuación lista!")
            st.download_button("⬇️ Descargar Word", data=crear_docx_adaptado(texto_paci), file_name=f"PACI_{asignatura_sel}.docx")
            with st.expander("Ver vista previa"): st.write(texto_paci)
    except Exception as e:
        st.error(f"Error técnico: {e}")
