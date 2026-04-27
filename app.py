import streamlit as st
import docx
from docx.shared import Pt
import google.generativeai as genai
from io import BytesIO
import os
import base64

# --- 1. CONFIGURACIÓN INICIAL DE LA PÁGINA ---
st.set_page_config(page_title="PACI Experto Pro", page_icon="👩‍🏫", layout="wide")

# --- 2. CONFIGURACIÓN DE LA API KEY (EL PROBLEMA ESTABA AQUÍ) ---
# Intentamos obtener la clave de los secrets de Streamlit
try:
    api_key_configurada = st.secrets["GEMINI_API_KEY"]
except KeyError:
    api_key_configurada = None

# --- 3. DISEÑO VISUAL (CSS) ---
def apply_custom_ui(image_file):
    try:
        if os.path.exists(image_file):
            with open(image_file, "rb") as f:
                encoded_string = base64.b64encode(f.read()).decode()
            st.markdown(f"""
                <style>
                .stApp {{
                    background-image: url("data:image/png;base64,{encoded_string}");
                    background-size: cover;
                    background-attachment: fixed;
                }}
                .top-header {{
                    background-color: rgba(255, 255, 255, 0.95); 
                    border-radius: 15px; 
                    padding: 15px;
                    text-align: center; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }}
                .item-card {{
                    background-color: rgba(255, 255, 255, 0.95);
                    border-radius: 15px; 
                    padding: 25px; 
                    margin-bottom: 20px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                [data-testid="stSidebar"] {{ display: none; }}
                </style>
                """, unsafe_allow_html=True)
        else:
             st.markdown("""<style>.stApp { background-color: #f0f8ff; }</style>""", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"No se pudo cargar el fondo: {e}")

# Aplicar el diseño
apply_custom_ui("fondo.png")

st.markdown('<div class="top-header"><h1>👩‍🏫 PACI Pro: Nivel Gemini 3</h1></div>', unsafe_allow_html=True)

# --- 4. FUNCIONES DE PROCESAMIENTO ---
def leer_docx(archivo):
    doc = docx.Document(archivo)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def crear_docx_adaptado(texto_adaptado, titulo_documento):
    if os.path.exists("plantilla.docx"):
        doc = docx.Document("plantilla.docx")
    else:
        doc = docx.Document()
        # Si no hay plantilla, crear un título básico
        t = doc.add_paragraph(titulo_documento)
        t.alignment = 1 # Centrado
        t.runs[0].bold = True
        t.runs[0].font.size = Pt(16)
        doc.add_paragraph("") 

    lineas = [l.strip() for l in texto_adaptado.split('\n') if l.strip()]
    cuerpo_prueba = lineas[1:] # Omitimos la línea 0 porque es el título

    # Reemplazo de {titulo} en la plantilla
    for p in doc.paragraphs:
        if "{titulo}" in p.text:
            p.text = p.text.replace("{titulo}", titulo_documento)
            for run in p.runs: 
                run.bold = True
                run.font.size = Pt(16)

    letra_opcion = 0
    abc = ["a)", "b)", "c)", "d)", "e)"]

    for linea in cuerpo_prueba:
        linea_limpia = linea.replace('---', '').replace('**', '').replace('\\_', '').strip()
        
        if linea_limpia:
            # Alternativas (a, b, c)
            if linea_limpia.startswith(('*', '-', '•')):
                texto_final = f"      {abc[letra_opcion % 5]} {linea_limpia[1:].strip()}"
                letra_opcion += 1
            else:
                texto_final = linea_limpia
                if not any(texto_final.startswith(x) for x in abc):
                    letra_opcion = 0

            p = doc.add_paragraph(texto_final)
            p.paragraph_format.space_after = Pt(12)

            # Formato de Títulos de Sección
            if "PARTE" in texto_final.upper() or "INSTRUCCIÓN" in texto_final.upper():
                p.runs[0].bold = True
                p.paragraph_format.space_before = Pt(18)
            
            # Espacio para dibujar
            if "DIBUJA" in texto_final.upper() or "DIBUJO" in texto_final.upper():
                for _ in range(8): 
                    doc.add_paragraph("")
    
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def adaptar_prueba_con_ia(texto_original, curso, asignatura, necesidad, api_key, modelo_nombre):
    genai.configure(api_key=api_key)
    modelo = genai.GenerativeModel(modelo_nombre)
    
    prompt = f"""
    Eres una Educadora Diferencial con 20 años de experiencia. 
    ADAPTA esta prueba de {asignatura} para {curso} con {necesidad}.

    REGLAS ESTRICTAS DE FORMATO Y CONTENIDO:
    1. NO SALUDES, NO TE DESPIDAS. Empieza directamente con el contenido.
    2. La PRIMERA LÍNEA de tu respuesta DEBE ser el título de la prueba.
    3. NO incluyas encabezados para nombre, fecha o curso (ya están en el documento).
    4. Usa viñetas (*) para las alternativas de selección múltiple.
    5. Para preguntas de Verdadero o Falso usa exactamente este formato: ______ (seis guiones bajos).
    6. NO uses tablas ni el símbolo | (línea vertical).
    7. Mantén el espacio de dibujo con una instrucción clara si la prueba original lo requiere.

    TEXTO ORIGINAL DE LA PRUEBA:
    {texto_original}
    """
    
    response = modelo.generate_content(prompt)
    return response.text

