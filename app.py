import streamlit as st
import docx
import google.generativeai as genai
from io import BytesIO

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Adecuaciones PACI", page_icon="📘", layout="centered")

# --- LÓGICA DE LA API KEY (SECRETS) ---
api_key_configurada = st.secrets.get("GEMINI_API_KEY", None)

# --- FUNCIONES ---
def leer_docx(archivo):
    doc = docx.Document(archivo)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def crear_docx_adaptado(texto_adaptado):
    doc = docx.Document()
    for linea in texto_adaptado.split('\n'):
        if linea.strip(): 
            doc.add_paragraph(linea.replace('**', ''))
    archivo_memoria = BytesIO()
    doc.save(archivo_memoria)
    archivo_memoria.seek(0)
    return archivo_memoria

def adaptar_prueba_con_ia(texto_original, curso, asignatura, necesidad, api_key):
    # Configuración de la API
    genai.configure(api_key=api_key)
    
    # Usamos el modelo estable 1.5
    modelo = genai.GenerativeModel('gemini-1.5-flash')
    
    # --- TU PROMPT PERSONALIZADO DE EXPERTA ---
    # Aquí incorporamos tu idea de la Educadora Diferencial con 20 años de experiencia
    prompt = f"""
    Eres una Educadora Diferencial con más de 20 años de experiencia en el sistema escolar chileno y experta en Decretos 83 y 170.
    
    Tu misión es ejecutar una adecuación curricular de la prueba de {asignatura} que se adjunta, diseñada para un nivel de {curso}.
    El estudiante para el cual debes adaptar el material presenta: {necesidad}.
    
    Como experta, debes realizar lo siguiente:
    1. Graduar la complejidad del lenguaje manteniendo el Objetivo de Aprendizaje (OA).
    2. Si es TEA: Usa lenguaje literal, evita ambigüedades y fragmenta las instrucciones paso a paso.
    3. Si es TDAH: Resalta palabras clave, usa frases cortas y elimina información irrelevante que distraiga.
    4. Si es Trastorno del Lenguaje: Simplifica la estructura gramatical y usa vocabulario de alta frecuencia.
    
    Entrega la prueba adaptada completa, lista para ser copiada a Word. No des explicaciones ni saludos, solo el contenido de la evaluación.
    
    TEXTO ORIGINAL DE LA PRUEBA:
    {texto_original}
    """
    
    response = modelo.generate_content(prompt)
    return response.text

# --- INTERFAZ DE USUARIO ---
st.title("📘 Generador PACI Profesional")
st.markdown("Plataforma de apoyo para Educadoras Diferenciales y especialistas PIE.")

with st.sidebar:
    st.header("⚙️ Configuración")
    
    if api_key_configurada:
        st.success("✅ IA conectada vía Secrets")
        final_api_key = api_key_configurada
    else:
        st.warning("⚠️ Clave no detectada")
        final_api_key = st.text_input("Ingresa API Key manualmente:", type="password")
    
    st.divider()
    
    curso_sel = st.selectbox("Curso:", ["1ro Básico", "2do Básico", "3ro Básico", "4to Básico", "5to Básico", "6to Básico", "7mo Básico", "8vo Básico", "1ro Medio", "2do Medio", "3ro Medio", "4to Medio"])
    asignatura_sel = st.selectbox("Asignatura:", ["Lenguaje", "Matemáticas", "Historia", "Ciencias", "Inglés"])
    necesidad_sel = st.selectbox("Necesidad (PIE):", ["TEA", "TDAH", "Trastorno del Lenguaje"])

# --- ÁREA DE PROCESAMIENTO ---
archivo_subido = st.file_uploader("Sube la prueba original (.docx)", type=["docx"])

if archivo_subido and st.button("🚀 Ejecutar Adecuación Experta"):
    if not final_api_key:
        st.error("Error: Falta la clave de la IA.")
    else:
        try:
            with st.spinner("La Educadora Diferencial virtual está trabajando en la adecuación..."):
                texto_original = leer_docx(archivo_subido)
                texto_paci = adaptar_prueba_con_ia(texto_original, curso_sel, asignatura_sel, necesidad_sel, final_api_key)
                archivo_descarga = crear_docx_adaptado(texto_paci)
                
                st.success("✨ ¡Adecuación completada con éxito!")
                st.download_button(
                    label="⬇️ Descargar Prueba Adaptada",
                    data=archivo_descarga,
                    file_name=f"Adaptacion_{asignatura_sel}_{necesidad_sel}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
                with st.expander("Ver vista previa"):
                    st.write(texto_paci)
        
        except Exception as e:
            st.error(f"Hubo un error técnico: {e}")
