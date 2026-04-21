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
    
    # Extraer el título de forma segura
    titulo_ia = "Prueba Adecuada"
    for linea in lineas:
        if linea.strip():
            titulo_ia = linea.replace('#', '').strip()
            break

    cuerpo_prueba = lineas

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
        # Limpieza de símbolos
        linea_limpia = linea.replace('---', '').replace('**', '').replace('\\_', '').replace('____', '______').strip()
        
        if linea_limpia:
            # Formatear alternativas a, b, c
            if linea_limpia.startswith(('*', '-', '•')):
                texto_final = f"{abc[letra_opcion % 5]} {linea_limpia[1:].strip()}"
                letra_opcion += 1
            else:
                texto_final = linea_limpia
                if not any(texto_final.startswith(x) for x in abc):
                    letra_opcion = 0

            p = doc.add_paragraph(texto_final)
            p.paragraph_format.space_after = Pt(8)

            # Formato de Títulos de Sección
            if any(x in texto_final.upper() for x in ["PARTE", "INSTRUCCIÓN", "INSTRUCCIONES"]):
                p.runs[0].bold = True
                p.paragraph_format.space_before = Pt(14)
            
            # ESPACIO PARA DIBUJAR (5 líneas)
            if "DIBUJA" in texto_final.upper() or "DIBUJO" in texto_final.upper():
                for _ in range(5): 
                    doc.add_paragraph("")
    
    archivo_memoria = BytesIO()
    doc.save(archivo_memoria)
    archivo_memoria.seek(0)
    return archivo_memoria

def adaptar_prueba_con_ia(texto_original, curso, asignatura, necesidad, api_key):
    genai.configure(api_key=api_key)
    
    # SOLUCIÓN DEL ERROR: Usar el modelo 'gemini-pro'
    modelo = genai.GenerativeModel('gemini-pro')
    
    instrucciones_tecnicas = {
        "TDAH": "Acorta oraciones, usa viñetas, resalta verbos de acción y elimina distractores.",
        "TEA": "Usa lenguaje literal, instrucciones paso a paso y evita metáforas o lenguaje ambiguo. MANTÉN la sección de dibujo.",
        "Trastorno del Lenguaje": "Usa vocabulario simple, frases cortas y estructuras gramaticales sencillas."
    }
    
    prompt = f"""
    Actúa como una Educadora Diferencial con 20 años de experiencia en el Programa de Integración Escolar (PIE) en Chile, experta en el Decreto 83.
    
    Realiza una adaptación curricular de la siguiente prueba de {asignatura} para un estudiante de {curso} con {necesidad}.
    
    Aplica rigurosamente estos criterios:
    {instrucciones_tecnicas[necesidad]}
    
    REGLAS ESTRICTAS DE FORMATO:
    1. La primera línea DEBE ser el título de la prueba.
    2. Usa viñetas (*) para las alternativas de selección múltiple.
    3. Para Verdadero o Falso usa exactamente este formato: ______ (guiones bajos).
    4. NO incluyas saludos, despedidas, ni explicaciones sobre lo que hiciste.
    5. NO incluyas encabezados para nombre, fecha o curso.
    
    TEXTO ORIGINAL DE LA PRUEBA:
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
    curso_sel = st.selectbox("Curso:", ["1ro Básico", "2do Básico", "3ro Básico", "4to Básico", "5to Básico", "6to Básico", "7mo Básico", "8vo Básico", "1ro Medio", "2do Medio", "3ro Medio", "4to Medio"])
    asignatura_sel = st.selectbox("Asignatura:", ["Lenguaje", "Matemáticas", "Historia", "Ciencias", "Inglés"])
    necesidad_sel = st.selectbox("Necesidad (PIE):", ["TEA", "TDAH", "Trastorno del Lenguaje"])

archivo = st.file_uploader("Sube la prueba original (.docx)", type=["docx"])

if archivo and st.button("🚀 Generar Word Profesional"):
    if not final_api_key:
        st.error("Falta la API Key en los Secrets de Streamlit.")
    else:
        try:
            with st.spinner("La educadora virtual está trabajando en la adaptación..."):
                texto_paci = adaptar_prueba_con_ia(leer_docx(archivo), curso_sel, asignatura_sel, necesidad_sel, final_api_key)
                archivo_word = crear_docx_adaptado(texto_paci)
                st.success("✨ ¡Adecuación lista!")
                st.download_button("⬇️ Descargar", data=archivo_word, file_name=f"PACI_{curso_sel}.docx")
                with st.expander("Ver vista previa"):
                    st.write(texto_paci)
        except Exception as e:
            st.error(f"Error técnico: {e}")
