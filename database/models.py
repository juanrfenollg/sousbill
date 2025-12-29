from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime # <--- Añade String
from sqlalchemy.orm import relationship
from database.connection import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(String, index=True) 
    

    vendor = Column(String)
    date = Column(String)
    total_amount = Column(Float)
    currency = Column(String)
    image_url = Column(String)

    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    description = Column(String)
    quantity = Column(Float)
    unit_price = Column(Float)
    total_price = Column(Float)

    invoice = relationship("Invoice", back_populates="items")