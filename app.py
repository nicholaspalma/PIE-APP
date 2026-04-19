import streamlit as st
import docx
import google.generativeai as genai
from io import BytesIO

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Adecuaciones PACI", page_icon="📘", layout="centered")

# --- FUNCIONES DE PROCESAMIENTO DE WORD ---
def leer_docx(archivo):
    """Extrae el texto manteniendo la separación de párrafos del Word original."""
    doc = docx.Document(archivo)
    texto_completo = []
    for parrafo in doc.paragraphs:
        if parrafo.text.strip(): # Solo lee párrafos que tengan texto
            texto_completo.append(parrafo.text)
    return "\n".join(texto_completo)

def crear_docx_adaptado(texto_adaptado):
    """Crea un nuevo documento Word en la memoria con el texto adaptado."""
    doc = docx.Document()
    
    # Separamos el texto de la IA por saltos de línea y lo agregamos al Word
    for linea in texto_adaptado.split('\n'):
        if linea.strip():
            doc.add_paragraph(linea.replace('**', '')) # Limpiamos posibles negritas de Markdown
            
    # Guardamos en memoria (BytesIO) para no ocupar espacio en el disco del servidor
    archivo_memoria = BytesIO()
    doc.save(archivo_memoria)
    archivo_memoria.seek(0)
    return archivo_memoria

# --- FUNCIÓN DE INTELIGENCIA ARTIFICIAL ---
def adaptar_prueba_con_ia(texto_original, curso, asignatura, necesidad, api_key):
    """Envía la prueba a la IA con las instrucciones pedagógicas específicas."""
    genai.configure(api_key=api_key)
    
    # Usamos el modelo optimizado para texto
    modelo = genai.GenerativeModel('gemini-pro')
    
    # Instrucciones pedagógicas dinámicas según la necesidad
    instrucciones_paci = {
        "TDAH": "Acorta las oraciones, usa viñetas para separar ideas, resalta (escribe en mayúsculas) los verbos de acción en las instrucciones (ej: SUBRAYA, MARCA, EXPLICA) y divide preguntas complejas en pasos A y B.",
        "TEA": "Usa lenguaje extremadamente literal y directo. Elimina metáforas, dobles negaciones y ambigüedades. Estructura la prueba de forma altamente predecible y clara.",
        "Trastorno del Lenguaje": "Simplifica el vocabulario complejo por sinónimos de uso frecuente. Acorta la longitud de los párrafos de lectura, manteniendo la idea principal y el objetivo de aprendizaje."
    }
    
    prompt = f"""
    Eres un experto en Educación Especial y Adecuaciones Curriculares (PACI).
    Tu tarea es adaptar la siguiente prueba de {asignatura} para un alumno de {curso} que presenta {necesidad}.
    
    REGLA DE FORMATO ESTRICTA: Debes mantener la estructura original de la prueba (Ítems, números de pregunta, alternativas A,B,C,D). NO resuelvas la prueba, solo adapta las preguntas y los textos.
    
    REGLA PEDAGÓGICA PARA {necesidad.upper()}: {instrucciones_paci[necesidad]}
    
    --- PRUEBA ORIGINAL ---
    {texto_original}
    --- FIN DE LA PRUEBA ORIGINAL ---
    
    Escribe a continuación la prueba adaptada respetando el formato original:
    """
    
    respuesta = modelo.generate_content(prompt)
    return respuesta.text

# --- INTERFAZ DE USUARIO (STREAMLIT) ---
st.title("📘 Generador de Pruebas Adaptadas (PACI)")
st.markdown("Sube la prueba original en Word, selecciona los parámetros y la IA generará el documento adaptado listo para imprimir.")

# Barra lateral para configuraciones y API Key
with st.sidebar:
    st.header("⚙️ Configuración")
    st.info("Necesitas una clave API gratuita de Google Gemini para usar el motor de IA.")
    api_key_usuario = st.text_input("Ingresa tu API Key de Gemini:", type="password")
    
    st.divider()
    st.header("📚 Parámetros")
    curso_sel = st.selectbox("Curso:", ["1ro Básico", "2do Básico", "3ro Básico", "4to Básico", "5to Básico", "6to Básico", "7mo Básico", "8vo Básico", "1ro Medio", "2do Medio", "3ro Medio", "4to Medio"])
    asignatura_sel = st.selectbox("Asignatura:", ["Lenguaje", "Matemáticas", "Historia", "Ciencias Naturales", "Inglés", "Otra"])
    necesidad_sel = st.selectbox("Necesidad Educativa:", ["TDAH", "TEA", "Trastorno del Lenguaje"])

# Área principal para subir el archivo
archivo_subido = st.file_uploader("Sube la prueba original aquí (formato .docx)", type=["docx"])

if archivo_subido is not None:
    st.success("Archivo Word cargado correctamente.")
    
    if st.button("🚀 Generar Adecuación PACI", use_container_width=True):
        if not api_key_usuario:
            st.error("Por favor, ingresa tu API Key en el menú de la izquierda para poder procesar la prueba.")
        else:
            with st.spinner(f"Analizando y adaptando prueba para {necesidad_sel}... Esto puede tardar unos segundos."):
                try:
                    # 1. Leer el Word original
                    texto_prueba = leer_docx(archivo_subido)
                    
                    # 2. Enviar a la IA para adaptar
                    texto_adecuado = adaptar_prueba_con_ia(texto_prueba, curso_sel, asignatura_sel, necesidad_sel, api_key_usuario)
                    
                    # 3. Crear el nuevo Word
                    nuevo_word = crear_docx_adaptado(texto_adecuado)
                    
                    st.success("¡Prueba adaptada con éxito!")
                    
                    # 4. Botón de descarga
                    st.download_button(
                        label="⬇️ Descargar Prueba Adaptada (.docx)",
                        data=nuevo_word,
                        file_name=f"Prueba_{asignatura_sel}_{necesidad_sel}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Hubo un error al procesar el archivo. Revisa tu API Key o el formato de tu Word. Detalle técnico: {e}")
