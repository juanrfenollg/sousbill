import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def analizar_factura_con_gemini(image_path):
    """
    Envía la imagen a Gemini Flash y retorna un diccionario JSON.
    """
    try:
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        
        sample_file = genai.upload_file(path=image_path, display_name="Factura Temp")

        prompt = """
        Actúa como un sistema experto de OCR para contabilidad.
        Analiza esta imagen y extrae los datos en formato JSON puro.
        
        Campos requeridos:
        - vendor (nombre del proveedor)
        - date (fecha en formato YYYY-MM-DD, si no hay año asume el actual)
        - total_amount (número flotante)
        - currency (simbolo o codigo, ej: USD, EUR)
        - items: Lista de objetos con {description, quantity, unit_price}
        
        Si un campo no es visible, usa null. No uses bloques de código markdown, solo el JSON raw.
        """

        response = model.generate_content([sample_file, prompt])
        
        
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        
        return json.loads(clean_text)
        
    except Exception as e:
        return {"error": str(e)}