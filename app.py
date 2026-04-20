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
    genai.configure(api_key=api_key)
    
    # Usamos el modelo más rápido y moderno de Google
    modelo = genai.GenerativeModel('gemini-1.5-flash')
    
    instrucciones = {
        "TDAH": "Acorta oraciones, usa viñetas, resalta verbos de acción y elimina distractores.",
        "TEA": "Usa lenguaje literal, instrucciones paso a paso y evita metáforas o lenguaje ambiguo.",
        "Trastorno del Lenguaje": "Usa vocabulario simple, frases cortas y estructuras gramaticales sencillas."
    }
    
    # --- AQUÍ ESTÁ TU SÚPER PROMPT ---
    prompt = f"""
    Actúa como una Educadora Diferencial altamente capacitada, con más de 20 años de experiencia trabajando en el Programa de Integración Escolar (PIE) en Chile.
    
    Tu tarea es ejecutar una adecuación curricular de la siguiente prueba de {asignatura} para un estudiante de {curso}. 
    El estudiante presenta la siguiente condición: {necesidad}.
    
    Basado en tu vasta experiencia, debes aplicar rigurosamente estos criterios técnicos en tu adaptación: {instrucciones[necesidad]}.
    
    Toma el texto original de la prueba y reescríbelo completo. Adapta el formato, las instrucciones y la complejidad del lenguaje para que el estudiante pueda rendirla de forma autónoma con éxito, pero manteniendo intacto el Objetivo de Aprendizaje (OA). 
    Entrega solamente la prueba lista para imprimir, sin saludos ni explicaciones extra.
    
    TEXTO ORIGINAL DE LA PRUEBA:
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
                with st.spinner("La educadora virtual está analizando y adaptando la prueba..."):
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
