import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, time, timedelta
from database.connection import get_db_session
from database.models import Invoice, InvoiceItem
from sqlalchemy.orm import joinedload

def load_data():
    """
    Carga facturas e ítems de la BD filtrando por el USUARIO ACTUAL.
    """
    db = get_db_session()
    try:
        # Verificamos que el usuario esté en sesión para evitar crash
        if 'user' not in st.session_state:
            return pd.DataFrame(), pd.DataFrame()

        current_user_id = st.session_state.user.id
        
        # Usamos joinedload para traer los items en la misma consulta (Eficiencia)
        invoices = db.query(Invoice)\
            .filter(Invoice.user_id == current_user_id)\
            .options(joinedload(Invoice.items))\
            .all()
        
        if not invoices:
            return pd.DataFrame(), pd.DataFrame()

        # --- Procesar Facturas ---
        data_invoices = []
        for inv in invoices:
            data_invoices.append({
                "id": inv.id,
                "vendor": inv.vendor,
                "date": inv.date, # Esto suele ser un objeto datetime.date
                "total": float(inv.total_amount or 0), # Convertimos a float seguro
                "currency": inv.currency
            })
        df_invoices = pd.DataFrame(data_invoices)
        # Aseguramos formato datetime para poder filtrar luego
        df_invoices['date'] = pd.to_datetime(df_invoices['date'])

        # --- Procesar Ítems ---
        data_items = []
        for inv in invoices:
            for item in inv.items:
                # REVISIÓN: Calculamos el total aquí para asegurar consistencia
                qty = float(item.quantity or 0)
                price = float(item.unit_price or 0)
                total_line = item.total_price if item.total_price else (qty * price)

                data_items.append({
                    "date": pd.to_datetime(inv.date), 
                    "vendor": inv.vendor,
                    "description": item.description,
                    "quantity": qty,
                    "unit_price": price,
                    "total_line": float(total_line)
                })
        df_items = pd.DataFrame(data_items)

        return df_invoices, df_items
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame(), pd.DataFrame()
    finally:
        db.close()

