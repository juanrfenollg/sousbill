import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(" ERROR CRÍTICO: No se encontró la variable 'DATABASE_URL' en el archivo .env")


if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

try:
    
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    print(f" Engine configurado para: {DATABASE_URL.split('@')[1]}") 
except Exception as e:
    print(f" Error creando el engine de base de datos: {e}")
    raise e

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    """
    Crea las tablas en la base de datos si no existen.
    Se llama al inicio de la aplicación.
    """
    
    import database.models
    
    print(" Creando/Verificando tablas en Supabase...")
    Base.metadata.create_all(bind=engine)
    print(" Tablas listas.")

def get_db_session():
    """
    Generador que entrega una sesión segura y la cierra al terminar.
    Uso: with get_db_session() as db: ...
    """
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e