# 👨‍🍳 SousBill

**SousBill** es el "Segundo de Cocina Financiero" para restaurantes modernos. Una aplicación inteligente que digitaliza facturas, controla costes y detecta inflación en los ingredientes utilizando Inteligencia Artificial.

## 🚀 Funcionalidades

- **Escaneo con IA:** Extrae datos de fotos o PDFs de facturas automáticamente (Google Gemini).
- **Dashboard en Tiempo Real:** Control de gasto total, proveedores y categorías.
- **Detector de Inflación:** Alerta vía email si un ingrediente sube de precio respecto a la última compra.
- **Historial:** Gestión completa de registros pasados.

## 🛠️ Tecnologías

- **Frontend:** Streamlit
- **Backend:** Python
- **Base de Datos:** PostgreSQL (Supabase)
- **IA:** Google Gemini Pro Vision
- **Notificaciones:** Resend API

## 📦 Instalación Local

1. Clonar el repositorio.
2. Crear un entorno virtual: `python -m venv venv`
3. Instalar dependencias: `pip install -r requirements.txt`
4. Configurar el archivo `.env` con tus claves API.
5. Ejecutar: `streamlit run app.py`