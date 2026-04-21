import streamlit as st
import docx
from docx.shared import Pt
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
    if os.path.exists("plantilla.docx"):
        doc = docx.Document("plantilla.docx")
    else:
        doc = docx.Document()

    lineas = texto_adaptado.split('\n')
    titulo_ia = lineas[0].replace('#', '').strip() # La primera línea será el título
    cuerpo_prueba = lineas[1:]

    # REEMPLAZO DE TÍTULO EN LA PLANTILLA
    for p in doc.paragraphs:
        if "{titulo}" in p.text:
            p.text = p.text.replace("{titulo}", titulo_ia)
            for run in p.runs:
                run.bold = True

    # PROCESAMIENTO DEL CUERPO
    letra_opcion = 0
    abc = ["a)", "b)", "c)", "d)", "e)"]

    for linea in cuerpo_prueba:
        linea_limpia = linea.replace('---', '').replace('**', '').replace('\\_', '_').strip()
        
        if linea_limpia:
            # Convertir puntos de IA en letras (a, b, c)
            if linea_limpia.startswith('*') or linea_limpia.startswith('-'):
                texto_final = f"{abc[letra_opcion % 5]} {linea_limpia[1:].strip()}"
                letra_opcion += 1
            else:
                texto_final = linea_limpia
                if not any(char in linea_limpia for char in "abcde)"): # Si no es opción, reinicia letras
                    letra_opcion = 0

            p = doc.add_paragraph(texto_final)
            
            # Formato de Títulos de Sección
            if "PARTE" in texto_final.upper() or "INSTRUCCIÓN" in texto_final.upper():
                p.runs[0].bold = True
                p.paragraph_format.space_before = Pt(12)
            
            # ESPACIO PARA DIBUJAR: Si la línea menciona dibujar, añade espacio
            if "DIBUJA" in texto_final.upper() or "DIBUJO" in texto_final.upper():
                for _ in range(8): # Añade 8 líneas en blanco
                    doc.add_paragraph("")
    
    archivo_memoria = BytesIO()
    doc.save(archivo_memoria)
    archivo_memoria.seek(0)
    return archivo_memoria

def adaptar_prueba_con_ia(texto_original, curso, asignatura, necesidad, api_key, nombre_modelo):
    genai.configure(api_key=api_key)
    modelo = genai.GenerativeModel(nombre_modelo)
    
    prompt = f"""
    Eres una Educadora Diferencial con 20 años de experiencia. 
    ADAPTA esta prueba de {asignatura} para {curso} (Necesidad: {necesidad}).

    REGLAS DE FORMATO OBLIGATORIAS:
    1. La primera línea DEBE ser el título de la prueba.
    2. Usa una lista con viñetas (*) para las alternativas de selección múltiple.
    3. Para Verdadero o Falso usa exactamente este formato: ______ (6 guiones bajos).
    4. Indica claramente las secciones como PARTE I, PARTE II, etc.
    5. Prohibido saludar o dar explicaciones, entrega solo la prueba.
    6. No incluyas encabezados de nombre o fecha.

    TEXTO ORIGINAL:
    {texto_original}
    """
    
    response = modelo.generate_content(prompt)
    return response.text

# --- INTERFAZ STREAMLIT ---
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
        with st.spinner("Aplicando formato profesional..."):
            try:
                texto_paci = adaptar_prueba_con_ia(leer_docx(archivo), curso_sel, "Prueba", necesidad_sel, final_api_key, modelo_seleccionado)
                archivo_word = crear_docx_adaptado(texto_paci)
                st.success("✨ ¡Documento generado correctamente!")
                st.download_button("⬇️ Descargar Word", data=archivo_word, file_name=f"Prueba_Adaptada.docx")
            except Exception as e:
                st.error(f"Error: {e}")
