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
    """Lee el contenido de un archivo Word."""
    doc = docx.Document(archivo)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def crear_docx_adaptado(texto_adaptado):
    """Crea un nuevo archivo Word con el texto procesado."""
    doc = docx.Document()
    for linea in texto_adaptado.split('\n'):
        if linea.strip(): 
            doc.add_paragraph(linea.replace('**', ''))
    
    archivo_memoria = BytesIO()
    doc.save(archivo_memoria)
    archivo_memoria.seek(0)
    return archivo_memoria

def adaptar_prueba_con_ia(texto_original, curso, asignatura, necesidad, api_key):
    """Conecta con Google Gemini para adaptar el contenido."""
    genai.configure(api_key=api_key)
    
    # SOLUCIÓN DEL ERROR: Usamos gemini-1.0-pro que es 100% compatible
    modelo = genai.GenerativeModel('gemini-1.0-pro')
    
    instrucciones = {
        "TDAH": "Acorta oraciones, usa viñetas, resalta verbos de acción y elimina distractores.",
        "TEA": "Usa lenguaje literal, instrucciones paso a paso y evita metáforas o lenguaje ambiguo.",
        "Trastorno del Lenguaje": "Usa vocabulario simple, frases cortas y estructuras gramaticales sencillas."
    }
    
    prompt = f"""
    Eres un experto en Educación Diferencial y adecuaciones PACI en Chile.
    Tu tarea es adaptar la siguiente prueba de {asignatura} para un nivel de {curso}.
    El estudiante presenta {necesidad}, por lo que debes aplicar estos criterios: {instrucciones[necesidad]}
    
    Mantén el contenido pedagógico pero ajusta la forma y complejidad del lenguaje según el nivel.
    
    TEXTO DE LA PRUEBA A ADAPTAR:
    {texto_original}
    """
    
    response = modelo.generate_content(prompt)
    return response.text

# --- INTERFAZ DE USUARIO ---
st.title("📘 Generador PACI Profesional")
st.markdown("Sube una prueba en formato Word y la IA la adaptará automáticamente según el perfil del estudiante.")

with st.sidebar:
    st.header("⚙️ Configuración")
    
    if api_key_configurada:
        st.success("✅ IA conectada vía Secrets")
        final_api_key = api_key_configurada
    else:
        st.warning("⚠️ Clave no detectada en Secrets")
        final_api_key = st.text_input("Ingresa API Key manualmente:", type="password")
    
    st.divider()
    
    curso_sel = st.selectbox("Curso:", ["1ro Básico", "2do Básico", "3ro Básico", "4to Básico", "5to Básico", "6to Básico", "7mo Básico", "8vo Básico", "1ro Medio", "2do Medio", "3ro Medio", "4to Medio"])
    asignatura_sel = st.selectbox("Asignatura:", ["Lenguaje", "Matemáticas", "Historia", "Ciencias", "Inglés"])
    necesidad_sel = st.selectbox("Necesidad (PIE):", ["TDAH", "TEA", "Trastorno del Lenguaje"])

# --- ÁREA DE CARGA Y PROCESAMIENTO ---
archivo_subido = st.file_uploader("Sube la prueba original (.docx)", type=["docx"])

if archivo_subido:
    if st.button("🚀 Generar Adecuación"):
        if not final_api_key:
            st.error("Error: No hay una API Key configurada. Revisa los Secrets de Streamlit.")
        else:
            try:
                with st.spinner("La IA está analizando y adaptando la prueba..."):
                    texto_original = leer_docx(archivo_subido)
                    texto_paci = adaptar_prueba_con_ia(texto_original, curso_sel, asignatura_sel, necesidad_sel, final_api_key)
                    archivo_descarga = crear_docx_adaptado(texto_paci)
                    
                    st.success("✨ ¡Adecuación lista!")
                    st.download_button(
                        label="⬇️ Descargar Prueba Adaptada",
                        data=archivo_descarga,
                        file_name=f"Prueba_{asignatura_sel}_{curso_sel}_PACI.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                    
                    with st.expander("Ver vista previa del texto adaptado"):
                        st.write(texto_paci)
            
            except Exception as e:
                st.error(f"Hubo un error técnico: {e}")
