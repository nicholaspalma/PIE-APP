import streamlit as st
import docx
from docx.shared import Pt
import google.generativeai as genai
from io import BytesIO
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="PACI Experto Pro G3", page_icon="👩‍🏫", layout="centered")

api_key_configurada = st.secrets.get("GEMINI_API_KEY", None)

def leer_docx(archivo):
    doc = docx.Document(archivo)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def crear_docx_adaptado(texto_adaptado):
    if os.path.exists("plantilla.docx"):
        doc = docx.Document("plantilla.docx")
    else:
        doc = docx.Document()

    lineas = [l for l in texto_adaptado.split('\n') if l.strip()]
    
    # --- LÓGICA DE TÍTULO NO REDUNDANTE ---
    # La primera línea es el título. Las demás son el cuerpo.
    titulo_ia = lineas[0].replace('#', '').strip() if lineas else "Evaluación Adecuada"
    cuerpo_prueba = lineas[1:] 

    # Reemplazo del tag {titulo} en la plantilla original
    for p in doc.paragraphs:
        if "{titulo}" in p.text:
            p.text = p.text.replace("{titulo}", titulo_ia)
            for run in p.runs:
                run.bold = True

    # --- PROCESAMIENTO DEL CUERPO ---
    letra_opcion = 0
    abc = ["a)", "b)", "c)", "d)", "e)"]
    dibujo_realizado = False 

    for linea in cuerpo_prueba:
        # Limpieza de formatos Markdown
        linea_limpia = linea.replace('---', '').replace('**', '').replace('\\_', '').replace('____', '______').strip()
        
        if linea_limpia:
            # Formateo de alternativas de selección múltiple [cite: 229-232, 297-300]
            if linea_limpia.startswith(('*', '-', '•')):
                texto_final = f"{abc[letra_opcion % 5]} {linea_limpia[1:].strip()}"
                letra_opcion += 1
            else:
                texto_final = linea_limpia
                if not any(texto_final.startswith(x) for x in abc):
                    letra_opcion = 0 # Reinicia si es una pregunta nueva

            p = doc.add_paragraph(texto_final)
            
            # SEPARACIÓN: 12 puntos entre cada pregunta/párrafo 
            p.paragraph_format.space_after = Pt(12)

            # Destacar títulos de sección
            if any(x in texto_final.upper() for x in ["PARTE", "INSTRUCCIÓN"]):
                if p.runs:
                    p.runs[0].bold = True
                p.paragraph_format.space_before = Pt(18)
            
            # ESPACIO PARA DIBUJAR: 10 líneas 
            if ("DIBUJA" in texto_final.upper() or "DIBUJO" in texto_final.upper()) and not dibujo_realizado:
                for _ in range(10): 
                    doc.add_paragraph("")
                dibujo_realizado = True 
    
    archivo_memoria = BytesIO()
    doc.save(archivo_memoria)
    archivo_memoria.seek(0)
    return archivo_memoria

def adaptar_prueba_con_ia(texto_original, curso, asignatura, necesidad, api_key):
    genai.configure(api_key=api_key)
    
    # SELECCIÓN DEL MODELO MÁS AVANZADO (Gemini 3 Flash Preview)
    modelo = genai.GenerativeModel('gemini-3-flash-preview')
    
    prompt = f"""
    Actúa como una Educadora Diferencial con 20 años de experiencia. 
    ADAPTA esta prueba de {asignatura} para {curso} con {necesidad}.

    REGLAS DE FORMATO:
    1. La primera línea de tu respuesta DEBE ser el título de la prueba.
    2. Usa viñetas (*) para las alternativas.
    3. Para Verdadero o Falso usa exactamente: ______
    4. MANTÉN el espacio de dibujo al final.
    5. Prohibido saludar o dar introducciones. Solo la prueba.
    6. No dupliques campos de nombre o curso.

    TEXTO ORIGINAL:
    {texto_original}
    """
    
    response = modelo.generate_content(prompt)
    return response.text

# --- INTERFAZ ---
st.title("👩‍🏫 PACI Pro: Nivel Gemini 3")

with st.sidebar:
    st.header("⚙️ Configuración")
    final_api_key = api_key_configurada if api_key_configurada else st.text_input("API Key:", type="password")
    
    st.divider()
    asignatura_sel = st.selectbox("Asignatura:", ["Lenguaje", "Matemáticas", "Historia", "Ciencias", "Inglés"])
    curso_sel = st.selectbox("Curso:", ["1ro Básico", "2do Básico", "3ro Básico", "4to Básico", "5to Básico", "6to Básico", "7mo Básico", "8vo Básico"])
    necesidad_sel = st.selectbox("Necesidad (PIE):", ["TEA", "TDAH", "Trastorno del Lenguaje"])

archivo = st.file_uploader("Sube la prueba original (.docx)", type=["docx"])

if archivo and st.button("🚀 Ejecutar Adecuación"):
    if not final_api_key:
        st.error("Falta la API Key.")
    else:
        with st.spinner("Gemini 3 está adaptando el material con precisión experta..."):
            try:
                texto_paci = adaptar_prueba_con_ia(leer_docx(archivo), curso_sel, asignatura_sel, necesidad_sel, final_api_key)
                archivo_word = crear_docx_adaptado(texto_paci)
                st.success("✨ ¡Adecuación lista!")
                st.download_button("⬇️ Descargar", data=archivo_word, file_name=f"PACI_{curso_sel}.docx")
            except Exception as e:
                st.error(f"Error técnico: {e}")
