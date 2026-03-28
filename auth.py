import sqlite3
import hashlib
from datetime import datetime
import os

DB_PATH = "data/iribas_auth.db"
ADMIN_EMAIL = "r.migliore@iribas.com.py"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Tabla Usuarios
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla Logs/Auditoría
    c.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(email: str, password: str) -> tuple[bool, str]:
    if not email.endswith('@iribas.com.py'):
        return False, "El correo debe terminar en @iribas.com.py"
        
    role = "admin" if email.lower() == ADMIN_EMAIL.lower() else "viewer"
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)", 
                  (email.lower(), hash_password(password), role))
        conn.commit()
        return True, "Cuenta creada exitosamente. Ya puedes iniciar sesión."
    except sqlite3.IntegrityError:
        return False, "Este correo ya está registrado."
    finally:
        conn.close()

def login_user(email: str, password: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT email, role, password_hash FROM users WHERE email=?", (email.lower(),))
    user = c.fetchone()
    conn.close()
    
    if user and user[2] == hash_password(password):
        return {"email": user[0], "role": user[1]}
    return None

def log_action(email: str, action: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO activity_logs (email, action) VALUES (?, ?)", (email.lower(), action))
    conn.commit()
    conn.close()

def get_logs():
    conn = sqlite3.connect(DB_PATH)
    # Get last 500 logs ordered by timestamp desc
    import pandas as pd
    df = pd.read_sql_query("SELECT timestamp as Fecha, email as Usuario, action as Accion FROM activity_logs ORDER BY id DESC LIMIT 500", conn)
    conn.close()
    return df

def get_users():
    conn = sqlite3.connect(DB_PATH)
    import pandas as pd
    df = pd.read_sql_query("SELECT email as Usuario, role as Rol, created_at as 'Fecha de Creación' FROM users ORDER BY id DESC", conn)
    conn.close()
    return df

init_db()
