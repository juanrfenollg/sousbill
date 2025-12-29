import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")


supabase: Client = create_client(url, key)

def sign_in(email, password):
    """Inicia sesión y devuelve el usuario si es correcto"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email, 
            "password": password
        })
        return response.user
    except Exception as e:
        return None

def sign_up(email, password):
    """Registra un nuevo usuario"""
    try:
        response = supabase.auth.sign_up({
            "email": email, 
            "password": password
        })
        return response.user
    except Exception as e:
        return None

def sign_out():
    """Cierra la sesión"""
    supabase.auth.sign_out()