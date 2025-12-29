import streamlit as st
import pandas as pd
from database.connection import get_db_session
from database.models import Invoice, InvoiceItem

def render_history_view():
    st.header("🗂️ Historial y Gestión de Facturas")

    
    db = get_db_session()
    user_id = st.session_state.user.id
    
    try:
        
        invoices = db.query(Invoice).filter(Invoice.user_id == user_id).order_by(Invoice.date.desc()).all()

        if not invoices:
            st.info("No tienes facturas guardadas todavía.")
            return

        
        data = []
        for inv in invoices:
            data.append({
                "ID": inv.id,
                "Fecha": inv.date,
                "Proveedor": inv.vendor,
                "Total": f"{inv.total_amount:.2f} {inv.currency}"
            })
        
        df = pd.DataFrame(data)
        
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.divider()

        
        st.subheader("✏️ Editar o Eliminar")
        
        
        opciones = [f"{inv.id} - {inv.vendor} ({inv.total_amount})" for inv in invoices]
        seleccion = st.selectbox("Selecciona la factura a gestionar:", opciones)
        
        
        selected_id = int(seleccion.split(" - ")[0])
        
        
        invoice_to_edit = db.query(Invoice).get(selected_id)

        if invoice_to_edit:
            
            with st.expander("📝 Modificar Datos", expanded=True):
                with st.form("update_form"):
                    col1, col2 = st.columns(2)
                    new_vendor = col1.text_input("Proveedor", value=invoice_to_edit.vendor)
                    new_date = col2.text_input("Fecha (YYYY-MM-DD)", value=invoice_to_edit.date)
                    
                    c3, c4 = st.columns(2)
                    new_total = c3.number_input("Total", value=float(invoice_to_edit.total_amount))
                    new_currency = c4.text_input("Moneda", value=invoice_to_edit.currency)

                    submitted = st.form_submit_button("💾 Guardar Cambios")
                    
                    if submitted:
                        invoice_to_edit.vendor = new_vendor
                        invoice_to_edit.date = new_date
                        invoice_to_edit.total_amount = new_total
                        invoice_to_edit.currency = new_currency
                        
                        db.commit()
                        st.success("¡Factura actualizada correctamente!")
                        st.rerun()

            
            st.write("")
            st.warning("⚠️ Zona de Peligro")
            
            col_del1, col_del2 = st.columns([4, 1])
            with col_del1:
                st.caption("Esta acción eliminará la factura y todos sus productos asociados. No se puede deshacer.")
            
            with col_del2:
                
                if st.button("🗑️ Eliminar", type="primary"):
                    db.delete(invoice_to_edit) 
                    db.commit()
                    st.toast("Factura eliminada", icon="🗑️")
                    st.rerun()
                    
    except Exception as e:
        st.error(f"Error cargando historial: {e}")
    finally:
        db.close()