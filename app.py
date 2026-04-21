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
    # Intentamos abrir la plantilla con logos, si no existe, creamos uno blanco
    if os.path.exists("plantilla.docx"):
        doc = docx.Document("plantilla.docx")
        # Añadimos un salto de página después del encabezado de la plantilla
        doc.add_page_break()
    else:
        doc = docx.Document()

    # Estilo para el título de la prueba
    titulo = doc.add_paragraph("EVALUACIÓN ADECUADA (PACI)")
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = titulo.runs[0]
    run.bold = True
    run.font.size = Pt(14)

    # Procesamos el texto de la IA para aplicar formato básico
    for linea in texto_adaptado.split('\n'):
        if linea.strip():
            p = doc.add_paragraph()
            # Si la línea parece un título (ej: Parte I, Instrucciones), la ponemos en negrita
            if ":" in linea or linea.isupper() or "PARTE" in linea.upper():
                run = p.add_run(linea.replace('**', ''))
                run.bold = True
            else:
                p.add_run(linea.replace('**', ''))
    
    archivo_memoria = BytesIO()
    doc.save(archivo_memoria)
    archivo_memoria.seek(0)
    return archivo_memoria

def adaptar_prueba_con_ia(texto_original, curso, asignatura, necesidad, api_key, nombre_modelo):
    genai.configure(api_key=api_key)
    modelo = genai.GenerativeModel(nombre_modelo)
    
    # PROMPT MEJORADO: Le pedimos a la IA que use una estructura clara
    prompt = f"""
    Actúa como una Educadora Diferencial con 20 años de experiencia en Chile. 
    Tu misión es realizar la adecuación PACI de esta prueba de {asignatura} para {curso}.
    Condición del estudiante: {necesidad}.

    INSTRUCCIONES DE FORMATO PARA EL WORD:
    1. Organiza la prueba en secciones claras (Ej: PARTE I: SELECCIÓN MÚLTIPLE).
    2. Usa instrucciones cortas y numeradas.
    3. Asegúrate de que el contenido sea estéticamente ordenado.
    4. No incluyas comentarios personales, solo la prueba final.

    PRUEBA ORIGINAL:
    {texto_original}
    """
    
    response = modelo.generate_content(prompt)
    return response.text

# --- INTERFAZ ---
st.title("👩‍🏫 Generador PACI: Formato Profesional")
st.info("Nota: Para mantener los logos, asegúrate de haber subido 'plantilla.docx' a tu GitHub.")

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
        with st.spinner("La experta está redactando y formateando la prueba..."):
            try:
                texto_paci = adaptar_prueba_con_ia(leer_docx(archivo), curso_sel, "Asignatura", necesidad_sel, final_api_key, modelo_seleccionado)
                archivo_word = crear_docx_adaptado(texto_paci)
                st.success("✨ ¡Documento generado!")
                st.download_button("⬇️ Descargar Word con Formato", data=archivo_word, file_name=f"Prueba_PACI_{curso_sel}.docx")
            except Exception as e:
                st.error(f"Error: {e}")
