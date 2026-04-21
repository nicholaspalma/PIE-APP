import streamlit as st
import docx
from docx.shared import Pt
import google.generativeai as genai
from io import BytesIO
import os

# --- CONFIGURACIÓN DE PÁGINA ---
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

    # Filtramos líneas vacías y pre-procesamos
    lineas = [l.strip() for l in texto_adaptado.split('\n') if l.strip()]
    
    # --- LÓGICA DE TÍTULO ---
    titulo_ia = lineas[0].replace('#', '').strip() if lineas else "Evaluación Adecuada"
    cuerpo_crudo = lineas[1:] 

    # Reemplazo del tag {titulo} en la plantilla
    for p in doc.paragraphs:
        if "{titulo}" in p.text:
            p.text = p.text.replace("{titulo}", titulo_ia)
            for run in p.runs:
                run.bold = True

    # --- PROCESAMIENTO DEL CUERPO (CON FILTROS) ---
    letra_opcion = 0
    abc = ["a)", "b)", "c)", "d)", "e)"]
    dibujo_listo = False 
    palabras_prohibidas = ["NOMBRE", "CURSO", "FECHA", "APELLIDO", "RUT", "PUNTAJE"]

    for linea in cuerpo_crudo:
        # 1. FILTRO DE REDUNDANCIA: Saltamos líneas que tengan datos que ya están en el cuadro
        if any(p in linea.upper() for p in palabras_prohibidas) and len(linea) < 50:
            continue

        # 2. LIMPIEZA DE LÍNEAS VERTICALES Y SÍMBOLOS
        linea_limpia = linea.replace('|', '').replace('---', '').replace('**', '').replace('\\_', '').replace('____', '______').strip()
        
        if linea_limpia:
            # Lógica de alternativas
            if linea_limpia.startswith(('*', '-', '•')):
                texto_final = f"{abc[letra_opcion % 5]} {linea_limpia[1:].strip()}"
                letra_opcion += 1
            else:
                texto_final = linea_limpia
                if not any(texto_final.startswith(x) for x in abc):
                    letra_opcion = 0

            p = doc.add_paragraph(texto_final)
            p.paragraph_format.space_after = Pt(12) # Separación entre preguntas

            # Formato de Títulos
            if any(x in texto_final.upper() for x in ["PARTE", "INSTRUCCIÓN"]):
                if p.runs:
                    p.runs[0].bold = True
                p.paragraph_format.space_before = Pt(18)
            
            # ESPACIO PARA DIBUJAR: 10 líneas limpias
            if ("DIBUJA" in texto_final.upper() or "DIBUJO" in texto_final.upper()) and not dibujo_listo:
                for _ in range(10): 
                    doc.add_paragraph("")
                dibujo_listo = True 
    
    archivo_memoria = BytesIO()
    doc.save(archivo_memoria)
    archivo_memoria.seek(0)
    return archivo_memoria

def adaptar_prueba_con_ia(texto_original, curso, asignatura, necesidad, api_key):
    genai.configure(api_key=api_key)
    
    # USAMOS EL MODELO MÁS AVANZADO (GEMINI 3 FLASH PREVIEW)
    modelo = genai.GenerativeModel('gemini-3-flash-preview')
    
    prompt = f"""
    Actúa como una Educadora Diferencial con 20 años de experiencia. 
    ADAPTA esta prueba de {asignatura} para {curso} con {necesidad}.

    REGLAS DE ORO:
    1. La primera línea DEBE ser el título.
    2. Usa viñetas (*) para las alternativas.
    3. Para Verdadero o Falso usa: ______
    4. NO USES tablas ni el símbolo | (línea vertical).
    5. NO incluyas encabezados de "Nombre", "Curso", etc. Salta directo a la prueba.
    6. MANTÉN el espacio de dibujo con una instrucción clara.
    7. Prohibido saludar o explicar lo que haces.

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
        with st.spinner("Gemini 3 está procesando la adecuación..."):
            try:
                texto_paci = adaptar_prueba_con_ia(leer_docx(archivo), curso_sel, asignatura_sel, necesidad_sel, final_api_key)
                archivo_word = crear_docx_adaptado(texto_paci)
                st.success("✨ ¡Adecuación lista!")
                st.download_button("⬇️ Descargar Word", data=archivo_word, file_name=f"PACI_{curso_sel}.docx")
            except Exception as e:
                st.error(f"Error técnico: {e}")