# --- 5. INTERFAZ DE USUARIO ---
st.markdown('<div class="item-card">', unsafe_allow_html=True)
st.markdown("### 1. Configura la adecuación")

# Obtenemos la API Key (de secrets o manual)
api_key_input = api_key_configurada if api_key_configurada else st.text_input("Ingresa tu API Key (obligatorio si no está en Secrets):", type="password")

col1, col2, col3 = st.columns(3)
with col1: asignatura_sel = st.selectbox("Asignatura:", ["Lenguaje", "Matemáticas", "Historia", "Ciencias", "Inglés"])
with col2: curso_sel = st.selectbox("Curso:", ["1ro Básico", "2do Básico", "3ro Básico", "4to Básico", "5to Básico", "6to Básico", "7mo Básico", "8vo Básico"])
with col3: necesidad_sel = st.selectbox("Necesidad (PIE):", ["TEA", "TDAH", "Trastorno del Lenguaje"])

# Selector de modelo dinámico (solo se muestra si hay una API Key válida)
modelo_elegido = None
if api_key_input:
    try:
        genai.configure(api_key=api_key_input)
        modelos_disponibles = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        modelos_gemini = [m for m in modelos_disponibles if 'gemini' in m and 'vision' not in m]
        if modelos_gemini:
            modelo_elegido = st.selectbox("🤖 Modelo de IA detectado (Elige el más avanzado):", modelos_gemini, index=len(modelos_gemini)-1) # Selecciona el último de la lista, que suele ser el más nuevo
        else:
            st.error("Tu API Key es válida, pero no tienes modelos de texto disponibles.")
    except Exception as e:
        st.error("La API Key ingresada no es válida o no tiene permisos.")

st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="item-card">', unsafe_allow_html=True)
st.markdown("### 2. Sube tu archivo")
archivo = st.file_uploader("Arrastra aquí tu prueba original (.docx)", type=["docx"])

if archivo and st.button("🚀 Generar Adecuación Profesional", use_container_width=True):
    if not api_key_input:
        st.error("Falta la API Key.")
    elif not modelo_elegido:
        st.error("No se ha seleccionado un modelo válido.")
    else:
        with st.spinner(f"La educadora virtual está trabajando (usando {modelo_elegido})..."):
            try:
                texto_original = leer_docx(archivo)
                texto_paci = adaptar_prueba_con_ia(texto_original, curso_sel, asignatura_sel, necesidad_sel, api_key_input, modelo_elegido)
                
                # Extraemos el título generado por la IA (la primera línea)
                lineas_ia = [l.strip() for l in texto_paci.split('\n') if l.strip()]
                titulo_documento = lineas_ia[0] if lineas_ia else f"Evaluación Adaptada - {asignatura_sel}"
                
                archivo_word = crear_docx_adaptado(texto_paci, titulo_documento)
                
                st.balloons()
                st.success("✨ ¡Adecuación lista!")
                st.download_button("⬇️ Descargar Documento Adaptado", data=archivo_word, file_name=f"PACI_{asignatura_sel}_{curso_sel}.docx", use_container_width=True)
                
                with st.expander("Ver texto generado por la IA (Modo Desarrollador)"):
                    st.text(texto_paci) 
            except Exception as e:
                st.error(f"Error técnico durante la generación: {e}")
st.markdown('</div>', unsafe_allow_html=True)