def render_dashboard_view():
    st.title("📊 Control de Costes y Compras")

    df_invoices, df_items = load_data()

    if df_invoices.empty:
        st.info("👋 ¡Hola! Aún no tienes datos. Ve a 'Subir Facturas' para empezar.")
        return

    # --- BARRA LATERAL (FILTROS) ---
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
        
        # Convertimos date a datetime para que la comparación sea correcta
        fecha_inicio = datetime.combine(d_start, time.min)
        fecha_fin = datetime.combine(d_end, time.max)

    # Aseguramos normalización de fechas
    fecha_inicio = pd.to_datetime(fecha_inicio)
    fecha_fin = pd.to_datetime(fecha_fin)

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Del: {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}")

    # --- APLICAR FILTROS ---
    # Normalizamos la columna date del dataframe para asegurar comparaciones sin hora
    mask_inv = (df_invoices['date'] >= fecha_inicio) & (df_invoices['date'] <= fecha_fin)
    df_inv_filtered = df_invoices.loc[mask_inv].copy()
    
    mask_items = (df_items['date'] >= fecha_inicio) & (df_items['date'] <= fecha_fin)
    df_items_filtered = df_items.loc[mask_items].copy()

    # --- MÉTRICAS (KPIs) ---
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    
    gasto_total = df_inv_filtered['total'].sum()
    num_facturas = len(df_inv_filtered)
    proveedores_unicos = df_inv_filtered['vendor'].nunique()
    
    # Calculamos el producto frecuente con seguridad
    top_prod = "N/A"
    if not df_items_filtered.empty:
        modas = df_items_filtered['description'].mode()
        if not modas.empty:
            top_prod = modas[0]
            # Si el nombre es muy largo, lo cortamos visualmente
            if len(top_prod) > 15: 
                top_prod = top_prod[:12] + "..."

    col1.metric("Gasto Total", f"{gasto_total:,.2f}€")
    col2.metric("Facturas", num_facturas)
    col3.metric("Proveedores", proveedores_unicos)
    col4.metric("Prod. Frecuente", top_prod)

    # --- ANÁLISIS DE PRODUCTOS ---
    st.subheader("🥩 Análisis de Ingredientes")
    
    if not df_items_filtered.empty:
        
        # Agrupación segura
        product_stats = df_items_filtered.groupby('description').agg({
            'total_line': 'sum',      
            'quantity': 'sum',        
            'unit_price': 'mean',     
            'vendor': lambda x: x.mode()[0] if not x.mode().empty else "Varios"
        }).reset_index()

        product_stats.columns = ['Producto', 'Gasto Total (€)', 'Cantidad Total', 'Precio Medio (€)', 'Proveedor']
        product_stats = product_stats.sort_values('Gasto Total (€)', ascending=False)

        tab_gasto, tab_volumen = st.tabs(["💰 Top Gasto", "📦 Top Volumen"])
        
        with tab_gasto:
            chart_gasto = alt.Chart(product_stats.head(10)).mark_bar().encode(
                x=alt.X('Gasto Total (€)', title='Euros Gastados'),
                y=alt.Y('Producto', sort='-x'),
                color=alt.Color('Gasto Total (€)', scale=alt.Scale(scheme='orangered')),
                tooltip=['Producto', 'Gasto Total (€)', 'Proveedor']
            ).properties(height=350)
            st.altair_chart(chart_gasto, use_container_width=True)

        with tab_volumen:
            stats_qty = product_stats.sort_values('Cantidad Total', ascending=False).head(10)
            chart_qty = alt.Chart(stats_qty).mark_bar().encode(
                x=alt.X('Cantidad Total', title='Cantidad'),
                y=alt.Y('Producto', sort='-x'),
                color=alt.Color('Cantidad Total', scale=alt.Scale(scheme='blues')),
                tooltip=['Producto', 'Cantidad Total', 'Proveedor']
            ).properties(height=350)
            st.altair_chart(chart_qty, use_container_width=True)

        st.write("#### 📋 Detalle")
        st.dataframe(
            product_stats,
            column_config={
                "Gasto Total (€)": st.column_config.ProgressColumn(
                    "Gasto Total",
                    format="%.2f €",
                    min_value=0,
                    max_value=float(product_stats['Gasto Total (€)'].max()),
                ),
                "Cantidad Total": st.column_config.NumberColumn("Cantidad", format="%.2f"),
                "Precio Medio (€)": st.column_config.NumberColumn("Precio Medio", format="%.2f €"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.warning("No hay productos registrados en este periodo.")

    st.divider()

    # --- DETECTOR DE INFLACIÓN ---
    st.subheader("📈 Detector de Inflación")
    
    # Usamos TODOS los items históricos, no solo los filtrados, para ver la evolución real
    todos_items = sorted(df_items['description'].unique()) if not df_items.empty else []
    
    col_sel, col_info = st.columns([2, 1])
    with col_sel:
        item_seleccionado = st.selectbox("Buscar evolución de precio:", todos_items)

    if item_seleccionado:
        # Filtramos historial completo de ese item
        historial = df_items[df_items['description'] == item_seleccionado].sort_values('date')
        
        if not historial.empty:
            # Gráfico de línea temporal
            chart_line = alt.Chart(historial).mark_line(point=True).encode(
                x=alt.X('date:T', title='Fecha', axis=alt.Axis(format='%d/%m/%y')),
                y=alt.Y('unit_price', title='Precio Unitario (€)', scale=alt.Scale(zero=False)), # zero=False para ver mejor las variaciones pequeñas
                tooltip=[
                    alt.Tooltip('date', title='Fecha', format='%d-%m-%Y'), 
                    alt.Tooltip('unit_price', title='Precio', format='.2f€'),
                    'vendor'
                ]
            ).interactive()
            st.altair_chart(chart_line, use_container_width=True)
            
            # Estadísticas rápidas
            with col_info:
                curr_price = historial.iloc[-1]['unit_price']
                avg_price = historial['unit_price'].mean()
                delta = ((curr_price - avg_price) / avg_price) * 100
                
                st.metric("Precio Última Compra", f"{curr_price:.2f}€", f"{delta:.1f}% vs Media")
                st.caption(f"Min: {historial['unit_price'].min():.2f}€ | Max: {historial['unit_price'].max():.2f}€")
                
        else:
            st.info("Sin datos suficientes para graficar.")