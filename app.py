import streamlit as st
import docx
from docx.shared import Pt
import google.generativeai as genai
from io import BytesIO
import os
import base64  # Necesario para codificar la imagen de fondo

# --- CONFIGURACIÓN DE PÁGINA ---
# Usamos layout="wide" para un diseño más moderno y espacioso
st.set_page_config(
    page_title="PACI Experto Pro G3", 
    page_icon="👩‍🏫", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNCIÓN PARA APLICAR FONDO DE PANTALLA PERSONALIZADO ---
# Streamlit requiere este truco de CSS para fondos de imagen locales
def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{encoded_string.decode()}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    # .stApp > header {{
    #     background-color: rgba(0,0,0,0);
    # }}
    
    # .stApp > div:nth-child(1) {{
    #     background-color: rgba(0,0,0,0);
    # }}
    </style>
    """,
    unsafe_allow_html=True
    )

# --- APLICAR EL FONDO ---
# Asegúrate de que 'fondo.png' esté en la misma carpeta en GitHub
if os.path.exists("fondo.png"):
    add_bg_from_local('fondo.png')
else:
    st.warning("No se encontró el archivo 'fondo.png'. Por favor súbelo a GitHub para ver el fondo personalizado.")


api_key_configurada = st.secrets.get("GEMINI_API_KEY", None)

def leer_docx(archivo):
    doc = docx.Document(archivo)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def crear_docx_adaptado(texto_adaptado):
    if os.path.exists("plantilla.docx"):
        doc = docx.Document("plantilla.docx")
    else:
        doc = docx.Document()

    lineas = [l.strip() for l in texto_adaptado.split('\n') if l.strip()]
    
    titulo_ia = lineas[0].replace('#', '').strip() if lineas else "Evaluación Adecuada"
    cuerpo_crudo = lineas[1:] 

    for p in doc.paragraphs:
        if "{titulo}" in p.text:
            p.text = p.text.replace("{titulo}", titulo_ia)
            for run in p.runs:
                run.bold = True

    letra_opcion = 0
    abc = ["a)", "b)", "c)", "d)", "e)"]
    dibujo_listo = False 
    palabras_prohibidas = ["NOMBRE", "CURSO", "FECHA", "APELLIDO", "RUT", "PUNTAJE"]

    for linea in cuerpo_crudo:
        if any(p in linea.upper() for p in palabras_prohibidas) and len(linea) < 50:
            continue

        linea_limpia = linea.replace('|', '').replace('---', '').replace('**', '').replace('\\_', '').replace('____', '______').strip()
        
        if linea_limpia:
            if linea_limpia.startswith(('*', '-', '•')):
                texto_final = f"{abc[letra_opcion % 5]} {linea_limpia[1:].strip()}"
                letra_opcion += 1
            else:
                texto_final = linea_limpia
                if not any(texto_final.startswith(x) for x in abc):
                    letra_opcion = 0

            p = doc.add_paragraph(texto_final)
            p.paragraph_format.space_after = Pt(12)

            if any(x in texto_final.upper() for x in ["PARTE", "INSTRUCCIÓN"]):
                if p.runs:
                    p.runs[0].bold = True
                p.paragraph_format.space_before = Pt(18)
            
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

# --- BARRA LATERAL (SIDEBAR) MODERNA ---
with st.sidebar:
    # --- AGREGAR LOGOS DE LA SIP ---
    # Asumiendo que image_0.png y image_1.png están en tu repo de GitHub
    if os.path.exists("image_0.png"):
        st.image("image_0.png", use_column_width=True)
    
    st.header("⚙️ Configuración")
    final_api_key = api_key_configurada if api_key_configurada else st.text_input("API Key:", type="password")
    
    st.divider()
    asignatura_sel = st.selectbox("Asignatura:", ["Lenguaje", "Matemáticas", "Historia", "Ciencias", "Inglés"])
    curso_sel = st.selectbox("Curso:", ["1ro Básico", "2do Básico", "3ro Básico", "4to Básico", "5to Básico", "6to Básico", "7mo Básico", "8vo Básico"])
    necesidad_sel = st.selectbox("Necesidad (PIE):", ["TEA", "TDAH", "Trastorno del Lenguaje"])
    
    if os.path.exists("image_1.png"):
        st.image("image_1.png", width=100) # Logo secundario más pequeño abajo

# --- CONTENIDO PRINCIPAL ---
st.title("👩‍🏫 PACI Pro: Nivel Gemini 3")
st.markdown("---")

archivo = st.file_uploader("Sube la prueba original (.docx)", type=["docx"])

if archivo and st.button("🚀 Ejecutar Adecuación"):
    if not final_api_key:
        st.error("Falta la API Key.")
    else:
        # Usamos st.columns para centrar el spinner y hacerlo ver más profesional
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            with st.spinner("Gemini 3 está procesando la adecuación..."):
                try:
                    texto_paci = adaptar_prueba_con_ia(leer_docx(archivo), curso_sel, asignatura_sel, necesidad_sel, final_api_key)
                    archivo_word = crear_docx_adaptado(texto_paci)
                    st.success("✨ ¡Adecuación lista!")
                    st.download_button("⬇️ Descargar Word", data=archivo_word, file_name=f"PACI_{curso_sel}.docx")
                except Exception as e:
                    st.error(f"Error técnico: {e}")
