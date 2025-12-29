import streamlit as st
import pandas as pd
from datetime import datetime
from services.gemini import analyze_invoice
from database.connection import get_db_session
from database.models import Invoice, InvoiceItem

def render_upload_view():
    st.header("📤 Subir Facturas")
    
    # 1. Pestañas de selección
    tab1, tab2 = st.tabs(["📁 Subir Archivo", "📸 Usar Cámara"])
    
    uploaded_file = None
    
    with tab1:
        # Aceptamos PDF además de imágenes
        file = st.file_uploader("Arrastra tu factura", type=["jpg", "png", "jpeg", "pdf"])
        if file:
            uploaded_file = file
            
    with tab2:
        camera = st.camera_input("Haz una foto a la factura")
        if camera:
            uploaded_file = camera

    # 2. Lógica de Previsualización y Análisis
    if uploaded_file:
        st.divider()
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Vista Previa")
            # Si es PDF mostramos aviso, si es imagen la mostramos
            if uploaded_file.type == "application/pdf":
                st.info("📄 Documento PDF cargado correctamente.")
            else:
                st.image(uploaded_file, use_container_width=True)

        with col2:
            st.subheader("Análisis IA")
            
            # Botón para iniciar el análisis
            if st.button("✨ Analizar con Gemini", type="primary"):
                with st.spinner("🤖 Leyendo factura (esto puede tardar unos segundos)..."):
                    
                    # --- AQUÍ ESTABA EL ERROR ANTES ---
                    # Ahora pasamos 'uploaded_file' DIRECTAMENTE a la función
                    # No guardamos nada en disco.
                    datos = analyze_invoice(uploaded_file)
                    
                    if datos is None:
                        st.error("Error desconocido: La IA no devolvió nada.")
                    elif "error" in datos:
                        st.error(datos['error'])
                    else:
                        # Si todo sale bien, guardamos los datos en la "memoria" de la app
                        st.session_state['current_invoice'] = datos
                        st.toast("¡Factura leída con éxito!", icon="🎉")

    # 3. Formulario de Revisión y Guardado
    # Solo mostramos esto si ya tenemos datos analizados en memoria
    if 'current_invoice' in st.session_state:
        data = st.session_state['current_invoice']
        
        st.divider()
        st.subheader("📝 Revisar y Guardar")
        
        with st.form("save_invoice_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                vendor = st.text_input("Proveedor", value=data.get("vendor", ""))
                date_str = st.text_input("Fecha (YYYY-MM-DD)", value=data.get("date", datetime.now().strftime("%Y-%m-%d")))
            with col_b:
                total = st.number_input("Total (€)", value=float(data.get("total_amount", 0.0)))
                currency = st.text_input("Moneda", value=data.get("currency", "EUR"))
            
            st.write("Productos detectados:")
            # Convertimos los items a DataFrame para poder editarlos si queremos
            items_df = pd.DataFrame(data.get("items", []))
            
            # Usamos data_editor para permitir correcciones manuales rápidas
            edited_items = st.data_editor(items_df, num_rows="dynamic", use_container_width=True)
            
            submitted = st.form_submit_button("💾 Guardar en Base de Datos", type="primary")
            
            if submitted:
                try:
                    # Conexión a Base de Datos
                    session = get_db_session()
                    
                    # 1. Crear la Factura
                    new_invoice = Invoice(
                        vendor=vendor,  # <--- ¡AQUÍ ESTABA EL ERROR! (Antes ponía vendor_name)
                        date=datetime.strptime(date_str, "%Y-%m-%d").date(),
                        total_amount=total,
                        currency=currency
                    )
                    session.add(new_invoice)
                    session.flush() # Esto nos da el ID de la factura antes de cerrar
                    
                    # 2. Crear los Ítems
                    # Leemos del editor (edited_items es un DataFrame)
                    for index, row in edited_items.iterrows():
                        item = InvoiceItem(
                            invoice_id=new_invoice.id,
                            description=row.get("description", "Item"),
                            quantity=float(row.get("quantity", 1)),
                            unit_price=float(row.get("unit_price", 0)),
                            total_line=float(row.get("total", 0))
                        )
                        session.add(item)
                    
                    session.commit()
                    st.success(f"✅ Factura de {vendor} guardada correctamente.")
                    
                    # Limpiamos la memoria para la siguiente factura
                    del st.session_state['current_invoice']
                    session.close()
                    
                except Exception as e:
                    st.error(f"Error guardando en base de datos: {e}")