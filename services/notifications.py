import os
import resend
from sqlalchemy.orm import Session
from database.models import Invoice, InvoiceItem
from sqlalchemy import desc


resend.api_key = os.getenv("RESEND_API_KEY")

def obtener_precio_anterior(db: Session, user_id: str, description: str, current_date: str):
    """
    Busca la última vez que compramos este ítem antes de la fecha actual
    para comparar el precio.
    """
    last_purchase = (
        db.query(InvoiceItem)
        .join(Invoice)
        .filter(
            Invoice.user_id == user_id,
            InvoiceItem.description == description,
            Invoice.date < current_date 
        )
        .order_by(desc(Invoice.date)) 
        .first()
    )
    
    if last_purchase:
        return last_purchase.unit_price
    return None

def enviar_alerta_correo(user_email, alertas):
    """
    Envía un correo HTML bonito con la tabla de subidas.
    """
    if not alertas:
        return

    
    items_html = ""
    for item in alertas:
        subida = item['nuevo'] - item['anterior']
        porcentaje = (subida / item['anterior']) * 100
        
        items_html += f"""
        <li style="margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px;">
            <strong>{item['producto']}</strong><br>
            🔴 Antes: {item['anterior']:.2f}€ | Ahora: {item['nuevo']:.2f}€<br>
            <span style="color: red; font-weight: bold;">▲ Subida: +{porcentaje:.1f}% ({subida:.2f}€)</span>
        </li>
        """

    html_content = f"""
    <h1>⚠️ Alerta de Inflación Detectada</h1>
    <p>Hola, hemos detectado que algunos productos de tu última factura han subido de precio respecto a tu última compra:</p>
    <ul>
        {items_html}
    </ul>
    <p>Te recomendamos revisar proveedores o ajustar tus precios de venta.</p>
    <br>
    <p><em>Tu Asistente de Facturas AI 🤖</em></p>
    """

    try:
        r = resend.Emails.send({
            "from": "onboarding@resend.dev", 
            "to": user_email,
            "subject": f"📈 Alerta: {len(alertas)} productos han subido de precio",
            "html": html_content
        })
        return r
    except Exception as e:
        print(f"Error enviando email: {e}")
        return None