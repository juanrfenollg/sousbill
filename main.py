import streamlit as st
from PIL import Image

from database.connection import init_db
from views.upload_invoice import render_upload_view
from views.dashboard import render_dashboard_view
from views.history import render_history_view
from views.login import render_login_view
from services.auth import sign_out


try:
    icon_img = Image.open("assets/logo_sousbill.png")
except Exception:
    icon_img = "👨‍🍳"

st.set_page_config(
    page_title="SousBill | Tu Segundo de Cocina Financiero",
    page_icon=icon_img,
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
    /* IMPORTAR FUENTE INTER */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* APLICAR FUENTE SOLO A TEXTOS, NO A ICONOS */
    html, body, p, h1, h2, h3, h4, h5, h6, span, div, label, button, input, textarea {
        font-family: 'Inter', sans-serif;
    }

    /* LIMPIEZA VISUAL */
    #MainMenu {visibility: hidden;}
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}

    /* --- TARJETAS DE MÉTRICAS (KPIs) --- */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease-in-out;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border-color: #E85D04;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.95rem !important;
        color: #64748B !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        color: #0F172A !important;
        font-weight: 700 !important;
    }

    /* --- BOTONES --- */
    /* Apuntamos específicamente al botón interior para no romper el contenedor */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.2s ease !important;
        /* No forzamos font-family aquí para respetar iconos dentro de botones si los hubiera */
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(232, 93, 4, 0.3) !important;
    }

    /* --- BARRA LATERAL --- */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0;
    }

    /* --- PESTAÑAS (TABS) --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #FFFFFF;
        border-radius: 8px 8px 0 0;
        color: #64748B;
        border: 1px solid #E2E8F0;
        border-bottom: none;
        padding: 0 24px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #E85D04 !important;
        border-top: 2px solid #E85D04 !important;
        border-right: 1px solid #E2E8F0 !important;
        border-left: 1px solid #E2E8F0 !important;
        font-weight: 700 !important;
    }
    
    /* --- TOAST --- */
    [data-testid="stToast"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #E2E8F0;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)


init_db()


if "user" not in st.session_state:
    render_login_view()
    st.stop()

user_email = st.session_state.user.email


with st.sidebar:
    try:
        st.image("assets/logo_sousbill.png", width=140)
    except Exception:
        st.header("👨‍🍳 SousBill")
    
    st.write("")
    
    st.caption(f"Hola, **{user_email.split('@')[0]}**")

    opcion = st.radio(
        "Navegación", 
        ["Dashboard", "Subir Facturas", "Historial"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    if st.button("🚪 Cerrar Sesión", type="primary", use_container_width=True):
        try:
            sign_out()
        except Exception:
            pass
        del st.session_state.user
        st.rerun()

if opcion == "Subir Facturas":
    render_upload_view()

elif opcion == "Dashboard":
    render_dashboard_view()

elif opcion == "Historial":
    render_history_view()