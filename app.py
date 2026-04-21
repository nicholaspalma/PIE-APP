import streamlit as st
import docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import google.generativeai as genai
from io import BytesIO
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="PACI Experto Pro", page_icon="👩‍🏫", layout="centered")

api_key_configurada = st.secrets.get("GEMINI_API_KEY", None)

def leer_docx(archivo):
    doc = docx.Document(archivo)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def crear_docx_adaptado(texto_adaptado):
    # Abrimos la plantilla (con tus logos)
    if os.path.exists("plantilla.docx"):
        doc = docx.Document("plantilla.docx")
    else:
        doc = docx.Document()

    # Añadimos un poco de espacio después del encabezado de la plantilla
    doc.add_paragraph("\n")

    # Procesamos el texto para limpiar símbolos extraños de la IA
    for linea in texto_adaptado.split('\n'):
        # Saltamos líneas que son solo guiones o decoraciones de la IA
        linea_limpia = linea.replace('---', '').replace('***', '').replace('**', '').strip()
        
        if linea_limpia:
            p = doc.add_paragraph()
            # Si es un título de sección (ej: PARTE I) lo ponemos destacado
            if "PARTE" in linea_limpia.upper() or "INSTRUCCIONES" in linea_limpia.upper():
                run = p.add_run(linea_limpia)
                run.bold = True
                run.font.size = Pt(12)
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.add_run(linea_limpia)
    
    archivo_memoria = BytesIO()
    doc.save(archivo_memoria)
    archivo_memoria.seek(0)
    return archivo_memoria

def adaptar_prueba_con_ia(texto_original, curso, asignatura, necesidad, api_key, nombre_modelo):
    genai.configure(api_key=api_key)
    modelo = genai.GenerativeModel(nombre_modelo)
    
    # PROMPT ULTRA-ESTRICTO: Eliminamos la "conversación" de la IA
    prompt = f"""
    Eres una Educadora Diferencial con 20 años de experiencia. 
    ADAPTA esta prueba de {asignatura} para {curso} (Necesidad: {necesidad}).

    REGLAS CRÍTICAS DE SALIDA:
    1. PROHIBIDO saludar, presentarte o dar explicaciones. 
    2. Comienza DIRECTAMENTE con el nombre de la prueba.
    3. NO incluyas campos de "Nombre", "Fecha" o "Curso" (ya están en la plantilla).
    4. NO uses tablas de texto (símbolos |). Usa listas simples.
    5. NO uses líneas de guiones (---).
    6. Usa instrucciones claras y segmentadas para el estudiante.

    TEXTO ORIGINAL A ADAPTAR:
    {texto_original}
    """
    
    response = modelo.generate_content(prompt)
    return response.text

# --- INTERFAZ ---
st.title("👩‍🏫 Generador PACI Profesional")

with st.sidebar:
    st.header("⚙️ Configuración")
    final_api_key = api_key_configurada if api_key_configurada else st.text_input("API Key:", type="password")
    modelo_seleccionado = None
    
    if final_api_key:
        try:
            genai.configure(api_key=final_api_key)
            modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            modelos_limpios = [m for m in modelos if "vision" not in m]
            if modelos_limpios:
                modelo_seleccionado = st.selectbox("🧠 Cerebro IA:", modelos_limpios)
        except:
            st.error("Error de conexión.")
    
    st.divider()
    curso_sel = st.selectbox("Curso:", ["1ro Básico", "2do Básico", "3ro Básico", "4to Básico", "5to Básico", "6to Básico", "7mo Básico", "8vo Básico"])
    necesidad_sel = st.selectbox("Necesidad:", ["TEA", "TDAH", "Trastorno del Lenguaje"])

archivo = st.file_uploader("Sube la prueba original (.docx)", type=["docx"])

if archivo and st.button("🚀 Generar Word Profesional"):
    if final_api_key and modelo_seleccionado:
        with st.spinner("Generando adecuación limpia..."):
            try:
                texto_paci = adaptar_prueba_con_ia(leer_docx(archivo), curso_sel, "Asignatura", necesidad_sel, final_api_key, modelo_seleccionado)
                archivo_word = crear_docx_adaptado(texto_paci)
                st.success("✨ ¡Documento listo!")
                st.download_button("⬇️ Descargar Word", data=archivo_word, file_name=f"Prueba_Adaptada.docx")
            except Exception as e:
                st.error(f"Error: {e}")
