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
    # La primera línea que no esté vacía será el título
    titulo_ia = next((l.replace('#', '').strip() for l in lineas if l.strip()), "Prueba Adecuada")
    cuerpo_prueba = lineas

    # 1. REEMPLAZO DE {titulo} EN LA PLANTILLA
    for p in doc.paragraphs:
        if "{titulo}" in p.text:
            p.text = p.text.replace("{titulo}", titulo_ia)
            for run in p.runs:
                run.bold = True

    # 2. PROCESAMIENTO DEL CUERPO
    letra_opcion = 0
    abc = ["a)", "b)", "c)", "d)", "e)"]
    dibujo_listo = False 

    for linea in cuerpo_prueba:
        # Limpieza profunda de símbolos
        linea_limpia = linea.replace('---', '').replace('**', '').replace('\\_', '').replace('____', '______').strip()
        
        if linea_limpia:
            # Lógica para alternativas (convertir * o - en letras a, b, c)
            if linea_limpia.startswith(('*', '-', '•')):
                texto_final = f"{abc[letra_opcion % 5]} {linea_limpia[1:].strip()}"
                letra_opcion += 1
            else:
                texto_final = linea_limpia
                if not any(texto_final.startswith(x) for x in abc):
                    letra_opcion = 0 # Reinicia letras si no es una alternativa

            p = doc.add_paragraph(texto_final)
            
            # Espaciado entre preguntas [cite: 228-232]
            p.paragraph_format.space_after = Pt(8)

            # Formato de Títulos de Sección
            if any(x in texto_final.upper() for x in ["PARTE", "INSTRUCCIÓN"]):
                p.runs[0].bold = True
                p.paragraph_format.space_before = Pt(14)
            
            # ESPACIO PARA DIBUJAR (Solo una vez y tamaño controlado) 
            if ("DIBUJA" in texto_final.upper() or "DIBUJO" in texto_final.upper()) and not dibujo_listo:
                for _ in range(5): 
                    doc.add_paragraph("")
                dibujo_listo = True 
    
    archivo_memoria = BytesIO()
    doc.save(archivo_memoria)
    archivo_memoria.seek(0)
    return archivo_memoria

def adaptar_prueba_con_ia(texto_original, curso, asignatura, necesidad, api_key):
    genai.configure(api_key=api_key)
    
    # Intentamos usar el modelo Flash (el más rápido) con un nombre alternativo si falla
    try:
        modelo = genai.GenerativeModel('gemini-1.5-flash-latest')
    except:
        modelo = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Eres una Educadora Diferencial con 20 años de experiencia en Chile. 
    ADAPTA esta prueba de {asignatura} para {curso} (Necesidad: {necesidad}).

    INSTRUCCIONES TÉCNICAS:
    1. Comienza con el título de la prueba.
    2. Usa viñetas (*) para las alternativas de selección múltiple.
    3. Para Verdadero o Falso usa este formato: ______ (línea de 6 guiones).
    4. MANTÉN la sección de dibujo al final con una instrucción clara.
    5. No incluyas saludos ni explicaciones de lo que vas a hacer.
    6. No dupliques el encabezado de nombre/curso.

    TEXTO A ADAPTAR:
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
    # Volvemos a poner la Asignatura
    asignatura_sel = st.selectbox("Asignatura:", ["Lenguaje", "Matemáticas", "Historia", "Ciencias", "Inglés"])
    curso_sel = st.selectbox("Curso:", ["1ro Básico", "2do Básico", "3ro Básico", "4to Básico", "5to Básico", "6to Básico", "7mo Básico", "8vo Básico"])
    necesidad_sel = st.selectbox("Necesidad (PIE):", ["TEA", "TDAH", "Trastorno del Lenguaje"])

archivo = st.file_uploader("Sube la prueba original (.docx)", type=["docx"])

if archivo and st.button("🚀 Generar Word Profesional"):
    if final_api_key:
        with st.spinner("La educadora virtual está trabajando rápidamente..."):
            try:
                texto_paci = adaptar_prueba_con_ia(leer_docx(archivo), curso_sel, asignatura_sel, necesidad_sel, final_api_key)
                archivo_word = crear_docx_adaptado(texto_paci)
                st.success("✨ ¡Adecuación lista!")
                st.download_button("⬇️ Descargar", data=archivo_word, file_name=f"PACI_{curso_sel}.docx")
            except Exception as e:
                st.error(f"Error: {e}")
