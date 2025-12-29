import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from database.connection import get_db_session
from database.models import Invoice, InvoiceItem
from sqlalchemy.orm import joinedload

def load_data():
    """
    Carga facturas e ítems de la BD filtrando por el USUARIO ACTUAL.
    """
    db = get_db_session()
    try:
        
        current_user_id = st.session_state.user.id
        
        
        invoices = db.query(Invoice)\
            .filter(Invoice.user_id == current_user_id)\
            .options(joinedload(Invoice.items))\
            .all()
        
        if not invoices:
            return pd.DataFrame(), pd.DataFrame()

        
        data_invoices = []
        for inv in invoices:
            data_invoices.append({
                "id": inv.id,
                "vendor": inv.vendor,
                "date": inv.date,
                "total": inv.total_amount,
                "currency": inv.currency
            })
        df_invoices = pd.DataFrame(data_invoices)
        df_invoices['date'] = pd.to_datetime(df_invoices['date'], errors='coerce')

        
        data_items = []
        for inv in invoices:
            for item in inv.items:
                data_items.append({
                    "date": pd.to_datetime(inv.date, errors='coerce'), 
                    "vendor": inv.vendor,
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_line": item.total_price
                })
        df_items = pd.DataFrame(data_items)

        return df_invoices, df_items
    finally:
        db.close()

