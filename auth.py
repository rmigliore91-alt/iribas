import hashlib
from datetime import datetime
import os
import json

# ──────────────────────────────────────────────────────────────────────────────
# FILE-BASED AUTH (persists across Streamlit Cloud reboots via repo)
# Users stored in JSON; activity logs stored in SQLite (ephemeral, non-critical)
# ──────────────────────────────────────────────────────────────────────────────

USERS_FILE = "data/users.json"
ADMIN_EMAIL = "r.migliore@iribas.com.py"


def _load_users() -> dict:
    """Load users dict from JSON file."""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_users(users: dict):
    """Save users dict to JSON file."""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def _migrate_from_sqlite():
    """One-time migration: copy users from old SQLite DB to JSON if JSON is empty."""
    import sqlite3
    db_path = "data/iribas_auth.db"
    if not os.path.exists(db_path):
        return
    users = _load_users()
    if users:  # already migrated
        return
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT email, password_hash, role, created_at FROM users")
        for row in c.fetchall():
            email, pw_hash, role, created_at = row
            users[email.lower()] = {
                "email": email.lower(),
                "password_hash": pw_hash,
                "role": role,
                "created_at": created_at or datetime.now().isoformat(),
            }
        conn.close()
        if users:
            _save_users(users)
    except Exception:
        pass


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(email: str, password: str) -> tuple[bool, str]:
    if not email.endswith('@iribas.com.py'):
        return False, "El correo debe terminar en @iribas.com.py"

    email_lower = email.lower()
    role = "admin" if email_lower == ADMIN_EMAIL.lower() else "viewer"

    users = _load_users()
    if email_lower in users:
        return False, "Este correo ya está registrado."

    users[email_lower] = {
        "email": email_lower,
        "password_hash": hash_password(password),
        "role": role,
        "created_at": datetime.now().isoformat(),
    }
    _save_users(users)
    return True, "Cuenta creada exitosamente. Ya puedes iniciar sesión."


def login_user(email: str, password: str) -> dict:
    users = _load_users()
    user = users.get(email.lower())
    if user and user["password_hash"] == hash_password(password):
        return {"email": user["email"], "role": user["role"]}
    return None


def log_action(email: str, action: str):
    """Log to SQLite (ephemeral, best-effort). Not critical if lost on reboot."""
    try:
        import sqlite3
        db_path = "data/iribas_auth.db"
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute("INSERT INTO activity_logs (email, action) VALUES (?, ?)", (email.lower(), action))
        conn.commit()
        conn.close()
    except Exception:
        pass  # non-critical


def get_logs():
    """Get activity logs (ephemeral)."""
    import pandas as pd
    try:
        import sqlite3
        db_path = "data/iribas_auth.db"
        if not os.path.exists(db_path):
            return pd.DataFrame(columns=["Fecha", "Usuario", "Accion"])
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(
            "SELECT timestamp as Fecha, email as Usuario, action as Accion "
            "FROM activity_logs ORDER BY id DESC LIMIT 500", conn
        )
        conn.close()
        return df
    except Exception:
        return pd.DataFrame(columns=["Fecha", "Usuario", "Accion"])


def get_users():
    """Get all registered users."""
    import pandas as pd
    users = _load_users()
    if not users:
        return pd.DataFrame(columns=["Usuario", "Rol", "Fecha de Creación"])
    rows = [
        {"Usuario": u["email"], "Rol": u["role"], "Fecha de Creación": u.get("created_at", "")}
        for u in users.values()
    ]
    return pd.DataFrame(rows)


def init_db():
    """Initialize: migrate old SQLite users to JSON if needed."""
    os.makedirs("data", exist_ok=True)
    _migrate_from_sqlite()
    # Ensure at least the admin exists
    users = _load_users()
    if not users:
        # Create default admin
        users[ADMIN_EMAIL.lower()] = {
            "email": ADMIN_EMAIL.lower(),
            "password_hash": hash_password("admin2024"),
            "role": "admin",
            "created_at": datetime.now().isoformat(),
        }
        _save_users(users)


init_db()
