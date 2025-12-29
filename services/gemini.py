import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Intentamos configurar la API. Si falla aquí, lo capturaremos en la función.
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
except Exception as e:
    print(f"Error configurando API Key: {e}")

def analyze_invoice(uploaded_file):
    """
    Analiza facturas (PDF o Imagen) con Gemini Flash.
    Devuelve un diccionario con los datos o un diccionario con la clave 'error'.
    """
    # Verificación 1: ¿Tenemos API Key?
    if not os.getenv("GOOGLE_API_KEY"):
        return {"error": "Falta la GOOGLE_API_KEY en los Secrets (.env)."}

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Verificación 2: ¿El archivo es válido?
        if uploaded_file is None:
            return {"error": "No se ha recibido ningún archivo."}

        # 1. PREPARAR DATOS
        try:
            bytes_data = uploaded_file.getvalue()
            mime_type = uploaded_file.type
        except Exception as e:
            return {"error": f"Error leyendo el archivo: {str(e)}"}

        # 2. PROMPT
        prompt = """
        Actúa como experto contable. Analiza este documento (imagen o PDF).
        Extrae y devuelve SOLO un JSON con:
        {
            "vendor": "Nombre proveedor",
            "date": "YYYY-MM-DD",
            "currency": "EUR",
            "total_amount": 0.00,
            "items": [{"description": "Item", "quantity": 1, "unit_price": 0.0, "total": 0.0}]
        }
        Si no encuentras datos, usa 0 o vacíos. No uses markdown.
        """

        document_blob = {"mime_type": mime_type, "data": bytes_data}

        # 3. LLAMADA A LA IA
        response = model.generate_content([prompt, document_blob])
        
        # 4. LIMPIEZA
        text_response = response.text.replace("```json", "").replace("```", "").strip()
        
        return json.loads(text_response)

    except Exception as e:
        # AQUÍ ESTÁ LA SOLUCIÓN:
        # En lugar de devolver None, devolvemos el error exacto para verlo en pantalla
        return {"error": f"Error de IA: {str(e)}"}