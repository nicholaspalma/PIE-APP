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
    
    # --- LOGICA PARA EL TÍTULO ÚNICO ---
    titulo_ia = ""
    cuerpo_limpio = []
    encontrado = False
    
    for l in lineas:
        if l.strip() and not encontrado:
            titulo_ia = l.replace('#', '').strip()
            encontrado = True # El primer texto que encuentra es el título
        else:
            cuerpo_limpio.append(l)

    # Reemplazo en la plantilla
    for p in doc.paragraphs:
        if "{titulo}" in p.text:
            p.text = p.text.replace("{titulo}", titulo_ia)
            for run in p.runs:
                run.bold = True

    # --- PROCESAMIENTO DEL CUERPO ---
    letra_opcion = 0
    abc = ["a)", "b)", "c)", "d)", "e)"]
    espacio_dibujo_creado = False 

    for linea in cuerpo_limpio:
        linea_limpia = linea.replace('---', '').replace('**', '').replace('\\_', '').replace('____', '______').strip()
        
        if linea_limpia:
            # Alternativas (a, b, c)
            if linea_limpia.startswith(('*', '-', '•')):
                texto_final = f"{abc[letra_opcion % 5]} {linea_limpia[1:].strip()}"
                letra_opcion += 1
            else:
                texto_final = linea_limpia
                if not any(texto_final.startswith(x) for x in abc):
                    letra_opcion = 0

            p = doc.add_paragraph(texto_final)
            
            # ESPACIADO MEJORADO: 12 puntos de separación entre cada párrafo/pregunta
            p.paragraph_format.space_after = Pt(12)

            # Formato de Títulos de Sección
            if any(x in texto_final.upper() for x in ["PARTE", "INSTRUCCIÓN"]):
                p.runs[0].bold = True
                p.paragraph_format.space_before = Pt(16)
            
            # ESPACIO PARA DIBUJAR (10 espacios)
            if ("DIBUJA" in texto_final.upper() or "DIBUJO" in texto_final.upper()) and not espacio_dibujo_creado:
                for _ in range(10): 
                    doc.add_paragraph("")
                espacio_dibujo_creado = True 
    
    archivo_memoria = BytesIO()
    doc.save(archivo_memoria)
    archivo_memoria.seek(0)
    return archivo_memoria

def adaptar_prueba_con_ia(texto_original, curso, asignatura, necesidad, api_key):
    genai.configure(api_key=api_key)
    
    # MODELO POR DEFECTO: El más avanzado y rápido (Gemini 1.5 Flash)
    # Nota: Los nombres "2.5" o "3" no existen oficialmente en la API aún, 
    # por lo que usamos la versión 1.5 que es la actual de alto rendimiento.
    modelo = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Actúa como una Educadora Diferencial con 20 años de experiencia. 
    ADAPTA esta prueba de {asignatura} para {curso} con {necesidad}.

    REGLAS DE FORMATO:
    1. La primera línea DEBE ser el título de la prueba.
    2. Usa viñetas (*) para las alternativas.
    3. Para Verdadero o Falso usa: ______
    4. MANTÉN siempre una sección de dibujo al final.
    5. Prohibido saludar, solo entrega la prueba.
    
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
    asignatura_sel = st.selectbox("Asignatura:", ["Lenguaje", "Matemáticas", "Historia", "Ciencias", "Inglés"])
    curso_sel = st.selectbox("Curso:", ["1ro Básico", "2do Básico", "3ro Básico", "4to Básico", "5to Básico", "6to Básico", "7mo Básico", "8vo Básico"])
    necesidad_sel = st.selectbox("Necesidad (PIE):", ["TEA", "TDAH", "Trastorno del Lenguaje"])

archivo = st.file_uploader("Sube la prueba (.docx)", type=["docx"])

if archivo and st.button("🚀 Generar Word Profesional"):
    if final_api_key:
        with st.spinner("Procesando con la mejor IA disponible..."):
            try:
                texto_paci = adaptar_prueba_con_ia(leer_docx(archivo), curso_sel, asignatura_sel, necesidad_sel, final_api_key)
                archivo_word = crear_docx_adaptado(texto_paci)
                st.success("✨ ¡Documento generado!")
                st.download_button("⬇️ Descargar", data=archivo_word, file_name=f"PACI_{curso_sel}.docx")
            except Exception as e:
                st.error(f"Error: {e}")
