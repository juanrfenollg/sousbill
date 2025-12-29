import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# Cargar variables de entorno (.env)
load_dotenv()

# Configurar la API Key de Google
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def analyze_invoice(uploaded_file):
    """
    Toma un archivo subido por Streamlit (Imagen o PDF) y lo envía a Gemini Flash.
    Retorna un diccionario (JSON) con los datos extraídos.
    """
    # Usamos 'gemini-1.5-flash' porque es rápido y soporta documentos PDF nativamente
    model = genai.GenerativeModel('gemini-1.5-flash')

    # 1. PREPARAR LOS DATOS DEL ARCHIVO
    # Extraemos los bytes y el tipo de archivo (ej: 'application/pdf' o 'image/jpeg')
    try:
        bytes_data = uploaded_file.getvalue()
        mime_type = uploaded_file.type
    except Exception as e:
        print(f"Error leyendo el archivo: {e}")
        return None

    # 2. DEFINIR EL PROMPT (Instrucciones para la IA)
    prompt = """
    Actúa como un sistema experto de extracción de datos para contabilidad de restaurantes.
    Analiza el documento adjunto (puede ser una imagen o un PDF de varias páginas).
    
    Extrae la siguiente información y devuélvela EXCLUSIVAMENTE en formato JSON:
    
    1. "vendor": Nombre del proveedor o supermercado.
    2. "date": Fecha de la factura en formato YYYY-MM-DD. Si no hay año, asume el actual.
    3. "currency": Moneda (EUR, USD, etc.).
    4. "total_amount": El importe total final de la factura (número decimal).
    5. "items": Una lista de los productos comprados. Para cada producto extrae:
    - "description": Nombre del producto.
    - "quantity": Cantidad (número). Si no se especifica, pon 1.
    - "unit_price": Precio unitario (número).
    - "total": Precio total de la línea (número).

    IMPORTANTE:
    - Si el documento tiene varias páginas, suma o lista todos los ítems de todas las páginas.
    - No incluyas texto extra, ni markdown (```json), solo el JSON crudo.
    - Si algún campo numérico no está claro, usa 0.0.
    """

    # 3. EMPAQUETAR DATOS PARA GEMINI
    # Creamos un objeto con los datos crudos y su tipo
    document_blob = {
        "mime_type": mime_type,
        "data": bytes_data
    }

    try:
        # 4. LLAMADA A LA IA
        # Le enviamos las instrucciones (prompt) + el documento (blob)
        response = model.generate_content([prompt, document_blob])
        
        # 5. LIMPIEZA Y PARSEO DE LA RESPUESTA
        # A veces la IA devuelve bloques de código markdown, los limpiamos
        text_response = response.text.replace("```json", "").replace("```", "").strip()
        
        # Convertimos el texto a un Diccionario de Python real
        invoice_data = json.loads(text_response)
        return invoice_data

    except Exception as e:
        print(f"Error procesando con Gemini: {e}")
        return None