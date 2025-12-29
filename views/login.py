import streamlit as st
import time
from services.auth import sign_in, sign_up

def render_login_view():

    col1, col2, col3 = st.columns([1, 2, 1])

    
    with col2:
        
        with st.container(border=True):
            st.header("🔐 Acceso Seguro")
            st.markdown("---") 

            tab_login, tab_signup = st.tabs(["Iniciar Sesión", "Registrarse"])

        
            with tab_login:
                st.write("") 
                with st.form("login_form"):
                    email = st.text_input("Email", placeholder="tu@email.com")
                    password = st.text_input("Contraseña", type="password")
                    
                    st.write("") 
                    submit = st.form_submit_button("Entrar", type="primary", use_container_width=True)

                    if submit:
                        if not email or not password:
                            st.warning("Por favor, llena todos los campos.")
                        else:
                            user = sign_in(email, password)
                            if user:
                                st.success("¡Bienvenido!")
                                st.session_state.user = user
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Email o contraseña incorrectos.")

        
            with tab_signup:
                st.write("")
                st.caption("Crea una cuenta para guardar tus facturas.")
                with st.form("signup_form"):
                    new_email = st.text_input("Email")
                    new_password = st.text_input("Contraseña (min 6 caracteres)", type="password")
                    confirm_password = st.text_input("Confirmar Contraseña", type="password")
                    
                    st.write("")
                    submit_reg = st.form_submit_button("Crear Cuenta", use_container_width=True)

                    if submit_reg:
                        if new_password != confirm_password:
                            st.error("Las contraseñas no coinciden.")
                        elif len(new_password) < 6:
                            st.error("La contraseña es muy corta.")
                        else:
                            user = sign_up(new_email, new_password)
                            if user:
                                st.success("¡Cuenta creada! Revisa tu email.")
                            else:
                                st.error("Error al crear cuenta. Puede que ya exista.")