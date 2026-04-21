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
    titulo_ia = lineas[0].replace('#', '').strip()
    cuerpo_prueba = lineas[1:]

    # 1. REEMPLAZO DE {titulo} EN LA PLANTILLA
    for p in doc.paragraphs:
        if "{titulo}" in p.text:
            p.text = p.text.replace("{titulo}", titulo_ia)
            for run in p.runs:
                run.bold = True

    # 2. PROCESAMIENTO DEL CUERPO
    letra_opcion = 0
    abc = ["a)", "b)", "c)", "d)", "e)"]
    dibujo_añadido = False # Para evitar repetir el espacio de dibujo

    for linea in cuerpo_prueba:
        # Limpieza de símbolos extraños
        linea_limpia = linea.replace('---', '').replace('**', '').replace('\\_', '').replace('____', '______').strip()
        
        if linea_limpia:
            # Lógica para alternativas (convertir * en letras a, b, c)
            if linea_limpia.startswith('*') or linea_limpia.startswith('-'):
                texto_final = f"{abc[letra_opcion % 5]} {linea_limpia[1:].strip()}"
                letra_opcion += 1
            else:
                texto_final = linea_limpia
                if not any(char in linea_limpia for char in "abcde)"):
                    letra_opcion = 0 # Reinicia si es una pregunta nueva

            p = doc.add_paragraph(texto_final)
            
            # Espaciado después de cada pregunta (para que no queden pegadas)
            p.paragraph_format.space_after = Pt(6)

            # Formato de Títulos de Sección
            if "PARTE" in texto_final.upper() or "INSTRUCCIÓN" in texto_final.upper():
                p.runs[0].bold = True
                p.paragraph_format.space_before = Pt(12)
            
            # ESPACIO PARA DIBUJAR (Controlado)
            if ("DIBUJA" in texto_final.upper() or "DIBUJO" in texto_final.upper()) and not dibujo_añadido:
                for _ in range(6): 
                    doc.add_paragraph("")
                dibujo_añadido = True 
    
    archivo_memoria = BytesIO()
    doc.save(archivo_memoria)
    archivo_memoria.seek(0)
    return archivo_memoria

def adaptar_prueba_con_ia(texto_original, curso, asignatura, necesidad, api_key):
    genai.configure(api_key=api_key)
    # HARDCODED: Usamos siempre 1.5 Flash por velocidad y compatibilidad
    modelo = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Eres una Educadora Diferencial con 20 años de experiencia. 
    ADAPTA esta prueba de {asignatura} para {curso} (Necesidad: {necesidad}).

    REGLAS DE FORMATO INVIOLABLES:
    1. La primera línea DEBE ser el título de la prueba.
    2. Usa viñetas (*) para las alternativas.
    3. Para Verdadero o Falso usa exactamente este formato: ______ (guiones bajos).
    4. MANTÉN la sección de dibujo. No la cambies por preguntas de escritura larga.
    5. Prohibido saludar o dar introducciones.
    6. No incluyas nombres de alumnos o fechas.

    TEXTO ORIGINAL:
    {texto_original}
    """
    
    response = modelo.generate_content(prompt)
    return response.text

# --- INTERFAZ ---
st.title("👩‍🏫 PACI Pro: Formato Institucional")

with st.sidebar:
    st.header("⚙️ Configuración")
    final_api_key = api_key_configurada if api_key_configurada else st.text_input("API Key:", type="password")
    
    st.divider()
    curso_sel = st.selectbox("Curso:", ["1ro Básico", "2do Básico", "3ro Básico", "4to Básico", "5to Básico", "6to Básico", "7mo Básico", "8vo Básico"])
    asignatura_sel = st.selectbox("Asignatura:", ["Lenguaje", "Matemáticas", "Historia", "Ciencias", "Inglés"])
    necesidad_sel = st.selectbox("Necesidad (PIE):", ["TEA", "TDAH", "Trastorno del Lenguaje"])

archivo = st.file_uploader("Sube la prueba original (.docx)", type=["docx"])

if archivo and st.button("🚀 Generar Word"):
    if final_api_key:
        with st.spinner("La educadora virtual está trabajando..."):
            try:
                texto_paci = adaptar_prueba_con_ia(leer_docx(archivo), curso_sel, asignatura_sel, necesidad_sel, final_api_key)
                archivo_word = crear_docx_adaptado(texto_paci)
                st.success("✨ ¡Adecuación lista!")
                st.download_button("⬇️ Descargar", data=archivo_word, file_name=f"PACI_{curso_sel}.docx")
            except Exception as e:
                st.error(f"Error: {e}")
