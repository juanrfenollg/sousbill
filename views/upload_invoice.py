import streamlit as st
import os
import base64
from PIL import Image
import pandas as pd
from services.gemini import analyze_invoice
from database.connection import get_db_session 
from database.models import Invoice, InvoiceItem
from services.notifications import obtener_precio_anterior, enviar_alerta_correo


def mostrar_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def render_upload_view(): 
    st.header("📤 Subir Nueva Factura")
    

    if "img_rotation" not in st.session_state:
        st.session_state.img_rotation = 0

    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    tab_upload, tab_camera = st.tabs(["📁 Subir Archivo", "📸 Usar Cámara"])
    
    image_source = None


    with tab_upload:
        uploaded_file = st.file_uploader(
            "Arrastra tu factura (PDF o Imagen)...", 
            type=["jpg", "png", "jpeg", "pdf"], 
            key=f"uploader_{st.session_state.uploader_key}" 
        )
        if uploaded_file:
            image_source = uploaded_file


    with tab_camera:
        camera_photo = st.camera_input(
            "Toma la foto", 
            key=f"camera_{st.session_state.uploader_key}"
        )
        if camera_photo:
            image_source = camera_photo


    if image_source is not None:
        os.makedirs("temp_uploads", exist_ok=True)
        filename = image_source.name if hasattr(image_source, 'name') else "camera_capture.jpg"
        file_path = os.path.join("temp_uploads", filename)
        
        with open(file_path, "wb") as f:
            f.write(image_source.getbuffer())

        col1, col2 = st.columns([1.2, 1]) 
        
        with col1:
            st.subheader("👁️ Vista Previa")
            
            if filename.lower().endswith(".pdf"):
                mostrar_pdf(file_path)
                st.session_state.img_rotation = 0
            else:
                c_rot1, c_rot2, c_rot3 = st.columns([1, 1, 3])
                if c_rot1.button("↺"):
                    st.session_state.img_rotation += 90
                if c_rot2.button("↻"):
                    st.session_state.img_rotation -= 90
                
                try:
                    image = Image.open(file_path)
                    rotated_image = image.rotate(st.session_state.img_rotation, expand=True)
                    st.image(rotated_image, use_container_width=True)
                    if st.session_state.img_rotation % 360 != 0:
                        rotated_image.save(file_path)
                        
                except Exception as e:
                    st.error(f"Error imagen: {e}")
        with col2:
            st.subheader("🧠 Análisis")
            if "invoice_data" not in st.session_state:
                st.session_state.invoice_data = {}
            if st.button("🚀 Analizar Factura", type="primary", use_container_width=True):
                with st.spinner("Leyendo documento..."):
                    datos = analyze_invoice(file_path)
                    
                    if "error" in datos:
                        st.error(datos['error'])
                    else:
                        st.toast("¡Datos extraídos!", icon="✨")
                        st.session_state.invoice_data = datos 
            if st.session_state.invoice_data:
                st.divider()
                datos = st.session_state.invoice_data
                
                with st.form("edit_form"):
                    st.caption("Verifica y guarda:")
                    c_a, c_b = st.columns(2)
                    
                    vendor = c_a.text_input("Proveedor", value=datos.get('vendor') or "")
                    date = c_b.text_input("Fecha (YYYY-MM-DD)", value=datos.get('date') or "")
                    total = c_a.number_input("Total", value=float(datos.get('total_amount') or 0.0), format="%.2f")
                    currency = c_b.text_input("Moneda", value=datos.get('currency') or "EUR")
                    
                    st.subheader("Ítems")
                    items_df = pd.DataFrame(datos.get('items', []))
                    
                    column_config = {
                        "description": st.column_config.TextColumn("Descripción", required=True),
                        "quantity": st.column_config.NumberColumn("Cant.", min_value=0, format="%.1f"),
                        "unit_price": st.column_config.NumberColumn("Precio", min_value=0, format="%.2f"),
                        "total_price": st.column_config.NumberColumn("Total", disabled=True)
                    }
                    edited_items = st.data_editor(items_df, num_rows="dynamic", column_config=column_config, use_container_width=True)
                    
                    guardar = st.form_submit_button("💾 Guardar Factura", type="primary", use_container_width=True)
                    
                    if guardar:
                        try:
                            db = get_db_session()
                            current_user_id = st.session_state.user.id
                            user_email = st.session_state.user.email
                            alertas_precio = []

                            nuevo_inv = Invoice(
                                user_id=current_user_id,
                                vendor=vendor, 
                                date=date, 
                                total_amount=total, 
                                currency=currency, 
                                image_url=file_path 
                            )
                            db.add(nuevo_inv)
                            db.commit() 
                            db.refresh(nuevo_inv) 
                            
                            
                            for index, row in edited_items.iterrows():
                                if row.get('description'): 
                                    qty = float(row.get('quantity') or 1)
                                    price = float(row.get('unit_price') or 0)
                                    desc_prod = row.get('description')
                                    
                                    
                                    precio_anterior = obtener_precio_anterior(db, current_user_id, desc_prod, date)
                                    if precio_anterior and price > precio_anterior:
                                        alertas_precio.append({
                                            "producto": desc_prod,
                                            "anterior": precio_anterior,
                                            "nuevo": price
                                        })

                                    item = InvoiceItem(
                                        invoice_id=nuevo_inv.id,
                                        description=desc_prod,
                                        quantity=qty,
                                        unit_price=price,
                                        total_price=qty * price
                                    )
                                    db.add(item)
                            
                            db.commit()

                            
                            if alertas_precio:
                                with st.spinner("📧 Enviando alerta de precios..."):
                                    enviar_alerta_correo(user_email, alertas_precio)

                            st.balloons()
                            st.toast("¡Factura guardada! Listo para la siguiente.", icon="✅")
                            
                            
                            st.session_state.invoice_data = {}
                            st.session_state.img_rotation = 0
                            
                            
                            st.session_state.uploader_key += 1 
                            
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error guardando: {e}")
                            db.rollback()
                        finally:
                            db.close()