def render_dashboard_view():
    st.title("📊 Control de Costes y Compras")

    df_invoices, df_items = load_data()

    if df_invoices.empty:
        st.info("👋 ¡Hola! Aún no tienes datos. Ve a 'Subir Facturas' para empezar.")
        return

    
    st.sidebar.header("📅 Filtros de Tiempo")
    
    filtro_tiempo = st.sidebar.radio(
        "Periodo:",
        ["Este Mes", "Mes Pasado", "Últimos 90 Días", "Este Año", "Personalizado"]
    )

    hoy = datetime.now()
    fecha_inicio = None
    fecha_fin = hoy

    
    if filtro_tiempo == "Este Mes":
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy
        
    elif filtro_tiempo == "Mes Pasado":
        
        primero_este_mes = hoy.replace(day=1)
        
        ultimo_mes_pasado = primero_este_mes - timedelta(days=1)
        
        primero_mes_pasado = ultimo_mes_pasado.replace(day=1)
        
        fecha_inicio = primero_mes_pasado
        fecha_fin = ultimo_mes_pasado

    elif filtro_tiempo == "Últimos 90 Días":
        fecha_inicio = hoy - timedelta(days=90)
        fecha_fin = hoy

    elif filtro_tiempo == "Este Año":
        fecha_inicio = hoy.replace(month=1, day=1)
        fecha_fin = hoy

    elif filtro_tiempo == "Personalizado":
        c1, c2 = st.sidebar.columns(2)
        
        d_start = c1.date_input("Desde", hoy - timedelta(days=30))
        d_end = c2.date_input("Hasta", hoy)
        
        fecha_inicio = pd.to_datetime(d_start)
        
        fecha_fin = pd.to_datetime(d_end) + timedelta(hours=23, minutes=59, seconds=59)

    
    
    fecha_inicio = pd.to_datetime(fecha_inicio)
    fecha_fin = pd.to_datetime(fecha_fin)

    st.sidebar.markdown(f"---")
    st.sidebar.caption(f"Mostrando datos del:\n{fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}")

    
    mask_inv = (df_invoices['date'] >= fecha_inicio) & (df_invoices['date'] <= fecha_fin)
    df_inv_filtered = df_invoices.loc[mask_inv]
    
    mask_items = (df_items['date'] >= fecha_inicio) & (df_items['date'] <= fecha_fin)
    df_items_filtered = df_items.loc[mask_items]

    
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    
    gasto_total = df_inv_filtered['total'].sum()
    num_facturas = len(df_inv_filtered)
    proveedores_unicos = df_inv_filtered['vendor'].nunique()
    
    col1.metric("Gasto Total", f"{gasto_total:,.2f}€")
    col2.metric("Facturas", num_facturas)
    col3.metric("Proveedores", proveedores_unicos)
    
    top_prod = "N/A"
    if not df_items_filtered.empty:
        top_prod = df_items_filtered['description'].mode()[0]
    col4.metric("Prod. Frecuente", top_prod)

    
    st.subheader("🥩 Análisis de Ingredientes")
    
    if not df_items_filtered.empty:
        
        product_stats = df_items_filtered.groupby('description').agg({
            'total_line': 'sum',      
            'quantity': 'sum',        
            'unit_price': 'mean',     
            'vendor': lambda x: x.mode()[0] if not x.mode().empty else "Varios"
        }).reset_index()

        product_stats.columns = ['Producto', 'Gasto Total (€)', 'Cantidad Total', 'Precio Medio (€)', 'Proveedor']
        product_stats = product_stats.sort_values('Gasto Total (€)', ascending=False)

        
        tab_gasto, tab_volumen = st.tabs(["💰 Top Gasto", "📦 Top Volumen (Kg/Ud)"])
        
        with tab_gasto:
            st.caption("¿En qué se va el dinero?")
            chart_gasto = alt.Chart(product_stats.head(10)).mark_bar().encode(
                x=alt.X('Gasto Total (€)', title='Euros Gastados'),
                y=alt.Y('Producto', sort='-x'),
                color=alt.Color('Gasto Total (€)', scale=alt.Scale(scheme='orangered')),
                tooltip=['Producto', 'Gasto Total (€)', 'Proveedor']
            ).properties(height=350)
            st.altair_chart(chart_gasto, use_container_width=True)

        with tab_volumen:
            st.caption("¿Qué compramos en mayor cantidad?")
            stats_qty = product_stats.sort_values('Cantidad Total', ascending=False).head(10)
            chart_qty = alt.Chart(stats_qty).mark_bar().encode(
                x=alt.X('Cantidad Total', title='Unidades / Kg'),
                y=alt.Y('Producto', sort='-x'),
                color=alt.Color('Cantidad Total', scale=alt.Scale(scheme='blues')),
                tooltip=['Producto', 'Cantidad Total', 'Proveedor']
            ).properties(height=350)
            st.altair_chart(chart_qty, use_container_width=True)

        
        st.write("#### 📋 Detalle de Compras")
        st.dataframe(
            product_stats,
            column_config={
                "Gasto Total (€)": st.column_config.ProgressColumn(
                    "Gasto Total",
                    format="%.2f €",
                    min_value=0,
                    max_value=product_stats['Gasto Total (€)'].max(),
                ),
                "Cantidad Total": st.column_config.NumberColumn("Cantidad", format="%.1f"),
                "Precio Medio (€)": st.column_config.NumberColumn("Precio Medio", format="%.2f €"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.warning("No hay datos de productos en este periodo.")

    st.divider()

    
    st.subheader("📈 Detector de Inflación")
    st.caption("Selecciona un ingrediente para ver cómo ha cambiado su precio unitario.")
    
    
    todos_items = sorted(df_items['description'].unique()) if not df_items.empty else []
    
    col_sel, col_graph = st.columns([1, 2])
    with col_sel:
        item_seleccionado = st.selectbox("Buscar Ingrediente:", todos_items)

    if item_seleccionado:
    
        historial = df_items[df_items['description'] == item_seleccionado].sort_values('date')
        
        if not historial.empty:
            chart_line = alt.Chart(historial).mark_line(point=True).encode(
                x=alt.X('date:T', title='Fecha'),
                y=alt.Y('unit_price', title='Precio Unitario (€)'),
                tooltip=['date', 'unit_price', 'vendor', 'quantity']
            ).interactive()
            st.altair_chart(chart_line, use_container_width=True)
            
            
            precio_min = historial['unit_price'].min()
            precio_max = historial['unit_price'].max()
            st.info(f"Rango de precio histórico: **{precio_min:.2f}€** - **{precio_max:.2f}€**")
        else:
            st.write("Sin historial suficiente.")