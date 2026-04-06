import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
import auth

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG & CUSTOM THEME
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Clínico · Analítica Médica",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium dark theme via CSS injection
st.markdown('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">', unsafe_allow_html=True)
st.markdown("""
<style>

:root {
    --bg-primary: #0e1117;
    --bg-card: #161b22;
    --bg-card-hover: #1c2333;
    --accent: #A11C32;
    --accent-glow: rgba(161, 28, 50, 0.15);
    --accent-green: #3fb950;
    --accent-purple: #264C8D;
    --accent-orange: #f0883e;
    --accent-pink: #f778ba;
    --text-primary: #e6edf3;
    --text-muted: #8b949e;
    --border: #30363d;
    --radius: 12px;
}

html, body, [class*="st-"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* EVITAR QUE EL FONT OVERRIDE ROMPA LOS ICONOS (LIGATURES) */
.material-symbols-rounded, 
.material-symbols-outlined, 
.material-icons, 
[class*="stIcon"],
[data-testid="stIconMaterial"] {
    font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
}
.stApp { background: var(--bg-primary); }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .stMarkdown h2 {
    color: var(--accent);
    font-weight: 700;
    letter-spacing: -0.02em;
}

div[data-testid="stMetric"] {
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-card-hover) 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 24px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
div[data-testid="stMetric"]:hover {
    border-color: var(--accent);
    box-shadow: 0 4px 20px var(--accent-glow);
    transform: translateY(-2px);
}
div[data-testid="stMetric"] label {
    color: var(--text-muted) !important;
    font-weight: 500;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.08em;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-weight: 700;
    font-size: 1.6rem !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: var(--bg-card);
    border-radius: var(--radius);
    padding: 4px;
    border: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 500;
    color: var(--text-muted);
    transition: all 0.2s ease;
}
.stTabs [aria-selected="true"] {
    background: var(--accent) !important;
    color: #fff !important;
    font-weight: 600;
    box-shadow: 0 2px 8px var(--accent-glow);
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-primary);
    background: rgba(88, 166, 255, 0.08);
}

.stDataFrame {
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
}

h1, .stTitle {
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-purple) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800 !important;
    letter-spacing: -0.03em;
}
h2, h3 { color: var(--text-primary) !important; font-weight: 600 !important; }
hr { border-color: var(--border) !important; }

section[data-testid="stFileUploader"] {
    border: 2px dashed var(--border);
    border-radius: var(--radius);
    padding: 8px;
    transition: border-color 0.3s ease;
}
section[data-testid="stFileUploader"]:hover { border-color: var(--accent); }
.stAlert { border-radius: var(--radius); border: 1px solid var(--border); }
.stPlotlyChart { border-radius: var(--radius); overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# PLOTLY THEME DEFAULTS
# ──────────────────────────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#e6edf3"),
    margin=dict(l=40, r=40, t=60, b=40),
    title_font=dict(size=16, color="#e6edf3"),
    title_subtitle_text="",
    hoverlabel=dict(
        bgcolor="#1c2333", font_size=13,
        font_family="Inter, sans-serif", bordercolor="#30363d",
    ),
    colorway=[
        "#58a6ff", "#3fb950", "#bc8cff", "#f0883e",
        "#f778ba", "#79c0ff", "#56d364", "#d2a8ff",
        "#ffa657", "#ff7b72",
    ],
)

HEATMAP_COLORS = [
    [0.0, "#0d1117"], [0.2, "#1a1e2e"], [0.4, "#1f3a5f"],
    [0.6, "#2a6496"], [0.8, "#3d8bd4"], [1.0, "#58a6ff"],
]

# ──────────────────────────────────────────────────────────────────────────────
# DIFFICULTY SCORING — weights per Sector (study type)
# ──────────────────────────────────────────────────────────────────────────────
DIFICULTAD_SECTOR = {
    "Radiografía": 1.0,
    "Densitometría Osea": 0.5,
    "Ecografía": 3.0,
    "Mamografía": 4.5,
    "Tomografía": 6.0,
    "Resonancia": 10.0,
}
DIFICULTAD_DEFAULT = 2.0


# ──────────────────────────────────────────────────────────────────────────────
# AGGREGATION HELPERS (No cache needed, pandas grouping is 100x faster than memory hashing)
# ──────────────────────────────────────────────────────────────────────────────
def compute_ranking(df_rad_ser):
    """Pre-compute ranking table from serialized radiologist data."""
    df = df_rad_ser
    rank = (
        df.groupby("Doctor Informante")
        .agg(
            Estudios=("Doctor Informante", "count"),
            Puntaje_Total=("Puntaje_Dificultad", "sum"),
            Facturacion=("TOTAL", "sum") if "TOTAL" in df.columns else ("Puntaje_Dificultad", "count")
        )
        .reset_index()
    )
    rank["Puntaje_Prom"] = rank["Puntaje_Total"] / rank["Estudios"]
    return rank.sort_values("Puntaje_Total", ascending=False)



def compute_detail_all(df_rad_ser):
    """Pre-compute per-radiologist + per-sector breakdown for all radiologists at once."""
    df = df_rad_ser
    detail = (
        df.groupby(["Doctor Informante", "Sector"])
        .agg(Estudios=("Sector", "count"), Puntaje=("Puntaje_Dificultad", "sum"))
        .reset_index()
    )
    return detail



def compute_evolution_general(df_rad_ser):
    """Pre-compute monthly evolution for entire center."""
    df = df_rad_ser
    evol = (
        df.groupby(pd.Grouper(key="Fecha", freq="ME"))
        .agg(Estudios=("Fecha", "count"), Puntaje=("Puntaje_Dificultad", "sum"))
        .reset_index()
    )
    evol["Periodo"] = evol["Fecha"].dt.strftime("%Y-%m")
    return evol



def compute_evolution_individual(df_rad_ser):
    """Pre-compute monthly evolution per radiologist."""
    df = df_rad_ser
    evol_pts = (
        df.groupby([pd.Grouper(key="Fecha", freq="ME"), "Doctor Informante"])
        .agg(Puntaje=("Puntaje_Dificultad", "sum"), Estudios=("Fecha", "count"))
        .reset_index()
    )
    evol_pts["Periodo"] = evol_pts["Fecha"].dt.strftime("%Y-%m")
    return evol_pts


# ──────────────────────────────────────────────────────────────────────────────
# HELPER: parse Guaraní-style numbers like " 97,000 " or " 230,000 "
# In PY locale: the comma here is thousands separator, not decimal.
# ──────────────────────────────────────────────────────────────────────────────
def parse_guarani_number(series):
    """Convert strings like ' 97,000 ' or ' - ' to float.
    Treats comma as thousands separator (Guaraní convention).
    """
    def _clean(x):
        s = str(x).strip()
        for ch in ["-", ".", ",", "$"]:
            s = s.replace(ch, "")
        return s.strip()

    cleaned = series.apply(_clean)
    return pd.to_numeric(cleaned, errors="coerce").fillna(0)


# ──────────────────────────────────────────────────────────────────────────────
# SMART CSV READER — auto-detects delimiter (comma, semicolon, tab, etc.)
# ──────────────────────────────────────────────────────────────────────────────
import csv
import io

def smart_read_csv(file, **kwargs):
    """Read CSV auto-detecting the delimiter. Works with file paths and file-like objects."""
    try:
        # Try reading a sample to sniff the delimiter
        if hasattr(file, 'read'):
            sample = file.read(8192)
            if isinstance(sample, bytes):
                sample = sample.decode('utf-8-sig', errors='replace')
            file.seek(0)
        else:
            with open(file, 'r', encoding='utf-8-sig', errors='replace') as f:
                sample = f.read(8192)
        dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
        sep = dialect.delimiter
    except Exception:
        sep = ','  # default fallback
    kwargs.setdefault('encoding', 'utf-8-sig')
    kwargs.setdefault('sep', sep)
    return pd.read_csv(file, **kwargs)


# ──────────────────────────────────────────────────────────────────────────────
# DATA LOADING & PREPROCESSING
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(file):
    """Load CSV adapted to the actual file format from the medical center."""
    df = smart_read_csv(file)
    df = df.reset_index(drop=True)  # ensure unique index after concat/dedup

    # ── Strip whitespace from column names ───────────────────────────────
    df.columns = df.columns.str.strip()

    # ── Deduplicate ALL column names (append _2, _3, … to repeats) ───────
    seen = {}
    new_cols = []
    for c in df.columns:
        if c in seen:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 1
            new_cols.append(c)
    df.columns = new_cols

    # ── Rename second Hora to "Hora_Num" (handles both our _2 and pandas .1)
    rename_map = {}
    if "Hora_2" in df.columns:
        rename_map["Hora_2"] = "Hora_Num"
    if "Hora.1" in df.columns:
        rename_map["Hora.1"] = "Hora_Num"
    # Fix known typo in source data
    if "Total a PAgar Seguro" in df.columns:
        rename_map["Total a PAgar Seguro"] = "Total a Pagar Seguro"
    if rename_map:
        df = df.rename(columns=rename_map)

    # ── Strip whitespace from all string values ─────────────────────────
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    # ── Drop fully empty trailing columns ────────────────────────────────
    df = df.dropna(axis=1, how="all")

    # ── Fecha: construct from Año/Mes/Dia columns (unambiguous) ────────
    if all(c in df.columns for c in ["Año", "Mes", "Dia"]):
        # Build dates from the explicit numeric columns — zero ambiguity
        df["Año"] = pd.to_numeric(df["Año"], errors="coerce")
        df["Mes"] = pd.to_numeric(df["Mes"], errors="coerce")
        df["Dia"] = pd.to_numeric(df["Dia"], errors="coerce")
        df["Fecha"] = pd.to_datetime(
            df[["Año", "Mes", "Dia"]].rename(columns={"Año": "year", "Mes": "month", "Dia": "day"}),
            errors="coerce",
        )
    elif "Fecha" in df.columns:
        # Fallback: parse from Fecha string (try M/D/YY since that matches the source format)
        parsed = pd.to_datetime(df["Fecha"], format="%m/%d/%y", errors="coerce")
        # Then try other formats
        missing = parsed.isna() & df["Fecha"].notna()
        if missing.any():
            parsed.loc[missing] = pd.to_datetime(
                df.loc[missing, "Fecha"], dayfirst=True, errors="coerce"
            )
        df["Fecha"] = parsed

    # ── Day of week (runs for both parsing paths) ────────────────────────
    if "Fecha" in df.columns and pd.api.types.is_datetime64_any_dtype(df["Fecha"]):
        dias_map = {
            0: "Lunes", 1: "Martes", 2: "Miércoles",
            3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo",
        }
        df["Dia_Semana"] = df["Fecha"].dt.dayofweek.map(dias_map)

    # ── Hora_Num: ensure integer hour ────────────────────────────────────
    if "Hora_Num" in df.columns:
        df["Hora_Num"] = pd.to_numeric(df["Hora_Num"], errors="coerce").astype("Int64")
    elif "Hora" in df.columns:
        parsed = pd.to_datetime(df["Hora"], format="%H:%M", errors="coerce")
        df["Hora_Num"] = parsed.dt.hour
        mask = df["Hora_Num"].isna()
        df.loc[mask, "Hora_Num"] = pd.to_numeric(
            df.loc[mask, "Hora"], errors="coerce"
        )
        df["Hora_Num"] = df["Hora_Num"].astype("Int64")

    # ── Financial columns: parse Guaraní format ──────────────────────────
    financial_cols = [
        "Arancel de Estudio",
        "Total a Pagar Estudio Seguro",
        "Total a Pagar Estudio Paciente",
        "Total a Pagar Insumos Seguro",
        "Total a Pagar Insumos Paciente",
        "Total a Pagar Paciente",
        "Descuento",
        "Total a Pagar Paciente con Descuento",
        "Total a Pagar Seguro",
        "TOTAL",
        "Insumos",
    ]
    for col in financial_cols:
        if col in df.columns:
            df[col] = parse_guarani_number(df[col])

    # ── Tipo paciente: PARTICULAR vs Seguro ──────────────────────────────
    if "Seguro" in df.columns:
        df["Tipo_Paciente"] = df["Seguro"].apply(
            lambda x: "Particular"
            if str(x).strip().upper() == "PARTICULAR"
            else "Seguro"
        )

    # ── Normalize Doctor Informante to uppercase ─────────────────────────
    if "Doctor Informante" in df.columns:
        df["Doctor Informante"] = df["Doctor Informante"].apply(
            lambda x: str(x).upper().strip() if pd.notna(x) else x
        )
    if "Doctor Tratante" in df.columns:
        df["Doctor Tratante"] = df["Doctor Tratante"].apply(
            lambda x: str(x).upper().strip() if pd.notna(x) else x
        )

    # ── Apply Aliases (Médicos Fusionados) ──────────────────────────────
    aliases_path = "data/aliases_medicos.json"
    if os.path.exists(aliases_path):
        try:
            with open(aliases_path, "r", encoding="utf-8") as f:
                aliases = json.load(f)
            if "Doctor Tratante" in df.columns:
                df["Doctor Tratante"] = df["Doctor Tratante"].replace(aliases)
            if "Doctor Informante" in df.columns:
                df["Doctor Informante"] = df["Doctor Informante"].replace(aliases)
        except Exception:
            pass

    # ── Normalize Sector to Title Case to prevent duplicate categories ───
    if "Sector" in df.columns:
        df["Sector"] = df["Sector"].apply(
            lambda x: str(x).strip().title() if pd.notna(x) else x
        )
        # Restore specific acronyms that should be uppercase
        df["Sector"] = df["Sector"].replace({
            "Pap": "PAP", "Eeg": "EEG", "Ecg": "ECG", "Rmn": "RMN", "Tac": "TAC"
        })

    # ── Difficulty score per study ───────────────────────────────────────
    if "Sector" in df.columns:
        df["Puntaje_Dificultad"] = df["Sector"].map(DIFICULTAD_SECTOR).fillna(DIFICULTAD_DEFAULT)

    # ── Lugar de Estudio (from OTRO column) ──────────────────────────────
    if "OTRO" in df.columns:
        df["Lugar_Estudio"] = df["OTRO"].apply(
            lambda x: str(x).strip().upper() if pd.notna(x) else "IRIBAS"
        )
        # SI means the study was done at IRIBAS
        df["Lugar_Estudio"] = df["Lugar_Estudio"].replace({
            "SI": "IRIBAS", "": "IRIBAS",
        })
        # Flag: internal vs external
        df["Es_Externo"] = df["Lugar_Estudio"].apply(
            lambda x: "Externo" if x != "IRIBAS" else "IRIBAS"
        )

    # ── Agente de Fichaje (from 'Usuario que fichó' column) ──────────────
    if "Usuario que fichó" in df.columns:
        df["Agente"] = df["Usuario que fichó"].apply(
            lambda x: str(x).strip() if pd.notna(x) and str(x).strip() != "" else pd.NA
        )

    # ── Replace bare "-" with NaN in remaining object cols ───────────────
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].replace("-", pd.NA)

    return df


# ──────────────────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center; padding: 12px 0 4px 0;">
        <h1 style="margin-bottom:0; font-size:2.2rem;">
            🏥 Dashboard Analítico Clínico y Financiero
        </h1>
        <p style="color:#8b949e; font-size:0.95rem; margin-top:4px;">
            Análisis integral de volumen operativo, rendimiento financiero y red de derivación médica
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# AUTHENTICATION
# ──────────────────────────────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state["user"] = None

def show_auth_page():
    # Decorate login page with custom background color elements if needed
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", use_container_width=True)
        else:
            st.markdown(
                """
                <div style="background: linear-gradient(135deg, #A11C32 0%, #264C8D 100%); 
                            padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px;">
                    <h1 style='color: white; margin:0;'>INSTITUTO IRIBAS</h1>
                    <h4 style='color: rgba(255,255,255,0.8); margin:0;'>Analítica Médica</h4>
                </div>
                """, unsafe_allow_html=True
            )
            
        st.markdown("---")
        
        tab_login, tab_register = st.tabs(["🚀 Iniciar Sesión", "📝 Crear Cuenta"])
        
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Ingresa tu correo (@iribas.com.py)")
                password = st.text_input("Contraseña", type="password")
                submit = st.form_submit_button("Ingresar", use_container_width=True)
                
                if submit:
                    user_data = auth.login_user(email, password)
                    if user_data:
                        st.session_state["user"] = user_data
                        auth.log_action(email, "Inició sesión")
                        st.success("¡Bienvenido!")
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas o usuario no registrado.")
                        
        with tab_register:
            with st.form("register_form"):
                reg_email = st.text_input("Correo Institucional (@iribas.com.py)")
                reg_password = st.text_input("Crea una contraseña", type="password")
                reg_submit = st.form_submit_button("Registrarse", use_container_width=True)
                
                if reg_submit:
                    success, msg = auth.register_user(reg_email, reg_password)
                    if success:
                        auth.log_action(reg_email, "Creó una nueva cuenta")
                        st.success(msg)
                    else:
                        st.error(msg)
                        
    st.stop()

if st.session_state["user"] is None:
    show_auth_page()

from utils_auth import init_sidebar_auth
init_sidebar_auth()

user_role = st.session_state["user"]["role"]
user_email = st.session_state["user"]["email"]

# ──────────────────────────────────────────────────────────────────────────────
# MENÚ LOGICO / NAV LATERAL (grouped by domain)
# ──────────────────────────────────────────────────────────────────────────────
# Flat list used internally — order matches the grouped sidebar below
_all_pages = [
    "📊 Dashboard General",            # 0 → tab1 (Evolución)
    "💰 KPIs Financieros",             # 1 → tab3
    "💎 Micro-Rentabilidad y Caja",    # 2 → tab11
    "🩺 Médicos Tratantes",            # 3 → tab5 (Red de Derivación)
    "🔬 Radiólogos Informantes",       # 4 → tab6
    "🔥 Mapa de Calor",                # 5 → tab2
    "🏢 Rendimiento por Sector",       # 6 → tab4
    "🔎 Análisis de Estudios",         # 7 → tab10
    "🛡️ Ranking de Seguros",           # 8 → tab7
    "📝 Agentes de Fichaje",           # 9 → tab12
    "📞 KPI Call Center",              # 10 → tab_cc
    "⚖️ Comparativa",                  # 11 → tab8
]

if user_role == "admin":
    _all_pages.append("⚙️ Panel Admin")  # 12 → tab9

with st.sidebar:
    st.markdown("##### 📍 Menú Principal")

    # ── Initialize active page in session state ──
    if "_active_page" not in st.session_state:
        st.session_state["_active_page"] = _all_pages[0]

    def _set_page(page):
        st.session_state["_active_page"] = page

    # Helper: render a group of pages as buttons
    def _nav_group(label, page_indices):
        st.markdown(f"<p style='color:#aaa;font-size:0.72rem;margin:12px 0 2px 4px;letter-spacing:0.05em;text-transform:uppercase;'>{label}</p>", unsafe_allow_html=True)
        for idx in page_indices:
            page = _all_pages[idx]
            is_active = st.session_state["_active_page"] == page
            btn_type = "primary" if is_active else "secondary"
            st.button(page, key=f"nav_{idx}", on_click=_set_page, args=(page,), use_container_width=True, type=btn_type)

    _nav_group("GENERAL", [0])
    _nav_group("FINANCIERO", [1, 2])
    _nav_group("MÉDICOS", [3, 4])
    _nav_group("INSTITUCIÓN", [5, 6, 7, 8, 9, 10])
    _nav_group("ANÁLISIS", [11])
    if user_role == "admin":
        _nav_group("ADMINISTRACIÓN", [12])

    current_tab = st.session_state["_active_page"]
    st.markdown("---")

# Map grouped menu → same tab flags used by all content blocks
tab1   = current_tab == _all_pages[0]   # Dashboard General
tab3   = current_tab == _all_pages[1]   # KPIs Financieros
tab11  = current_tab == _all_pages[2]   # Micro-Rentabilidad
tab5   = current_tab == _all_pages[3]   # Médicos Tratantes
tab6   = current_tab == _all_pages[4]   # Radiólogos Informantes
tab2   = current_tab == _all_pages[5]   # Mapa de Calor
tab4   = current_tab == _all_pages[6]   # Rendimiento por Sector
tab10  = current_tab == _all_pages[7]   # Análisis de Estudios
tab7   = current_tab == _all_pages[8]   # Ranking de Seguros
tab12  = current_tab == _all_pages[9]   # Agentes de Fichaje
tab_cc = current_tab == _all_pages[10]  # KPI Call Center
tab8   = current_tab == _all_pages[11]  # Comparativa
tab9   = current_tab == _all_pages[12] if user_role == "admin" else False

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR – DATA UPLOAD & FILTERS
# ──────────────────────────────────────────────────────────────────────────────
CACHE_FILE_PATH = "data/last_uploaded.csv"

with st.sidebar:
    if user_role == "admin":
        st.markdown("## 📂 Gestión de Datos (Admin)")
        
        modo_carga = st.radio("Acción con la base actual:", ["Sustituir Base Completa", "Sumar Nuevos Datos"], horizontal=True)
        uploaded_file = st.file_uploader(
            "Sube un nuevo archivo CSV consolidado" if modo_carga == "Sustituir Base Completa" else "Sube el CSV con pacientes/fechas nuevas",
            type=["csv"],
            help="Sustituirá la base actual por completo." if modo_carga == "Sustituir Base Completa" else "Se anexará automáticamente al final de la base principal eliminando duplicados."
        )

        if uploaded_file is not None:
            # Track which file has already been processed to avoid re-running on every rerun
            file_id = f"{uploaded_file.name}_{uploaded_file.size}"
            already_processed = st.session_state.get("_last_processed_file") == file_id

            os.makedirs(os.path.dirname(CACHE_FILE_PATH), exist_ok=True)
            if modo_carga == "Sustituir Base Completa":
                if not already_processed:
                    with open(CACHE_FILE_PATH, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    auth.log_action(user_email, "Subió un nuevo archivo CSV sustituto")
                    st.session_state["_last_processed_file"] = file_id
                file_to_load = CACHE_FILE_PATH
            else:
                if not already_processed:
                    with st.spinner("Anexando datos a la base principal y optimizando duplicados..."):
                        base_path = CACHE_FILE_PATH if os.path.exists(CACHE_FILE_PATH) else ("data/dataset_base.zip" if os.path.exists("data/dataset_base.zip") else None)
                        if base_path:
                            df_base = smart_read_csv(base_path, low_memory=False)
                            df_new = smart_read_csv(uploaded_file, low_memory=False)
                            # Normalize column names before concat (strip spaces + fix typos)
                            df_base.columns = df_base.columns.str.strip()
                            df_new.columns = df_new.columns.str.strip()
                            if "Total a PAgar Seguro" in df_base.columns:
                                df_base = df_base.rename(columns={"Total a PAgar Seguro": "Total a Pagar Seguro"})
                            df_concat = pd.concat([df_base, df_new], ignore_index=True).drop_duplicates()
                            df_concat.to_csv(CACHE_FILE_PATH, index=False, encoding="utf-8-sig")
                        else:
                            with open(CACHE_FILE_PATH, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                    st.session_state["_last_processed_file"] = file_id
                    auth.log_action(user_email, "Anexó nuevos datos al CSV base")
                file_to_load = CACHE_FILE_PATH
                st.success("✅ Datos anexados. Base actualizada.")
        elif os.path.exists(CACHE_FILE_PATH):
            file_to_load = CACHE_FILE_PATH
            st.success("✅ Base de datos unificada en memoria temporal.")
        elif os.path.exists("data/dataset_base.zip"):
            file_to_load = "data/dataset_base.zip"
            st.success("✅ Base de datos predeterminada activa.")
        else:
            file_to_load = None
            
        if file_to_load is not None:
            st.markdown("---")
            c_btn1, c_btn2 = st.columns(2)
            if c_btn1.button("🗑️ Borrar Temporales y Restablecer", use_container_width=True):
                if os.path.exists(CACHE_FILE_PATH):
                    os.remove(CACHE_FILE_PATH)
                st.cache_data.clear()
                auth.log_action(user_email, "Reinició temporal de la base de datos CSV")
                st.rerun()
            
            if os.path.exists(CACHE_FILE_PATH):
                with open(CACHE_FILE_PATH, "rb") as f:
                    c_btn2.download_button("💾 Descargar Base Unida (Master)", data=f, file_name="Iribas_Base_Sumada.csv", mime="text/csv", use_container_width=True)
    else:
        st.markdown("## 📂 Estado de Datos")
        if os.path.exists(CACHE_FILE_PATH):
            file_to_load = CACHE_FILE_PATH
            st.success("✅ Base de datos activa y en línea.")
        elif os.path.exists("data/dataset_base.zip"):
            file_to_load = "data/dataset_base.zip"
            st.success("✅ Base de datos predeterminada activa.")
        else:
            file_to_load = None
            st.warning("⚠️ El administrador aún no ha cargado los datos.")

# ──────────────────────────────────────────────────────────────────────────────
# LANDING STATE
# ──────────────────────────────────────────────────────────────────────────────
if file_to_load is None:
    st.markdown("---")
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown(
            """
            <div style="
                text-align:center;
                padding:80px 20px;
                border: 2px dashed #30363d;
                border-radius: 16px;
                background: linear-gradient(135deg, rgba(88,166,255,0.04) 0%, rgba(188,140,255,0.04) 100%);
            ">
                <div style="font-size:4rem; margin-bottom:16px;">📊</div>
                <h3 style="color:#e6edf3; margin-bottom:8px;">¡Bienvenido!</h3>
                <p style="color:#8b949e; max-width:400px; margin:auto; line-height:1.6;">
                    Sube un archivo <code style="color:#58a6ff;">.csv</code> desde el panel lateral
                    para desbloquear la analítica completa de tus datos clínicos y financieros.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# LOAD & FILTER  (optimized: no df.copy, vectorized masks, lightweight widgets)
# ──────────────────────────────────────────────────────────────────────────────
df = load_data(file_to_load)

# Build a single boolean mask instead of copying and re-filtering the whole DF
mask = pd.Series(True, index=df.index)

with st.sidebar:
    st.markdown("---")
    st.markdown("## 🎛️ Filtros Globales")

    # Date range
    if "Fecha" in df.columns and df["Fecha"].notna().any():
        min_d = df["Fecha"].min().date()
        max_d = df["Fecha"].max().date()
        default_start = max_d.replace(day=1)
        rango = st.date_input(
            "📅 Rango de Fechas",
            value=[default_start, max_d],
            min_value=min_d,
            max_value=max_d
        )
        if len(rango) == 2:
            start_ts = pd.to_datetime(rango[0])
            end_ts = pd.to_datetime(rango[1]) + pd.Timedelta(days=1, microseconds=-1)
            mask = mask & (df["Fecha"] >= start_ts) & (df["Fecha"] <= end_ts)

    # Sector — selectbox para excluir (ligero, sin hashear listas enormes)
    if "Sector" in df.columns:
        sectores = ["Todos"] + sorted(df["Sector"].dropna().unique().tolist())
        sel_sector = st.selectbox("🏷️ Filtrar Sector", sectores, index=0)
        if sel_sector != "Todos":
            mask = mask & (df["Sector"] == sel_sector)

    # Seguro
    if "Seguro" in df.columns:
        seguros = ["Todos"] + sorted(df["Seguro"].dropna().unique().tolist())
        sel_seguro = st.selectbox("🛡️ Filtrar Seguro", seguros, index=0)
        if sel_seguro != "Todos":
            mask = mask & (df["Seguro"] == sel_seguro)

    # Doctor Tratante
    if "Doctor Tratante" in df.columns:
        docs = ["Todos"] + sorted(df["Doctor Tratante"].dropna().unique().tolist())
        sel_doc = st.selectbox("👨‍⚕️ Doctor Tratante", docs, index=0)
        if sel_doc != "Todos":
            mask = mask & (df["Doctor Tratante"] == sel_doc)

    # Lugar de Estudio
    if "Lugar_Estudio" in df.columns:
        lugares = ["Todos", "IRIBAS", "Externos"] + sorted(
            [l for l in df["Lugar_Estudio"].dropna().unique().tolist() if l != "IRIBAS"]
        )
        sel_lugar = st.selectbox("🏥 Lugar del Estudio", lugares, index=0)
        if sel_lugar == "IRIBAS":
            mask = mask & (df["Lugar_Estudio"] == "IRIBAS")
        elif sel_lugar == "Externos":
            mask = mask & (df["Lugar_Estudio"] != "IRIBAS")
        elif sel_lugar != "Todos":
            mask = mask & (df["Lugar_Estudio"] == sel_lugar)

    st.markdown("---")
    st.caption(f"Registros filtrados: **{mask.sum():,}** / {len(df):,}")

df_filtered = df.loc[mask]

# ── Empty-filter guard ───────────────────────────────────────────────────────
if df_filtered.empty:
    st.warning("⚠️ No hay datos para los filtros seleccionados. Ajusta los parámetros en la barra lateral.")
    st.stop()

# ── Generador de Informe PDF ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📄 Informe Gerencial")
    from utils_pdf import generar_informe_pdf
    pd_min_d = min_d if 'min_d' in locals() else None
    pd_max_d = max_d if 'max_d' in locals() else None
    if st.button("Descargar Informe PDF", icon="📊", use_container_width=True):
        with st.spinner("Generando reporte PDF..."):
            pdf_bytes = generar_informe_pdf(df_filtered, pd_min_d, pd_max_d)
            st.download_button(
                label="⬇️ Haz clic aquí para guardar tu PDF",
                data=pdf_bytes,
                file_name="informe_gerencial_iribas.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )



# ── TAB 1 — Evolución Histórica ─────────────────────────────────────────────
if tab1:
    st.markdown("### 📊 Dashboard General")
    st.markdown("### Volumen de Estudios e Ingresos a lo largo del Tiempo")
    if "Fecha" in df_filtered.columns and "TOTAL" in df_filtered.columns:
        df_t = (
            df_filtered
            .groupby(pd.Grouper(key="Fecha", freq="ME"))
            .agg(Estudios=("Fecha", "count"), Ingresos=("TOTAL", "sum"))
            .reset_index()
        )
        df_t["Periodo"] = df_t["Fecha"].dt.strftime("%Y-%m")

        fig_evo = go.Figure()
        fig_evo.add_trace(go.Scatter(
            x=df_t["Periodo"], y=df_t["Ingresos"],
            name="Ingresos (₲)",
            mode="lines+markers",
            line=dict(color="#58a6ff", width=3),
            marker=dict(size=8, symbol="circle"),
            fill="tozeroy",
            fillcolor="rgba(88,166,255,0.08)",
            hovertemplate="<b>%{x}</b><br>Ingresos: ₲%{y:,.0f}<extra></extra>",
        ))
        fig_evo.add_trace(go.Scatter(
            x=df_t["Periodo"], y=df_t["Estudios"],
            name="Estudios (vol)",
            mode="lines+markers",
            line=dict(color="#3fb950", width=3, dash="dot"),
            marker=dict(size=8, symbol="diamond"),
            yaxis="y2",
            hovertemplate="<b>%{x}</b><br>Estudios: %{y:,}<extra></extra>",
        ))
        fig_evo.update_layout(
            **PLOTLY_LAYOUT,
            title=None,
            yaxis=dict(title="Ingresos (₲)", gridcolor="rgba(48,54,61,0.4)"),
            yaxis2=dict(title="Volumen de Estudios", overlaying="y", side="right",
                        gridcolor="rgba(48,54,61,0.1)"),
            xaxis=dict(gridcolor="rgba(48,54,61,0.4)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            height=480,
        )
        st.plotly_chart(fig_evo, use_container_width=True, key="tab1_evo")
    else:
        st.info("Columnas 'Fecha' o 'TOTAL' no disponibles.")

# ── TAB 2 — Mapa de Calor Operativo ─────────────────────────────────────────
if tab2:
    st.markdown("### Picos de Saturación: Día de la Semana vs. Hora")

    if "Dia_Semana" in df_filtered.columns and "Hora_Num" in df_filtered.columns:
        # Per-sector selector inside the tab
        if "Sector" in df_filtered.columns:
            opciones_sector = ["— Todos los sectores —"] + sorted(
                df_filtered["Sector"].dropna().unique()
            )
            sector_heat = st.selectbox(
                "Filtrar mapa de calor por sector:",
                opciones_sector,
                key="heatmap_sector",
            )
            df_heat_src = (
                df_filtered
                if sector_heat == "— Todos los sectores —"
                else df_filtered[df_filtered["Sector"] == sector_heat]
            )
        else:
            df_heat_src = df_filtered

        df_h = (
            df_heat_src
            .groupby(["Dia_Semana", "Hora_Num"])
            .size()
            .reset_index(name="Volumen")
        )

        if not df_h.empty:
            orden = {
                "Lunes": 0, "Martes": 1, "Miércoles": 2,
                "Jueves": 3, "Viernes": 4, "Sábado": 5, "Domingo": 6,
            }
            mat = df_h.pivot(index="Dia_Semana", columns="Hora_Num", values="Volumen").fillna(0)
            mat = mat.reindex(sorted(mat.columns), axis=1)
            mat = mat.reindex(sorted(mat.index, key=lambda d: orden.get(d, 7)))

            fig_heat = px.imshow(
                mat, text_auto=True, aspect="auto",
                labels=dict(x="Hora del Día", y="Día", color="Estudios"),
                color_continuous_scale=HEATMAP_COLORS,
            )
            fig_heat.update_layout(
                **PLOTLY_LAYOUT, title=None, height=420, xaxis=dict(side="top"),
            )
            fig_heat.update_traces(
                hovertemplate="<b>%{y}</b> a las <b>%{x}h</b><br>Estudios: %{z}<extra></extra>"
            )
            st.plotly_chart(fig_heat, use_container_width=True, key="tab2_heat")
        else:
            st.info("Sin datos para el mapa de calor con los filtros actuales.")
    else:
        st.info("Columnas de Día/Hora no disponibles.")

# ── TAB 3 — Financiero ──────────────────────────────────────────────────────
if tab3:
    st.markdown("### Indicadores Clave de Rendimiento Financiero")

    total_rev = df_filtered["TOTAL"].sum() if "TOTAL" in df_filtered.columns else 0
    total_seg = df_filtered["Total a Pagar Seguro"].sum() if "Total a Pagar Seguro" in df_filtered.columns else 0
    total_pac = df_filtered["Total a Pagar Paciente"].sum() if "Total a Pagar Paciente" in df_filtered.columns else 0
    n_estudios = len(df_filtered)
    ticket_prom = total_rev / n_estudios if n_estudios else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💵 Ingreso Total", f"₲ {total_rev:,.0f}")
    k2.metric("🛡️ Pago Seguros", f"₲ {total_seg:,.0f}")
    k3.metric("👤 Pago Pacientes", f"₲ {total_pac:,.0f}")
    k4.metric("🎫 Ticket Promedio", f"₲ {ticket_prom:,.0f}")

    st.markdown("---")
    st.markdown("#### Seguros vs. Particulares")

    if "Tipo_Paciente" in df_filtered.columns:
        col_a, col_b = st.columns(2)

        # Volume donut
        df_vol = df_filtered["Tipo_Paciente"].value_counts().reset_index()
        df_vol.columns = ["Tipo", "Estudios"]
        fig_vol = px.pie(
            df_vol, names="Tipo", values="Estudios", hole=0.45,
            color="Tipo",
            color_discrete_map={"Seguro": "#58a6ff", "Particular": "#bc8cff"},
        )
        fig_vol.update_layout(**PLOTLY_LAYOUT, title="Volumen de Estudios", height=380,
                              showlegend=True,
                              legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"))
        fig_vol.update_traces(
            textinfo="percent+value", textfont_size=13,
            hovertemplate="<b>%{label}</b><br>Estudios: %{value:,}<br>%{percent}<extra></extra>",
        )
        col_a.plotly_chart(fig_vol, use_container_width=True, key="tab3_vol_donut")

        # Revenue donut
        df_fac = df_filtered.groupby("Tipo_Paciente")["TOTAL"].sum().reset_index()
        fig_fac = px.pie(
            df_fac, names="Tipo_Paciente", values="TOTAL", hole=0.45,
            color="Tipo_Paciente",
            color_discrete_map={"Seguro": "#3fb950", "Particular": "#f0883e"},
        )
        fig_fac.update_layout(**PLOTLY_LAYOUT, title="Facturación (₲)", height=380,
                              showlegend=True,
                              legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"))
        fig_fac.update_traces(
            textinfo="percent+value", textfont_size=13,
            texttemplate="%{percent}<br>₲%{value:,.0f}",
            hovertemplate="<b>%{label}</b><br>Facturación: ₲%{value:,.0f}<br>%{percent}<extra></extra>",
        )
        col_b.plotly_chart(fig_fac, use_container_width=True, key="tab3_fac_donut")

    # ── Análisis cruzado Seguro × Sector ─────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🔍 Análisis Seguro × Sector")

    if "Seguro" in df_filtered.columns and "Sector" in df_filtered.columns and "TOTAL" in df_filtered.columns:
        # Sector exclusion selector
        sectores_fin = sorted(df_filtered["Sector"].dropna().unique())
        sectores_visibles = st.multiselect(
            "Sectores a incluir en el análisis:",
            sectores_fin,
            default=sectores_fin,
            key="fin_sector_filter",
            help="Desmarca sectores para ocultarlos del análisis Seguro × Sector.",
        )

        if sectores_visibles:
            df_seg_sec = df_filtered[df_filtered["Sector"].isin(sectores_visibles)]

            # Grouped bar: volume by Sector, colored by Tipo_Paciente
            df_cross_vol = (
                df_seg_sec
                .groupby(["Sector", "Tipo_Paciente"])
                .size()
                .reset_index(name="Estudios")
            )
            fig_cross_vol = px.bar(
                df_cross_vol, x="Sector", y="Estudios", color="Tipo_Paciente",
                barmode="group", text="Estudios",
                color_discrete_map={"Seguro": "#58a6ff", "Particular": "#bc8cff"},
            )
            fig_cross_vol.update_traces(
                textposition="outside", textfont_size=11,
                hovertemplate="<b>%{x}</b><br>%{data.name}: %{y:,} estudios<extra></extra>",
            )
            fig_cross_vol.update_layout(
                **PLOTLY_LAYOUT, title="Volumen por Sector — Seguros vs. Particulares",
                height=420,
                xaxis=dict(title="", tickangle=-35),
                yaxis=dict(title="Estudios", gridcolor="rgba(48,54,61,0.4)"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig_cross_vol, use_container_width=True, key="tab3_cross_vol")

            # Grouped bar: billing by Sector, colored by Tipo_Paciente
            df_cross_fac = (
                df_seg_sec
                .groupby(["Sector", "Tipo_Paciente"])["TOTAL"]
                .sum()
                .reset_index(name="Facturacion")
            )
            fig_cross_fac = px.bar(
                df_cross_fac, x="Sector", y="Facturacion", color="Tipo_Paciente",
                barmode="group", text="Facturacion",
                color_discrete_map={"Seguro": "#3fb950", "Particular": "#f0883e"},
            )
            fig_cross_fac.update_traces(
                texttemplate="₲%{text:,.0f}", textposition="outside", textfont_size=10,
                hovertemplate="<b>%{x}</b><br>%{data.name}: ₲%{y:,.0f}<extra></extra>",
            )
            fig_cross_fac.update_layout(
                **PLOTLY_LAYOUT, title="Facturación por Sector — Seguros vs. Particulares",
                height=420,
                xaxis=dict(title="", tickangle=-35),
                yaxis=dict(title="Facturación (₲)", gridcolor="rgba(48,54,61,0.4)"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig_cross_fac, use_container_width=True, key="tab3_cross_fac")
        else:
            st.info("Selecciona al menos un sector para ver el análisis cruzado.")

    # ── Lugar de Estudio — IRIBAS vs Externos ────────────────────────────
    if "Lugar_Estudio" in df_filtered.columns and "TOTAL" in df_filtered.columns:
        st.markdown("---")
        st.markdown("### 🏥 Distribución por Lugar de Estudio")

        # KPIs: IRIBAS vs Externos
        df_iribas = df_filtered[df_filtered["Lugar_Estudio"] == "IRIBAS"]
        df_externo = df_filtered[df_filtered["Lugar_Estudio"] != "IRIBAS"]

        n_iribas = len(df_iribas)
        n_ext = len(df_externo)
        rev_iribas = df_iribas["TOTAL"].sum()
        rev_ext = df_externo["TOTAL"].sum()
        pct_iribas = n_iribas / max(len(df_filtered), 1) * 100

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("📊 Estudios IRIBAS", f"{n_iribas:,}", f"{pct_iribas:.1f}%")
        k2.metric("💰 Facturación IRIBAS", f"₲ {rev_iribas:,.0f}")
        k3.metric("📊 Estudios Externos", f"{n_ext:,}", f"{100 - pct_iribas:.1f}%")
        k4.metric("💰 Facturación Externos", f"₲ {rev_ext:,.0f}")

        col_lugar1, col_lugar2 = st.columns(2)

        with col_lugar1:
            # Pie chart: IRIBAS vs Externo
            df_pie_lugar = pd.DataFrame({
                "Lugar": ["IRIBAS", "Externos"],
                "Estudios": [n_iribas, n_ext],
            })
            fig_pie = px.pie(
                df_pie_lugar, values="Estudios", names="Lugar",
                color="Lugar",
                color_discrete_map={"IRIBAS": "#58a6ff", "Externos": "#f78166"},
                hole=0.4,
            )
            fig_pie.update_layout(**PLOTLY_LAYOUT, title="Volumen: IRIBAS vs Externos", height=380)
            st.plotly_chart(fig_pie, use_container_width=True, key="tab3_pie_lugar")

        with col_lugar2:
            # Pie chart by revenue
            df_pie_rev = pd.DataFrame({
                "Lugar": ["IRIBAS", "Externos"],
                "Facturación": [rev_iribas, rev_ext],
            })
            fig_pie_rev = px.pie(
                df_pie_rev, values="Facturación", names="Lugar",
                color="Lugar",
                color_discrete_map={"IRIBAS": "#58a6ff", "Externos": "#f78166"},
                hole=0.4,
            )
            fig_pie_rev.update_layout(**PLOTLY_LAYOUT, title="Facturación: IRIBAS vs Externos", height=380)
            st.plotly_chart(fig_pie_rev, use_container_width=True, key="tab3_pie_rev_lugar")

        # Bar chart: detail by external facility
        if n_ext > 0:
            df_ext_detail = (
                df_externo.groupby("Lugar_Estudio")
                .agg(Estudios=("TOTAL", "count"), Facturación=("TOTAL", "sum"))
                .sort_values("Estudios", ascending=False)
                .reset_index()
            )
            fig_ext = px.bar(
                df_ext_detail, x="Lugar_Estudio", y="Estudios",
                text="Estudios", color="Facturación",
                color_continuous_scale="Blues",
            )
            fig_ext.update_traces(
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Estudios: %{y:,}<br>Facturación: ₲ %{marker.color:,.0f}<extra></extra>",
            )
            fig_ext.update_layout(
                **PLOTLY_LAYOUT, title="Detalle por Centro Externo",
                height=420,
                xaxis=dict(title="Centro"),
                yaxis=dict(title="Estudios"),
            )
            st.plotly_chart(fig_ext, use_container_width=True, key="tab3_ext_detail")

# ── TAB 4 — Rendimiento por Sector ──────────────────────────────────────────
if tab4:
    st.markdown("### Rendimiento por Sector Médico")
    if "Sector" in df_filtered.columns and "TOTAL" in df_filtered.columns:
        # ── Sector selector inside the tab ───────────────────────────────
        sectores_tab4 = sorted(df_filtered["Sector"].dropna().unique())
        sel_sectores_tab4 = st.multiselect(
            "Selecciona los sectores a visualizar:",
            sectores_tab4,
            default=sectores_tab4,
            key="tab4_sector_select",
        )

        if not sel_sectores_tab4:
            st.info("Selecciona al menos un sector para visualizar.")
        else:
            df_s = (
                df_filtered[df_filtered["Sector"].isin(sel_sectores_tab4)]
                .groupby("Sector")
                .agg(Facturacion=("TOTAL", "sum"), Estudios=("TOTAL", "count"))
                .reset_index()
            )

            # ── Sub-tabs: Facturación vs Volumen ─────────────────────────
            sub_fac, sub_vol = st.tabs(["💰 Facturación por Sector", "📊 Volumen de Estudios por Sector"])

            with sub_fac:
                df_s_fac = df_s.sort_values("Facturacion", ascending=True)
                fig_sec = px.bar(
                    df_s_fac, y="Sector", x="Facturacion", orientation="h",
                    text="Facturacion", color="Facturacion",
                    color_continuous_scale=["#1a1e2e", "#58a6ff"],
                )
                fig_sec.update_traces(
                    texttemplate="₲%{text:,.0f}", textposition="outside", textfont_size=12,
                    hovertemplate="<b>%{y}</b><br>Facturación: ₲%{x:,.0f}<extra></extra>",
                )
                fig_sec.update_layout(
                    **PLOTLY_LAYOUT, title=None,
                    height=max(380, len(df_s_fac) * 50),
                    yaxis=dict(title=""),
                    xaxis=dict(title="Facturación (₲)", gridcolor="rgba(48,54,61,0.4)"),
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_sec, use_container_width=True, key="tab4_fac_sector")

            with sub_vol:
                df_s_vol = df_s.sort_values("Estudios", ascending=True)
                fig_vol_sec = px.bar(
                    df_s_vol, y="Sector", x="Estudios", orientation="h",
                    text="Estudios", color="Estudios",
                    color_continuous_scale=["#1a1e2e", "#3fb950"],
                )
                fig_vol_sec.update_traces(
                    texttemplate="%{text:,}", textposition="outside", textfont_size=12,
                    hovertemplate="<b>%{y}</b><br>Estudios: %{x:,}<extra></extra>",
                )
                fig_vol_sec.update_layout(
                    **PLOTLY_LAYOUT, title=None,
                    height=max(380, len(df_s_vol) * 50),
                    yaxis=dict(title=""),
                    xaxis=dict(title="Volumen de Estudios", gridcolor="rgba(48,54,61,0.4)"),
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_vol_sec, use_container_width=True, key="tab4_vol_sector")

            # ── Summary table ────────────────────────────────────────────
            st.markdown("#### Resumen numérico")
            df_s_display = df_s.sort_values("Facturacion", ascending=False).copy()
            df_s_display["Ticket Prom."] = (df_s_display["Facturacion"] / df_s_display["Estudios"]).apply(lambda v: f"₲ {v:,.0f}")
            df_s_display["Facturacion"] = df_s_display["Facturacion"].apply(lambda v: f"₲ {v:,.0f}")
            st.dataframe(df_s_display[["Sector", "Estudios", "Facturacion", "Ticket Prom."]],
                          use_container_width=True, hide_index=True)
    else:
        st.info("Columnas 'Sector' o 'TOTAL' no disponibles.")

# ── TAB 5 — Red de Derivación ───────────────────────────────────────────────
if tab5:
    st.markdown("### 🩺 Médicos Tratantes — Top 15 Volumen y Facturación")
    if "Doctor Tratante" in df_filtered.columns and "TOTAL" in df_filtered.columns:
        df_d = (
            df_filtered
            .groupby("Doctor Tratante")
            .agg(Derivaciones=("Doctor Tratante", "count"), Facturacion=("TOTAL", "sum"))
            .reset_index()
            .sort_values("Derivaciones", ascending=False)
            .head(15)
        )

        st.markdown("#### 📋 Tabla de Derivaciones")
        df_d_show = df_d.copy()
        df_d_show["Facturacion_fmt"] = df_d_show["Facturacion"].apply(lambda v: f"₲ {v:,.0f}")
        st.dataframe(
            df_d_show[["Doctor Tratante", "Derivaciones", "Facturacion_fmt"]].rename(
                columns={"Facturacion_fmt": "Facturación"}
            ),
            use_container_width=True, hide_index=True,
        )

        st.markdown("---")
        st.markdown("#### 📊 Visualización")

        df_d_chart = df_d.sort_values("Facturacion", ascending=True)
        fig_doc = px.bar(
            df_d_chart, y="Doctor Tratante", x="Facturacion", orientation="h",
            color="Derivaciones",
            color_continuous_scale=["#1a1e2e", "#3fb950"],
            text="Facturacion",
        )
        fig_doc.update_traces(
            texttemplate="₲%{text:,.0f}", textposition="outside", textfont_size=11,
            hovertemplate="<b>%{y}</b><br>Derivaciones: %{marker.color:,}<br>Facturación: ₲%{x:,.0f}<extra></extra>",
        )
        fig_doc.update_layout(
            **PLOTLY_LAYOUT, title=None,
            height=max(400, len(df_d_chart) * 38),
            yaxis=dict(title=""),
            xaxis=dict(title="Facturación (₲)", gridcolor="rgba(48,54,61,0.4)"),
            coloraxis_colorbar=dict(title="Derivaciones"),
        )
        st.plotly_chart(fig_doc, use_container_width=True, key="tab5_doc")
    else:
        st.info("Columnas 'Doctor Tratante' o 'TOTAL' no disponibles.")

# ── TAB 6 — Radiólogos Informantes (KPI) ────────────────────────────────────
if tab6:
    st.markdown("### 🔬 KPI de Radiólogos Informantes")
    st.markdown(
        "Evaluación del rendimiento por volumen, tipo de estudio y **puntaje de dificultad ponderado**."
    )

    has_informante = "Doctor Informante" in df_filtered.columns
    has_puntaje = "Puntaje_Dificultad" in df_filtered.columns
    has_sector = "Sector" in df_filtered.columns

    if has_informante and has_puntaje:
        # Filter out blank / NO ASIGNADO informants
        df_rad = df_filtered[
            df_filtered["Doctor Informante"].notna()
            & (~df_filtered["Doctor Informante"].isin(["NO ASIGNADO", ""]))
        ].copy()

        if df_rad.empty:
            st.info("No hay registros con Doctor Informante asignado.")
        else:
            # ── Pre-compute ALL aggregations once (cached) ───────────────
            df_ranking = compute_ranking(df_rad)
            df_detail_all = compute_detail_all(df_rad) if has_sector else None

            # ── Difficulty legend ─────────────────────────────────────────
            with st.expander("📖 Tabla de Puntajes de Dificultad por Tipo de Estudio"):
                diff_data = {**DIFICULTAD_SECTOR, "Otros": DIFICULTAD_DEFAULT}
                df_diff = pd.DataFrame(
                    [(k, v) for k, v in diff_data.items()],
                    columns=["Sector / Tipo", "Puntaje"],
                ).sort_values("Puntaje", ascending=False)
                st.dataframe(df_diff, use_container_width=True, hide_index=True)

            # ── Global KPIs ──────────────────────────────────────────────
            n_radiologos = len(df_ranking)
            total_estudios_rad = df_ranking["Estudios"].sum()
            total_fac_rad = df_ranking["Facturacion"].sum() if "Facturacion" in df_ranking.columns else 0
            total_puntaje = df_ranking["Puntaje_Total"].sum()
            prom_puntaje = total_puntaje / n_radiologos if n_radiologos else 0

            gk1, gk2, gk3, gk4, gk5 = st.columns(5)
            gk1.metric("👨‍⚕️ Radiólogos Activos", f"{n_radiologos}")
            gk2.metric("📋 Estudios", f"{total_estudios_rad:,}")
            gk3.metric("⚡ Puntaje Total", f"{total_puntaje:,.1f}")
            gk4.metric("📊 Dificultad Prom.", f"{prom_puntaje:,.1f}")
            gk5.metric("💵 Facturación Aportada", f"₲ {total_fac_rad:,.0f}")

            st.markdown("---")

            # ── Sub-tabs inside Tab 6 ────────────────────────────────────
            st6_ranking, st6_detalle, st6_evol = st.tabs([
                "🏆 Ranking General",
                "📋 Detalle por Radiólogo",
                "📈 Evolución Temporal",
            ])

            # ── 6A: RANKING GENERAL ──────────────────────────────────────
            with st6_ranking:
                st.markdown("#### Ranking de Radiólogos por Puntaje Ponderado")

                df_rank_chart = df_ranking.sort_values("Puntaje_Total", ascending=True)
                fig_rank = px.bar(
                    df_rank_chart, y="Doctor Informante", x="Puntaje_Total",
                    orientation="h", text="Puntaje_Total",
                    color="Puntaje_Prom",
                    color_continuous_scale=["#1a1e2e", "#f0883e", "#ff7b72"],
                )
                fig_rank.update_traces(
                    texttemplate="%{text:,.0f} pts", textposition="outside", textfont_size=11,
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Puntaje Total: %{x:,.1f}<br>"
                        "Dificultad Prom: %{marker.color:.2f}<extra></extra>"
                    ),
                )
                fig_rank.update_layout(
                    **PLOTLY_LAYOUT, title=None,
                    height=max(450, len(df_rank_chart) * 30),
                    yaxis=dict(title=""),
                    xaxis=dict(title="Puntaje Ponderado Total", gridcolor="rgba(48,54,61,0.4)"),
                    coloraxis_colorbar=dict(title="Dif. Prom."),
                )
                st.plotly_chart(fig_rank, use_container_width=True, key="rad_rank_pts")

                st.markdown("#### Volumen de Estudios Informados")
                df_rank_vol = df_ranking.sort_values("Estudios", ascending=True)
                fig_rank_vol = px.bar(
                    df_rank_vol, y="Doctor Informante", x="Estudios",
                    orientation="h", text="Estudios",
                    color="Estudios",
                    color_continuous_scale=["#1a1e2e", "#58a6ff"],
                )
                fig_rank_vol.update_traces(
                    texttemplate="%{text:,}", textposition="outside", textfont_size=11,
                    hovertemplate="<b>%{y}</b><br>Estudios: %{x:,}<extra></extra>",
                )
                fig_rank_vol.update_layout(
                    **PLOTLY_LAYOUT, title=None,
                    height=max(450, len(df_rank_vol) * 30),
                    yaxis=dict(title=""),
                    xaxis=dict(title="Cantidad de Estudios", gridcolor="rgba(48,54,61,0.4)"),
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_rank_vol, use_container_width=True, key="rad_rank_vol")

                if "Facturacion" in df_ranking.columns:
                    st.markdown("#### Dinero Aportado (Facturación por Radiólogo)")
                    df_rank_fac = df_ranking.sort_values("Facturacion", ascending=True)
                    fig_rank_fac = px.bar(
                        df_rank_fac, y="Doctor Informante", x="Facturacion",
                        orientation="h", text="Facturacion",
                        color="Facturacion",
                        color_continuous_scale=["#1a1e2e", "#3fb950"],
                    )
                    fig_rank_fac.update_traces(
                        texttemplate="₲%{text:,.0f}", textposition="outside", textfont_size=11,
                        hovertemplate="<b>%{y}</b><br>Facturación: ₲%{x:,.0f}<extra></extra>",
                    )
                    fig_rank_fac.update_layout(
                        **PLOTLY_LAYOUT, title=None,
                        height=max(450, len(df_rank_fac) * 30),
                        yaxis=dict(title=""),
                        xaxis=dict(title="Facturación (₲)", gridcolor="rgba(48,54,61,0.4)"),
                        coloraxis_showscale=False,
                    )
                    st.plotly_chart(fig_rank_fac, use_container_width=True, key="rad_rank_fac")

                st.markdown("#### Tabla Resumen")
                df_rank_tbl = df_ranking.copy()
                df_rank_tbl["Puntaje_Total"] = df_rank_tbl["Puntaje_Total"].apply(lambda v: f"{v:,.1f}")
                df_rank_tbl["Puntaje_Prom"] = df_rank_tbl["Puntaje_Prom"].apply(lambda v: f"{v:.2f}")
                if "Facturacion" in df_rank_tbl.columns:
                    df_rank_tbl["Facturacion"] = df_rank_tbl["Facturacion"].apply(lambda v: f"₲ {v:,.0f}")
                
                st.dataframe(
                    df_rank_tbl.rename(columns={
                        "Doctor Informante": "Radiólogo",
                        "Puntaje_Total": "Puntaje Total",
                        "Puntaje_Prom": "Dificultad Prom.",
                        "Facturacion": "Facturación",
                    }),
                    use_container_width=True, hide_index=True,
                )

            # ── 6B: DETALLE POR RADIÓLOGO (uses pre-computed data) ───────
            with st6_detalle:
                st.markdown("#### Desglose por Tipo de Estudio")

                radiologos = sorted(df_ranking["Doctor Informante"].tolist())
                sel_radiologo = st.selectbox(
                    "Selecciona un radiólogo:", radiologos, key="rad_detail"
                )

                # Get individual stats from pre-computed ranking
                row_rank = df_ranking[df_ranking["Doctor Informante"] == sel_radiologo]
                ind_estudios = int(row_rank["Estudios"].iloc[0]) if len(row_rank) else 0
                ind_puntaje = float(row_rank["Puntaje_Total"].iloc[0]) if len(row_rank) else 0
                ind_prom = float(row_rank["Puntaje_Prom"].iloc[0]) if len(row_rank) else 0

                ik1, ik2, ik3 = st.columns(3)
                ik1.metric("📋 Estudios", f"{ind_estudios:,}")
                ik2.metric("⚡ Puntaje Total", f"{ind_puntaje:,.1f}")
                ik3.metric("📊 Dificultad Promedio", f"{ind_prom:.2f}")

                if df_detail_all is not None:
                    # Filter pre-computed detail for this radiologist
                    df_tipo = (
                        df_detail_all[df_detail_all["Doctor Informante"] == sel_radiologo]
                        .sort_values("Puntaje", ascending=True)
                    )

                    if not df_tipo.empty:
                        col_det_a, col_det_b = st.columns(2)

                        fig_tipo_vol = px.bar(
                            df_tipo, y="Sector", x="Estudios", orientation="h",
                            text="Estudios", color="Estudios",
                            color_continuous_scale=["#1a1e2e", "#58a6ff"],
                        )
                        fig_tipo_vol.update_traces(
                            texttemplate="%{text:,}", textposition="outside", textfont_size=11,
                            hovertemplate="<b>%{y}</b><br>Estudios: %{x:,}<extra></extra>",
                        )
                        fig_tipo_vol.update_layout(
                            **PLOTLY_LAYOUT, title="Volumen por Tipo",
                            height=max(300, len(df_tipo) * 40),
                            yaxis=dict(title=""), coloraxis_showscale=False,
                        )
                        col_det_a.plotly_chart(fig_tipo_vol, use_container_width=True, key="rad_det_vol")

                        fig_tipo_pts = px.bar(
                            df_tipo, y="Sector", x="Puntaje", orientation="h",
                            text="Puntaje", color="Puntaje",
                            color_continuous_scale=["#1a1e2e", "#f0883e"],
                        )
                        fig_tipo_pts.update_traces(
                            texttemplate="%{text:,.0f} pts", textposition="outside", textfont_size=11,
                            hovertemplate="<b>%{y}</b><br>Puntaje: %{x:,.1f}<extra></extra>",
                        )
                        fig_tipo_pts.update_layout(
                            **PLOTLY_LAYOUT, title="Puntaje Ponderado por Tipo",
                            height=max(300, len(df_tipo) * 40),
                            yaxis=dict(title=""), coloraxis_showscale=False,
                        )
                        col_det_b.plotly_chart(fig_tipo_pts, use_container_width=True, key="rad_det_pts")

                        fig_mix = px.pie(
                            df_tipo, names="Sector", values="Estudios", hole=0.4,
                        )
                        fig_mix.update_layout(
                            **PLOTLY_LAYOUT, title=f"Mix de Estudios — {sel_radiologo}",
                            height=380, showlegend=True,
                            legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
                        )
                        fig_mix.update_traces(
                            textinfo="percent+label", textfont_size=11,
                            hovertemplate="<b>%{label}</b><br>%{value:,} estudios<br>%{percent}<extra></extra>",
                        )
                        st.plotly_chart(fig_mix, use_container_width=True, key="rad_det_mix")

            # ── 6C: EVOLUCIÓN TEMPORAL (uses pre-computed data) ──────────
            with st6_evol:
                st.markdown("#### Evolución Temporal del Puntaje Ponderado")

                if "Fecha" in df_rad.columns and df_rad["Fecha"].notna().any():
                    vista_evol = st.radio(
                        "Vista:", ["General del Centro", "Individual por Radiólogo"],
                        horizontal=True, key="rad_evol_mode",
                    )

                    if vista_evol == "General del Centro":
                        df_evol_gen = compute_evolution_general(df_rad)

                        fig_evol_g = go.Figure()
                        fig_evol_g.add_trace(go.Scatter(
                            x=df_evol_gen["Periodo"], y=df_evol_gen["Puntaje"],
                            name="Puntaje Ponderado",
                            mode="lines+markers",
                            line=dict(color="#f0883e", width=3),
                            marker=dict(size=8),
                            fill="tozeroy", fillcolor="rgba(240,136,62,0.08)",
                            hovertemplate="<b>%{x}</b><br>Puntaje: %{y:,.0f}<extra></extra>",
                        ))
                        fig_evol_g.add_trace(go.Scatter(
                            x=df_evol_gen["Periodo"], y=df_evol_gen["Estudios"],
                            name="Estudios (vol)",
                            mode="lines+markers",
                            line=dict(color="#58a6ff", width=3, dash="dot"),
                            marker=dict(size=8, symbol="diamond"),
                            yaxis="y2",
                            hovertemplate="<b>%{x}</b><br>Estudios: %{y:,}<extra></extra>",
                        ))
                        fig_evol_g.update_layout(
                            **PLOTLY_LAYOUT, title="Evolución General del Centro",
                            yaxis=dict(title="Puntaje Ponderado", gridcolor="rgba(48,54,61,0.4)"),
                            yaxis2=dict(title="Estudios", overlaying="y", side="right",
                                        gridcolor="rgba(48,54,61,0.1)"),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                        xanchor="center", x=0.5),
                            height=480,
                        )
                        st.plotly_chart(fig_evol_g, use_container_width=True, key="rad_evol_gen")

                    else:
                        # Pre-compute all individual evolution once
                        df_evol_all = compute_evolution_individual(df_rad)

                        radiologos_evol = sorted(df_evol_all["Doctor Informante"].unique())
                        sel_rad_evol = st.multiselect(
                            "Selecciona radiólogos a comparar:",
                            radiologos_evol,
                            default=radiologos_evol[:5],
                            key="rad_evol_select",
                        )

                        if sel_rad_evol:
                            df_evol_sel = df_evol_all[df_evol_all["Doctor Informante"].isin(sel_rad_evol)]

                            fig_evol_i = px.line(
                                df_evol_sel, x="Periodo", y="Puntaje",
                                color="Doctor Informante", markers=True,
                            )
                            fig_evol_i.update_layout(
                                **PLOTLY_LAYOUT,
                                title="Evolución Individual — Puntaje Ponderado",
                                yaxis=dict(title="Puntaje Ponderado", gridcolor="rgba(48,54,61,0.4)"),
                                legend=dict(orientation="h", yanchor="bottom", y=-0.25,
                                            xanchor="center", x=0.5),
                                height=500,
                            )
                            fig_evol_i.update_traces(
                                hovertemplate="<b>%{data.name}</b><br>%{x}<br>Puntaje: %{y:,.0f}<extra></extra>",
                            )
                            st.plotly_chart(fig_evol_i, use_container_width=True, key="rad_evol_ind_pts")

                            fig_evol_iv = px.line(
                                df_evol_sel, x="Periodo", y="Estudios",
                                color="Doctor Informante", markers=True,
                            )
                            fig_evol_iv.update_layout(
                                **PLOTLY_LAYOUT,
                                title="Evolución Individual — Volumen",
                                yaxis=dict(title="Estudios", gridcolor="rgba(48,54,61,0.4)"),
                                legend=dict(orientation="h", yanchor="bottom", y=-0.25,
                                            xanchor="center", x=0.5),
                                height=500,
                            )
                            st.plotly_chart(fig_evol_iv, use_container_width=True, key="rad_evol_ind_vol")
                        else:
                            st.info("Selecciona al menos un radiólogo.")
                else:
                    st.info("Columna 'Fecha' no disponible para evolución temporal.")
    else:
        st.info("Columnas 'Doctor Informante' o 'Sector' no disponibles para el análisis.")

# ── TAB 7 — Ranking de Seguros ─────────────────────────────────────────────
if tab7:
    st.markdown("### 🛡️ Ranking de Seguros Médicos")
    st.markdown("Análisis de facturación, volumen y composición por aseguradora.")

    if "Seguro" in df_filtered.columns and "TOTAL" in df_filtered.columns:
        # ── Filter to exclude specific insurers from ranking ────────────
        seguros_disponibles = sorted(df_filtered["Seguro"].dropna().unique())
        seguros_ranking = st.multiselect(
            "Seguros a incluir en el ranking:",
            seguros_disponibles,
            default=seguros_disponibles,
            key="tab7_seguro_filter",
            help="Desmarca seguros para excluirlos del análisis.",
        )

        if not seguros_ranking:
            st.info("Selecciona al menos un seguro para ver el ranking.")
        else:
            df_seg = df_filtered[df_filtered["Seguro"].isin(seguros_ranking)]

            # ── Pre-compute aggregations ───────────────────────────────
            df_seg_agg = (
                df_seg.groupby("Seguro")
                .agg(
                    Facturacion=("TOTAL", "sum"),
                    Estudios=("TOTAL", "count"),
                    Pago_Seguro=("Total a Pagar Seguro", "sum") if "Total a Pagar Seguro" in df_seg.columns else ("TOTAL", "count"),
                    Pago_Paciente=("Total a Pagar Paciente", "sum") if "Total a Pagar Paciente" in df_seg.columns else ("TOTAL", "count"),
                )
                .reset_index()
            )
            df_seg_agg["Ticket_Prom"] = df_seg_agg["Facturacion"] / df_seg_agg["Estudios"]
            df_seg_agg = df_seg_agg.sort_values("Facturacion", ascending=False)

            # ── Global KPIs ────────────────────────────────────────────
            n_seguros = len(df_seg_agg)
            total_fac = df_seg_agg["Facturacion"].sum()
            total_est = df_seg_agg["Estudios"].sum()
            top_seguro = df_seg_agg.iloc[0]["Seguro"] if len(df_seg_agg) > 0 else "-"

            sk1, sk2, sk3, sk4 = st.columns(4)
            sk1.metric("🛡️ Seguros Activos", f"{n_seguros}")
            sk2.metric("💵 Facturación Total", f"₲ {total_fac:,.0f}")
            sk3.metric("📋 Total Estudios", f"{total_est:,}")
            sk4.metric("🏆 Líder", f"{top_seguro}")

            st.markdown("---")

            # ── Sub-tabs ──────────────────────────────────────────────
            st7_fac, st7_vol, st7_detalle = st.tabs([
                "💰 Facturación por Seguro",
                "📊 Volumen por Seguro",
                "🔍 Detalle por Seguro",
            ])

            # ── 7A: RANKING FACTURACIÓN ────────────────────────────────
            with st7_fac:
                st.markdown("#### Ranking por Facturación")
                df_fac_chart = df_seg_agg.sort_values("Facturacion", ascending=True)
                fig_seg_fac = px.bar(
                    df_fac_chart, y="Seguro", x="Facturacion", orientation="h",
                    text="Facturacion", color="Facturacion",
                    color_continuous_scale=["#1a1e2e", "#3fb950"],
                )
                fig_seg_fac.update_traces(
                    texttemplate="₲%{text:,.0f}", textposition="outside", textfont_size=11,
                    hovertemplate="<b>%{y}</b><br>Facturación: ₲%{x:,.0f}<extra></extra>",
                )
                fig_seg_fac.update_layout(
                    **PLOTLY_LAYOUT, title=None,
                    height=max(400, len(df_fac_chart) * 40),
                    yaxis=dict(title=""),
                    xaxis=dict(title="Facturación (₲)", gridcolor="rgba(48,54,61,0.4)"),
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_seg_fac, use_container_width=True, key="tab7_fac_bar")

                # Donut share
                fig_seg_donut = px.pie(
                    df_seg_agg, names="Seguro", values="Facturacion", hole=0.4,
                )
                fig_seg_donut.update_layout(
                    **PLOTLY_LAYOUT, title="Participación en Facturación",
                    height=420, showlegend=True,
                    legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
                )
                fig_seg_donut.update_traces(
                    textinfo="percent+label", textfont_size=10,
                    hovertemplate="<b>%{label}</b><br>₲%{value:,.0f}<br>%{percent}<extra></extra>",
                )
                st.plotly_chart(fig_seg_donut, use_container_width=True, key="tab7_fac_donut")

            # ── 7B: RANKING VOLUMEN ───────────────────────────────────
            with st7_vol:
                st.markdown("#### Ranking por Volumen de Estudios")
                df_vol_chart = df_seg_agg.sort_values("Estudios", ascending=True)
                fig_seg_vol = px.bar(
                    df_vol_chart, y="Seguro", x="Estudios", orientation="h",
                    text="Estudios", color="Estudios",
                    color_continuous_scale=["#1a1e2e", "#58a6ff"],
                )
                fig_seg_vol.update_traces(
                    texttemplate="%{text:,}", textposition="outside", textfont_size=11,
                    hovertemplate="<b>%{y}</b><br>Estudios: %{x:,}<extra></extra>",
                )
                fig_seg_vol.update_layout(
                    **PLOTLY_LAYOUT, title=None,
                    height=max(400, len(df_vol_chart) * 40),
                    yaxis=dict(title=""),
                    xaxis=dict(title="Cantidad de Estudios", gridcolor="rgba(48,54,61,0.4)"),
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_seg_vol, use_container_width=True, key="tab7_vol_bar")

                # Ticket promedio comparison
                st.markdown("#### Ticket Promedio por Seguro")
                df_ticket_chart = df_seg_agg.sort_values("Ticket_Prom", ascending=True)
                fig_ticket = px.bar(
                    df_ticket_chart, y="Seguro", x="Ticket_Prom", orientation="h",
                    text="Ticket_Prom", color="Ticket_Prom",
                    color_continuous_scale=["#1a1e2e", "#f0883e"],
                )
                fig_ticket.update_traces(
                    texttemplate="₲%{text:,.0f}", textposition="outside", textfont_size=11,
                    hovertemplate="<b>%{y}</b><br>Ticket Prom: ₲%{x:,.0f}<extra></extra>",
                )
                fig_ticket.update_layout(
                    **PLOTLY_LAYOUT, title=None,
                    height=max(400, len(df_ticket_chart) * 40),
                    yaxis=dict(title=""),
                    xaxis=dict(title="Ticket Promedio (₲)", gridcolor="rgba(48,54,61,0.4)"),
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_ticket, use_container_width=True, key="tab7_ticket_bar")

            # ── 7C: DETALLE POR SEGURO ────────────────────────────────
            with st7_detalle:
                st.markdown("#### Desglose por Seguro")

                sel_seguro_det = st.selectbox(
                    "Selecciona un seguro:",
                    df_seg_agg["Seguro"].tolist(),
                    key="tab7_seg_detail",
                )

                df_seg_ind = df_seg[df_seg["Seguro"] == sel_seguro_det]
                row_seg = df_seg_agg[df_seg_agg["Seguro"] == sel_seguro_det]

                # KPIs for selected insurer
                sd1, sd2, sd3 = st.columns(3)
                sd1.metric("📋 Estudios", f"{int(row_seg['Estudios'].iloc[0]):,}" if len(row_seg) else "0")
                sd2.metric("💵 Facturación", f"₲ {float(row_seg['Facturacion'].iloc[0]):,.0f}" if len(row_seg) else "₲ 0")
                sd3.metric("🎫 Ticket Prom.", f"₲ {float(row_seg['Ticket_Prom'].iloc[0]):,.0f}" if len(row_seg) else "₲ 0")

                # Sector breakdown for this insurer
                if "Sector" in df_seg_ind.columns:
                    df_seg_sector = (
                        df_seg_ind.groupby("Sector")
                        .agg(Estudios=("Sector", "count"), Facturacion=("TOTAL", "sum"))
                        .reset_index()
                        .sort_values("Facturacion", ascending=True)
                    )

                    col_seg_a, col_seg_b = st.columns(2)

                    fig_seg_sec_vol = px.bar(
                        df_seg_sector, y="Sector", x="Estudios", orientation="h",
                        text="Estudios", color="Estudios",
                        color_continuous_scale=["#1a1e2e", "#58a6ff"],
                    )
                    fig_seg_sec_vol.update_traces(
                        texttemplate="%{text:,}", textposition="outside", textfont_size=11,
                        hovertemplate="<b>%{y}</b><br>Estudios: %{x:,}<extra></extra>",
                    )
                    fig_seg_sec_vol.update_layout(
                        **PLOTLY_LAYOUT, title="Volumen por Sector",
                        height=max(300, len(df_seg_sector) * 38),
                        yaxis=dict(title=""), coloraxis_showscale=False,
                    )
                    col_seg_a.plotly_chart(fig_seg_sec_vol, use_container_width=True, key="tab7_det_vol")

                    fig_seg_sec_fac = px.bar(
                        df_seg_sector, y="Sector", x="Facturacion", orientation="h",
                        text="Facturacion", color="Facturacion",
                        color_continuous_scale=["#1a1e2e", "#3fb950"],
                    )
                    fig_seg_sec_fac.update_traces(
                        texttemplate="₲%{text:,.0f}", textposition="outside", textfont_size=11,
                        hovertemplate="<b>%{y}</b><br>Facturación: ₲%{x:,.0f}<extra></extra>",
                    )
                    fig_seg_sec_fac.update_layout(
                        **PLOTLY_LAYOUT, title="Facturación por Sector",
                        height=max(300, len(df_seg_sector) * 38),
                        yaxis=dict(title=""), coloraxis_showscale=False,
                    )
                    col_seg_b.plotly_chart(fig_seg_sec_fac, use_container_width=True, key="tab7_det_fac")

                    # Mix pie
                    fig_seg_mix = px.pie(
                        df_seg_sector, names="Sector", values="Estudios", hole=0.4,
                    )
                    fig_seg_mix.update_layout(
                        **PLOTLY_LAYOUT, title=f"Mix de Estudios — {sel_seguro_det}",
                        height=380, showlegend=True,
                        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
                    )
                    fig_seg_mix.update_traces(
                        textinfo="percent+label", textfont_size=10,
                        hovertemplate="<b>%{label}</b><br>%{value:,} estudios<br>%{percent}<extra></extra>",
                    )
                    st.plotly_chart(fig_seg_mix, use_container_width=True, key="tab7_det_mix")

            # ── Tabla resumen general ──────────────────────────────────
            st.markdown("---")
            st.markdown("#### Tabla Resumen de Seguros")
            df_seg_tbl = df_seg_agg.copy()
            df_seg_tbl["Facturacion"] = df_seg_tbl["Facturacion"].apply(lambda v: f"₲ {v:,.0f}")
            df_seg_tbl["Ticket_Prom"] = df_seg_tbl["Ticket_Prom"].apply(lambda v: f"₲ {v:,.0f}")
            if "Pago_Seguro" in df_seg_tbl.columns:
                df_seg_tbl["Pago_Seguro"] = df_seg_tbl["Pago_Seguro"].apply(lambda v: f"₲ {v:,.0f}")
            if "Pago_Paciente" in df_seg_tbl.columns:
                df_seg_tbl["Pago_Paciente"] = df_seg_tbl["Pago_Paciente"].apply(lambda v: f"₲ {v:,.0f}")
            st.dataframe(
                df_seg_tbl.rename(columns={
                    "Ticket_Prom": "Ticket Promedio",
                    "Pago_Seguro": "Pago Seguro",
                    "Pago_Paciente": "Pago Paciente",
                    "Facturacion": "Facturación",
                }),
                use_container_width=True, hide_index=True,
            )
    else:
        st.info("Columnas 'Seguro' o 'TOTAL' no disponibles.")

# ── TAB 12 — Agentes de Fichaje ────────────────────────────────────────────
if tab12:
    st.markdown("### 📝 Agentes de Fichaje")
    st.markdown("Análisis de productividad de los usuarios que registran estudios en el sistema. Solo incluye registros con agente asignado (datos 2026+).")

    has_agente = "Agente" in df_filtered.columns
    if has_agente:
        df_ag = df_filtered[df_filtered["Agente"].notna()].copy()
    else:
        df_ag = pd.DataFrame()

    if df_ag.empty:
        st.warning("No hay datos de agentes de fichaje en el período seleccionado. Esta información está disponible solo para datos de 2026 en adelante.")
    else:
        n_agentes = df_ag["Agente"].nunique()
        n_fichas = len(df_ag)
        rev_total = df_ag["TOTAL"].sum() if "TOTAL" in df_ag.columns else 0

        k1, k2, k3 = st.columns(3)
        k1.metric("👥 Agentes Activos", f"{n_agentes}")
        k2.metric("📋 Estudios Fichados", f"{n_fichas:,}")
        k3.metric("💰 Facturación Total", f"₲ {rev_total:,.0f}")

        # ── Filter by sector inside this tab ──
        col_filt1, col_filt2 = st.columns(2)
        with col_filt1:
            if "Sector" in df_ag.columns:
                sectores_ag = ["Todos"] + sorted(df_ag["Sector"].dropna().unique().tolist())
                sel_sector_ag = st.selectbox("Filtrar por Sector", sectores_ag, key="ag_sector")
                if sel_sector_ag != "Todos":
                    df_ag = df_ag[df_ag["Sector"] == sel_sector_ag]
        with col_filt2:
            if "Lugar_Estudio" in df_ag.columns:
                lugares_ag = ["Todos", "IRIBAS", "Externos"]
                sel_lugar_ag = st.selectbox("Filtrar por Lugar", lugares_ag, key="ag_lugar")
                if sel_lugar_ag == "IRIBAS":
                    df_ag = df_ag[df_ag["Lugar_Estudio"] == "IRIBAS"]
                elif sel_lugar_ag == "Externos":
                    df_ag = df_ag[df_ag["Lugar_Estudio"] != "IRIBAS"]

        st.markdown("---")

        # ── 1. Volume by Agent ──
        df_vol_ag = (
            df_ag.groupby("Agente")
            .size()
            .reset_index(name="Estudios")
            .sort_values("Estudios", ascending=False)
        )

        fig_vol = px.bar(
            df_vol_ag, x="Agente", y="Estudios", text="Estudios",
            color="Estudios", color_continuous_scale="Blues",
        )
        fig_vol.update_traces(
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Estudios: %{y:,}<extra></extra>",
        )
        fig_vol.update_layout(
            **PLOTLY_LAYOUT,
            title="Volumen de Estudios por Agente",
            height=450,
            xaxis=dict(title="", tickangle=-35),
            yaxis=dict(title="Estudios"),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_vol, use_container_width=True, key="ag_vol")

        # ── 2. IRIBAS vs Externo by Agent ──
        if "Es_Externo" in df_ag.columns:
            col_a, col_b = st.columns(2)
            with col_a:
                df_lugar_ag = (
                    df_ag.groupby(["Agente", "Es_Externo"])
                    .size()
                    .reset_index(name="Estudios")
                )
                fig_lugar = px.bar(
                    df_lugar_ag, x="Agente", y="Estudios", color="Es_Externo",
                    barmode="stack", text="Estudios",
                    color_discrete_map={"IRIBAS": "#58a6ff", "Externo": "#f78166"},
                )
                fig_lugar.update_traces(textposition="inside", textfont_size=10)
                fig_lugar.update_layout(
                    **PLOTLY_LAYOUT,
                    title="IRIBAS vs Externo por Agente",
                    height=420,
                    xaxis=dict(title="", tickangle=-35),
                    yaxis=dict(title="Estudios"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                )
                st.plotly_chart(fig_lugar, use_container_width=True, key="ag_lugar_chart")

            with col_b:
                # Revenue by Agent
                if "TOTAL" in df_ag.columns:
                    df_rev_ag = (
                        df_ag.groupby("Agente")["TOTAL"]
                        .sum()
                        .sort_values(ascending=True)
                        .reset_index()
                    )
                    fig_rev = px.bar(
                        df_rev_ag, y="Agente", x="TOTAL", orientation="h",
                        text=df_rev_ag["TOTAL"].apply(lambda x: f"₲ {x:,.0f}"),
                        color="TOTAL", color_continuous_scale="Greens",
                    )
                    fig_rev.update_traces(textposition="outside", textfont_size=10)
                    fig_rev.update_layout(
                        **PLOTLY_LAYOUT,
                        title="Facturación por Agente",
                        height=420,
                        xaxis=dict(title="Facturación (₲)"),
                        yaxis=dict(title=""),
                        coloraxis_showscale=False,
                    )
                    st.plotly_chart(fig_rev, use_container_width=True, key="ag_rev")

        # ── 3. Treemap: Agente → Sector breakdown ──
        if "Sector" in df_ag.columns and "TOTAL" in df_ag.columns:
            st.markdown("---")
            df_tree = (
                df_ag.groupby(["Agente", "Sector"])
                .agg(Estudios=("TOTAL", "count"), Facturación=("TOTAL", "sum"))
                .reset_index()
            )
            fig_tree = px.treemap(
                df_tree, path=["Agente", "Sector"], values="Estudios",
                color="Facturación", color_continuous_scale="Blues",
                hover_data={"Facturación": ":,.0f"},
            )
            fig_tree.update_layout(
                **PLOTLY_LAYOUT,
                title="Composición: Agente → Sector (tamaño = estudios, color = facturación)",
                height=550,
            )
            st.plotly_chart(fig_tree, use_container_width=True, key="ag_tree")

        # ── 4. Detail table ──
        st.markdown("---")
        st.markdown("#### 📊 Tabla Resumen por Agente")
        if "TOTAL" in df_ag.columns:
            df_tabla = (
                df_ag.groupby("Agente")
                .agg(
                    Estudios=("TOTAL", "count"),
                    Facturación=("TOTAL", "sum"),
                    Promedio_por_Estudio=("TOTAL", "mean"),
                )
                .sort_values("Estudios", ascending=False)
                .reset_index()
            )
            if "Es_Externo" in df_ag.columns:
                df_ext_count = (
                    df_ag[df_ag["Es_Externo"] == "Externo"]
                    .groupby("Agente").size()
                    .reset_index(name="Estudios_Externos")
                )
                df_tabla = df_tabla.merge(df_ext_count, on="Agente", how="left")
                df_tabla["Estudios_Externos"] = df_tabla["Estudios_Externos"].fillna(0).astype(int)
                df_tabla["% Externo"] = (df_tabla["Estudios_Externos"] / df_tabla["Estudios"] * 100).round(1)

            df_tabla["Facturación"] = df_tabla["Facturación"].apply(lambda x: f"₲ {x:,.0f}")
            df_tabla["Promedio_por_Estudio"] = df_tabla["Promedio_por_Estudio"].apply(lambda x: f"₲ {x:,.0f}")
            st.dataframe(df_tabla, use_container_width=True, hide_index=True, height=400)

# ── TAB CC — KPI Call Center ────────────────────────────────────────────────
if tab_cc:
    import pdfplumber, re, io

    st.markdown("### 📞 KPI Call Center")
    st.markdown(
        "Sube el reporte PDF mensual de Call Center. Cada página corresponde a un agente."
    )

    # ── Helper: parse one PDF into a list of agent dicts ──────────────────
    def _parse_callcenter_pdf(pdf_bytes: bytes) -> list[dict]:
        """
        Extract data from each page of the call-center PDF.
        Returns a list where each element is a dict with:
          - agente: str
          - grid: pd.DataFrame (rows=days, cols=hours, values=call counts / durations)
          - kpis: dict with parsed KPI values
        """
        results = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                if not lines:
                    continue

                # ── Agent name: first line that is NOT a table header ─────
                agente = lines[0] if lines else "Desconocido"

                # ── Extract the table ─────────────────────────────────────
                tables = page.extract_tables()
                grid_df = pd.DataFrame()
                if tables:
                    tbl = tables[0]  # main grid is the first table
                    # First row = header: Día, 8:00, 9:00, ... 19:00
                    header = [str(c).strip() if c else "" for c in tbl[0]]
                    rows_data = []
                    for row in tbl[1:]:
                        cleaned = [str(c).strip() if c else "" for c in row]
                        if cleaned and cleaned[0]:  # has a day name
                            rows_data.append(cleaned)
                    if header and rows_data:
                        grid_df = pd.DataFrame(rows_data, columns=header[:len(rows_data[0])])

                # ── Extract KPIs from text ────────────────────────────────
                kpis = {}

                # Tiempo Promedio Respuesta
                m = re.search(r"Tiempo\s+Promedio\s+Respuesta[:\s]+(\d+:\d+)", text, re.I)
                kpis["Tiempo Promedio Respuesta"] = m.group(1) if m else "N/D"

                # Oportunidades Nuevas
                m = re.search(r"Oportunidades\s+Nuevas[:\s]+(\d[\d.,]*)", text, re.I)
                kpis["Oportunidades Nuevas"] = int(m.group(1).replace(",", "").replace(".", "")) if m else 0

                # Tasa de Gestión
                m = re.search(r"Tasa\s+de\s+Gesti[oó]n[:\s]+([\d.,]+)\s*%", text, re.I)
                kpis["Tasa de Gestión (%)"] = float(m.group(1).replace(",", ".")) if m else 0.0

                # Tasa de Cierre
                m = re.search(r"Tasa\s+de\s+Cierre[:\s]+([\d.,]+)\s*%", text, re.I)
                kpis["Tasa de Cierre (%)"] = float(m.group(1).replace(",", ".")) if m else 0.0

                # Pendientes (Sin Atender)
                m = re.search(r"Pendientes\s*\(Sin\s+Atender\)[:\s]+(\d[\d.,]*)", text, re.I)
                kpis["Pendientes"] = int(m.group(1).replace(",", "").replace(".", "")) if m else 0

                results.append(dict(agente=agente, grid=grid_df, kpis=kpis))
        return results

    # ── Helper: convert mm:ss string grid to numeric minutes ─────────────
    def _time_to_minutes(val: str) -> float:
        """Convert 'M:SS' or 'H:MM' to total minutes as float."""
        try:
            parts = val.strip().split(":")
            if len(parts) == 2:
                return int(parts[0]) + int(parts[1]) / 60.0
            return float(val)
        except Exception:
            return 0.0

    # ── Session-state store for multi-month data ─────────────────────────
    if "_cc_data" not in st.session_state:
        st.session_state["_cc_data"] = {}  # {month_label: [agent_dicts]}

    # ── Upload UI ────────────────────────────────────────────────────────
    st.markdown("---")
    col_up1, col_up2 = st.columns([1, 2])
    with col_up1:
        month_label = st.text_input(
            "📅 Etiqueta del Mes",
            placeholder="Ej: Marzo 2026",
            help="Nombre descriptivo para identificar este reporte.",
        )
    with col_up2:
        cc_pdf = st.file_uploader(
            "📂 Subir PDF de Call Center",
            type=["pdf"],
            key="cc_pdf_upload",
            help="PDF con una página por agente."
        )

    if cc_pdf and month_label:
        file_id = f"{cc_pdf.name}_{cc_pdf.size}_{month_label}"
        if st.session_state.get("_cc_last_file") != file_id:
            with st.spinner("Extrayendo datos del PDF…"):
                raw = cc_pdf.read()
                agents = _parse_callcenter_pdf(raw)
            if agents:
                st.session_state["_cc_data"][month_label] = agents
                st.session_state["_cc_last_file"] = file_id
                st.success(f"✅ Se extrajeron **{len(agents)} agentes** para **{month_label}**.")
                st.rerun()
            else:
                st.error("No se pudieron extraer datos del PDF. Verifica el formato.")
    elif cc_pdf and not month_label:
        st.warning("⚠️ Escribe una etiqueta de mes antes de procesar el PDF.")

    # ── Show loaded months ───────────────────────────────────────────────
    cc_data = st.session_state.get("_cc_data", {})
    if cc_data:
        st.markdown("---")
        st.markdown("#### 📋 Meses cargados")
        cols_months = st.columns(min(len(cc_data), 5))
        for i, (ml, agents) in enumerate(cc_data.items()):
            with cols_months[i % len(cols_months)]:
                st.markdown(
                    f"""<div style="background:#161b22;border:1px solid #30363d;border-radius:10px;
                    padding:14px;text-align:center;">
                    <span style="font-size:1.4rem;">📅</span><br>
                    <b style="color:#e6edf3;">{ml}</b><br>
                    <span style="color:#8b949e;font-size:0.85rem;">{len(agents)} agentes</span></div>""",
                    unsafe_allow_html=True,
                )
        # Option to clear data
        if st.button("🗑️ Limpiar todos los datos cargados", key="cc_clear"):
            st.session_state["_cc_data"] = {}
            st.session_state.pop("_cc_last_file", None)
            st.rerun()

        # ── Month selector ────────────────────────────────────────────────
        st.markdown("---")
        month_options = list(cc_data.keys())
        sel_month = st.selectbox("Seleccionar mes para análisis:", month_options, key="cc_sel_month")
        agents = cc_data[sel_month]

        # ── Build unified DataFrame for KPIs ─────────────────────────────
        kpi_rows = []
        for a in agents:
            row = {"Agente": a["agente"]}
            row.update(a["kpis"])
            kpi_rows.append(row)
        df_kpi = pd.DataFrame(kpi_rows)

        # ── KPI Summary Cards ────────────────────────────────────────────
        st.markdown("---")
        st.markdown(f"### 📊 Resumen KPI — {sel_month}")

        total_oportunidades = df_kpi["Oportunidades Nuevas"].sum()
        avg_gestion = df_kpi["Tasa de Gestión (%)"].mean()
        avg_cierre = df_kpi["Tasa de Cierre (%)"].mean()
        total_pendientes = df_kpi["Pendientes"].sum()

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("🎯 Oportunidades Nuevas", f"{total_oportunidades:,}")
        k2.metric("📈 Tasa Gestión Promedio", f"{avg_gestion:.1f}%")
        k3.metric("🏆 Tasa Cierre Promedio", f"{avg_cierre:.1f}%")
        k4.metric("⏳ Pendientes Totales", f"{total_pendientes:,}")

        # ── Table: KPIs per Agent ─────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 📋 Detalle por Agente")
        df_show = df_kpi.copy()
        df_show["Tasa de Gestión (%)"] = df_show["Tasa de Gestión (%)"].apply(lambda x: f"{x:.1f}%")
        df_show["Tasa de Cierre (%)"] = df_show["Tasa de Cierre (%)"].apply(lambda x: f"{x:.1f}%")
        df_show["Oportunidades Nuevas"] = df_show["Oportunidades Nuevas"].apply(lambda x: f"{x:,}")
        st.dataframe(df_show, use_container_width=True, hide_index=True)

        # ── Bar chart: Oportunidades Nuevas per Agent ─────────────────────
        st.markdown("---")
        st.markdown("#### 🎯 Oportunidades Nuevas por Agente")
        df_opp = df_kpi.sort_values("Oportunidades Nuevas", ascending=True)
        fig_opp = px.bar(
            df_opp, y="Agente", x="Oportunidades Nuevas", orientation="h",
            text="Oportunidades Nuevas", color="Oportunidades Nuevas",
            color_continuous_scale=["#1a1e2e", "#58a6ff"],
        )
        fig_opp.update_traces(
            texttemplate="%{text:,}", textposition="outside", textfont_size=12,
            hovertemplate="<b>%{y}</b><br>Oportunidades: %{x:,}<extra></extra>",
        )
        fig_opp.update_layout(
            **PLOTLY_LAYOUT, title=None,
            height=max(380, len(df_opp) * 48),
            yaxis=dict(title=""),
            xaxis=dict(title="Oportunidades Nuevas", gridcolor="rgba(48,54,61,0.4)"),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_opp, use_container_width=True, key="cc_opp_bar")

        # ── Dual bar: Tasa de Gestión vs Tasa de Cierre ───────────────────
        st.markdown("---")
        st.markdown("#### 📈 Tasas de Gestión y Cierre por Agente")
        df_tasas = df_kpi[["Agente", "Tasa de Gestión (%)", "Tasa de Cierre (%)"]].melt(
            id_vars="Agente", var_name="Indicador", value_name="Porcentaje"
        )
        fig_tasas = px.bar(
            df_tasas, x="Agente", y="Porcentaje", color="Indicador",
            barmode="group", text="Porcentaje",
            color_discrete_map={
                "Tasa de Gestión (%)": "#3fb950",
                "Tasa de Cierre (%)": "#58a6ff",
            },
        )
        fig_tasas.update_traces(
            texttemplate="%{text:.1f}%", textposition="outside", textfont_size=11,
            hovertemplate="<b>%{x}</b><br>%{data.name}: %{y:.1f}%<extra></extra>",
        )
        fig_tasas.update_layout(
            **PLOTLY_LAYOUT, title=None, height=450,
            xaxis=dict(title="", tickangle=-35),
            yaxis=dict(title="Porcentaje (%)", gridcolor="rgba(48,54,61,0.4)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        )
        st.plotly_chart(fig_tasas, use_container_width=True, key="cc_tasas_bar")

        # ── Pendientes bar ────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### ⏳ Pendientes (Sin Atender) por Agente")
        df_pend = df_kpi.sort_values("Pendientes", ascending=True)
        fig_pend = px.bar(
            df_pend, y="Agente", x="Pendientes", orientation="h",
            text="Pendientes", color="Pendientes",
            color_continuous_scale=["#1a1e2e", "#f78166"],
        )
        fig_pend.update_traces(
            texttemplate="%{text:,}", textposition="outside", textfont_size=12,
            hovertemplate="<b>%{y}</b><br>Pendientes: %{x:,}<extra></extra>",
        )
        fig_pend.update_layout(
            **PLOTLY_LAYOUT, title=None,
            height=max(380, len(df_pend) * 48),
            yaxis=dict(title=""),
            xaxis=dict(title="Pendientes (Sin Atender)", gridcolor="rgba(48,54,61,0.4)"),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_pend, use_container_width=True, key="cc_pend_bar")

        # ── Heatmap: Agent × Hour activity ────────────────────────────────
        st.markdown("---")
        st.markdown("#### 🔥 Mapa de Calor de Actividad por Hora")
        st.markdown("Suma de actividad de todos los días por agente y franja horaria.")

        heat_rows = []
        for a in agents:
            gdf = a["grid"]
            if gdf.empty:
                continue
            # Columns: Día, 8:00, 9:00, ..., 19:00
            hour_cols = [c for c in gdf.columns if re.match(r"\d+:\d+", c)]
            for hc in hour_cols:
                total = gdf[hc].apply(_time_to_minutes).sum()
                heat_rows.append({"Agente": a["agente"], "Hora": hc, "Actividad": round(total, 1)})

        if heat_rows:
            df_heat = pd.DataFrame(heat_rows)
            mat = df_heat.pivot(index="Agente", columns="Hora", values="Actividad").fillna(0)

            # Sort hours numerically
            sorted_hours = sorted(mat.columns, key=lambda h: int(h.split(":")[0]))
            mat = mat[sorted_hours]

            fig_cc_heat = px.imshow(
                mat, text_auto=".1f", aspect="auto",
                labels=dict(x="Hora del Día", y="Agente", color="Minutos"),
                color_continuous_scale=HEATMAP_COLORS,
            )
            fig_cc_heat.update_layout(
                **PLOTLY_LAYOUT, title=None, height=max(380, len(mat) * 45),
                xaxis=dict(side="top"),
            )
            fig_cc_heat.update_traces(
                hovertemplate="<b>%{y}</b> a las <b>%{x}</b><br>Actividad: %{z:.1f} min<extra></extra>"
            )
            st.plotly_chart(fig_cc_heat, use_container_width=True, key="cc_heatmap")
        else:
            st.info("No se pudo generar el mapa de calor (tablas de grilla no detectadas).")

        # ── Individual agent detail ───────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 🔍 Detalle Individual de Agente")
        agent_names = [a["agente"] for a in agents]
        sel_agent = st.selectbox("Seleccionar agente:", agent_names, key="cc_sel_agent")

        sel_data = next((a for a in agents if a["agente"] == sel_agent), None)
        if sel_data:
            # KPI mini-cards for selected agent
            kp = sel_data["kpis"]
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("⏱️ T. Promedio Resp.", kp.get("Tiempo Promedio Respuesta", "N/D"))
            c2.metric("🎯 Oportunidades", f"{kp.get('Oportunidades Nuevas', 0):,}")
            c3.metric("📈 Gestión", f"{kp.get('Tasa de Gestión (%)', 0):.1f}%")
            c4.metric("🏆 Cierre", f"{kp.get('Tasa de Cierre (%)', 0):.1f}%")
            c5.metric("⏳ Pendientes", f"{kp.get('Pendientes', 0):,}")

            # Show grid table if available
            gdf = sel_data["grid"]
            if not gdf.empty:
                st.markdown("##### Grilla de Actividad (valores originales)")
                st.dataframe(gdf, use_container_width=True, hide_index=True)

                # Individual heatmap for this agent
                hour_cols = [c for c in gdf.columns if re.match(r"\d+:\d+", c)]
                day_col = gdf.columns[0] if gdf.columns[0] not in hour_cols else "Día"
                if hour_cols and day_col in gdf.columns:
                    mat_agent = gdf.set_index(day_col)[hour_cols].map(_time_to_minutes)
                    sorted_hours_a = sorted(hour_cols, key=lambda h: int(h.split(":")[0]))
                    mat_agent = mat_agent[sorted_hours_a]

                    fig_agent_heat = px.imshow(
                        mat_agent, text_auto=".1f", aspect="auto",
                        labels=dict(x="Hora", y="Día", color="Minutos"),
                        color_continuous_scale=[
                            [0.0, "#0d1117"], [0.3, "#1a1e2e"], [0.5, "#2a4a3a"],
                            [0.7, "#2d7a4a"], [0.9, "#3fb950"], [1.0, "#56d364"],
                        ],
                    )
                    fig_agent_heat.update_layout(
                        **PLOTLY_LAYOUT,
                        title=f"Actividad por Día y Hora — {sel_agent}",
                        height=350,
                        xaxis=dict(side="top"),
                    )
                    fig_agent_heat.update_traces(
                        hovertemplate="<b>%{y}</b> a las <b>%{x}</b><br>%{z:.1f} min<extra></extra>"
                    )
                    st.plotly_chart(fig_agent_heat, use_container_width=True, key="cc_agent_heat")

        # ── Multi-month comparison (if 2+ months loaded) ──────────────────
        if len(cc_data) >= 2:
            st.markdown("---")
            st.markdown("#### 📈 Evolución Mensual entre Períodos")

            evo_rows = []
            for ml, ags in cc_data.items():
                for a in ags:
                    evo_rows.append({
                        "Mes": ml,
                        "Agente": a["agente"],
                        "Oportunidades Nuevas": a["kpis"].get("Oportunidades Nuevas", 0),
                        "Tasa de Gestión (%)": a["kpis"].get("Tasa de Gestión (%)", 0),
                        "Tasa de Cierre (%)": a["kpis"].get("Tasa de Cierre (%)", 0),
                        "Pendientes": a["kpis"].get("Pendientes", 0),
                    })
            df_evo = pd.DataFrame(evo_rows)

            # Total KPI by month
            df_evo_totals = df_evo.groupby("Mes").agg(
                Oportunidades=("Oportunidades Nuevas", "sum"),
                Gestión_Prom=("Tasa de Gestión (%)", "mean"),
                Cierre_Prom=("Tasa de Cierre (%)", "mean"),
                Pendientes=("Pendientes", "sum"),
            ).reset_index()

            col_evo_a, col_evo_b = st.columns(2)
            with col_evo_a:
                fig_evo_opp = px.bar(
                    df_evo_totals, x="Mes", y="Oportunidades", text="Oportunidades",
                    color_discrete_sequence=["#58a6ff"],
                )
                fig_evo_opp.update_traces(
                    texttemplate="%{text:,}", textposition="outside",
                    hovertemplate="<b>%{x}</b><br>Oportunidades: %{y:,}<extra></extra>",
                )
                fig_evo_opp.update_layout(
                    **PLOTLY_LAYOUT, title="Oportunidades Nuevas por Mes",
                    height=380,
                    xaxis=dict(title=""),
                    yaxis=dict(title="Oportunidades", gridcolor="rgba(48,54,61,0.4)"),
                )
                st.plotly_chart(fig_evo_opp, use_container_width=True, key="cc_evo_opp")

            with col_evo_b:
                fig_evo_pend = px.bar(
                    df_evo_totals, x="Mes", y="Pendientes", text="Pendientes",
                    color_discrete_sequence=["#f78166"],
                )
                fig_evo_pend.update_traces(
                    texttemplate="%{text:,}", textposition="outside",
                    hovertemplate="<b>%{x}</b><br>Pendientes: %{y:,}<extra></extra>",
                )
                fig_evo_pend.update_layout(
                    **PLOTLY_LAYOUT, title="Pendientes por Mes",
                    height=380,
                    xaxis=dict(title=""),
                    yaxis=dict(title="Pendientes", gridcolor="rgba(48,54,61,0.4)"),
                )
                st.plotly_chart(fig_evo_pend, use_container_width=True, key="cc_evo_pend")

            # Per-agent evolution line chart
            st.markdown("##### Evolución por Agente")
            kpi_sel = st.selectbox(
                "KPI a visualizar:",
                ["Oportunidades Nuevas", "Tasa de Gestión (%)", "Tasa de Cierre (%)", "Pendientes"],
                key="cc_evo_kpi",
            )
            fig_evo_line = px.line(
                df_evo, x="Mes", y=kpi_sel, color="Agente",
                markers=True, text=kpi_sel,
            )
            fig_evo_line.update_traces(textposition="top center", textfont_size=10)
            fig_evo_line.update_layout(
                **PLOTLY_LAYOUT, title=None, height=450,
                xaxis=dict(title=""),
                yaxis=dict(title=kpi_sel, gridcolor="rgba(48,54,61,0.4)"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig_evo_line, use_container_width=True, key="cc_evo_line")

    else:
        st.markdown("---")
        st.markdown(
            """<div style="text-align:center; padding:60px 20px; border:2px dashed #30363d;
            border-radius:16px; background:linear-gradient(135deg, rgba(88,166,255,0.04) 0%, rgba(188,140,255,0.04) 100%);">
            <div style="font-size:3.5rem; margin-bottom:12px;">📞</div>
            <h3 style="color:#e6edf3; margin-bottom:8px;">Sin datos de Call Center</h3>
            <p style="color:#8b949e; max-width:450px; margin:auto; line-height:1.6;">
                Sube un archivo <code style="color:#58a6ff;">PDF</code> mensual de Call Center
                indicando el mes correspondiente para comenzar el análisis.
            </p></div>""",
            unsafe_allow_html=True,
        )

# ── TAB 8 — Comparativa entre Períodos ─────────────────────────────────────
if tab8:
    st.markdown("### ⚖️ Comparativa de Períodos")
    st.markdown("Compara indicadores clave de rendimiento entre dos ventanas de tiempo distintas.")

    if "Fecha" in df.columns:
        # Default dates: 
        min_date = df["Fecha"].min().date() if not pd.isna(df["Fecha"].min()) else None
        max_date = df["Fecha"].max().date() if not pd.isna(df["Fecha"].max()) else None
        
        if min_date and max_date:
            from datetime import timedelta
            
            # Simple heuristic for defaults: Periodo B = last 30 days of data, Periodo A = previous 30 days
            default_b_end = max_date
            default_b_start = max(min_date, default_b_end - timedelta(days=29))
            default_a_end = max(min_date, default_b_start - timedelta(days=1))
            default_a_start = max(min_date, default_a_end - timedelta(days=29))

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("#### 📅 Período A (Base)")
                rango_a = st.date_input("Fechas del Período A", value=(default_a_start, default_a_end), key="rango_a", min_value=min_date, max_value=max_date)
            
            with col_b:
                st.markdown("#### 📅 Período B (Comparación)")
                rango_b = st.date_input("Fechas del Período B", value=(default_b_start, default_b_end), key="rango_b", min_value=min_date, max_value=max_date)

            if len(rango_a) == 2 and len(rango_b) == 2:
                # ── Filtrar dataframes ────────────────────────────────────
                start_a = pd.to_datetime(rango_a[0])
                end_a = pd.to_datetime(rango_a[1]) + pd.Timedelta(days=1, microseconds=-1)
                start_b = pd.to_datetime(rango_b[0])
                end_b = pd.to_datetime(rango_b[1]) + pd.Timedelta(days=1, microseconds=-1)
                
                df_a = df[(df["Fecha"] >= start_a) & (df["Fecha"] <= end_a)]
                df_b = df[(df["Fecha"] >= start_b) & (df["Fecha"] <= end_b)]

                st.markdown("---")
                
                # ── Calcular métricas globales ────────────────────────────
                fac_a = df_a["TOTAL"].sum() if "TOTAL" in df_a.columns else 0
                est_a = len(df_a)
                ticket_a = fac_a / est_a if est_a else 0
                
                fac_b = df_b["TOTAL"].sum() if "TOTAL" in df_b.columns else 0
                est_b = len(df_b)
                ticket_b = fac_b / est_b if est_b else 0
                
                # Deltas
                def pct_change(old, new):
                    if old == 0 and new == 0: return "0%"
                    if old == 0: return "∞%"
                    pct = ((new - old) / old) * 100
                    return f"{pct:+.1f}%"

                colK1, colK2, colK3 = st.columns(3)
                colK1.metric("💵 Facturación (B vs A)", f"₲ {fac_b:,.0f}", delta=pct_change(fac_a, fac_b))
                colK2.metric("📋 Volumen Estudios", f"{est_b:,}", delta=pct_change(est_a, est_b))
                colK3.metric("🎫 Ticket Prom.", f"₲ {ticket_b:,.0f}", delta=pct_change(ticket_a, ticket_b))

                st.markdown("---")

                # ── Gráficos Comparativos: Sectores ───────────────────────
                if "Sector" in df.columns:
                    # Agrupar A
                    df_sec_a = df_a.groupby("Sector").agg(Facturacion_A=("TOTAL", "sum"), Estudios_A=("Sector", "count")).reset_index()
                    # Agrupar B
                    df_sec_b = df_b.groupby("Sector").agg(Facturacion_B=("TOTAL", "sum"), Estudios_B=("Sector", "count")).reset_index()
                    
                    # Merge outer for comparison
                    df_comp = pd.merge(df_sec_a, df_sec_b, on="Sector", how="outer").fillna(0)
                    df_comp = df_comp.sort_values("Estudios_B", ascending=False).head(15) # Top 15 para visualizar mejor
                    
                    st.markdown("#### Comparación por Sector")
                    tc1, tc2 = st.tabs(["📊 Volumen", "💰 Facturación"])
                    
                    with tc1:
                        fig_vol_comp = go.Figure()
                        fig_vol_comp.add_trace(go.Bar(
                            x=df_comp["Sector"], y=df_comp["Estudios_A"],
                            name="Período A", marker_color="#1f6feb"
                        ))
                        fig_vol_comp.add_trace(go.Bar(
                            x=df_comp["Sector"], y=df_comp["Estudios_B"],
                            name="Período B", marker_color="#3fb950"
                        ))
                        fig_vol_comp.update_layout(
                            **PLOTLY_LAYOUT, barmode='group',
                            xaxis_title="Sector", yaxis_title="Cantidad de Estudios",
                            height=400,
                        )
                        st.plotly_chart(fig_vol_comp, use_container_width=True, key="comp_vol")
                        
                    with tc2:
                        fig_fac_comp = go.Figure()
                        fig_fac_comp.add_trace(go.Bar(
                            x=df_comp["Sector"], y=df_comp["Facturacion_A"],
                            name="Período A", marker_color="#1f6feb"
                        ))
                        fig_fac_comp.add_trace(go.Bar(
                            x=df_comp["Sector"], y=df_comp["Facturacion_B"],
                            name="Período B", marker_color="#3fb950"
                        ))
                        fig_fac_comp.update_layout(
                            **PLOTLY_LAYOUT, barmode='group',
                            xaxis_title="Sector", yaxis_title="Facturación (₲)",
                            height=400,
                        )
                        st.plotly_chart(fig_fac_comp, use_container_width=True, key="comp_fac")
            else:
                st.info("Selecciona rangos de inicio y fin para ambos períodos.")
        else:
            st.info("La columna de fechas no contiene datos válidos.")
    else:
        st.info("La columna 'Fecha' no está disponible para hacer comparaciones temporales.")

# ── TAB 10 — Análisis de Estudios ──────────────────────────────────────────
if tab10:
    st.markdown("### 🔎 Análisis Profundo de Estudios")
    st.markdown("Explora en detalle los tipos de estudios realizados, qué médicos derivan más para cada modalidad, y qué estudios generan mayor facturación.")

    has_sector = "Sector" in df_filtered.columns
    has_estudio = "Estudio" in df_filtered.columns
    has_total = "TOTAL" in df_filtered.columns
    has_doc = "Doctor Tratante" in df_filtered.columns
    has_informante = "Doctor Informante" in df_filtered.columns

    # ── Filtros propios de esta pestaña ──────────────────────────────────
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        if has_sector:
            opciones_sector = ["Todos"] + sorted(df_filtered["Sector"].dropna().unique().tolist())
            filtro_sector = st.selectbox("🏷️ Modalidad / Sector", opciones_sector, index=0, key="est_sector")
        else:
            filtro_sector = "Todos"
    with fc2:
        if has_doc:
            opciones_doc = ["Todos"] + sorted(df_filtered["Doctor Tratante"].dropna().unique().tolist())
            filtro_doc = st.selectbox("👨‍⚕️ Doctor Tratante", opciones_doc, index=0, key="est_doc")
        else:
            filtro_doc = "Todos"
    with fc3:
        if has_informante:
            opciones_inf = ["Todos"] + sorted(df_filtered["Doctor Informante"].dropna().unique().tolist())
            filtro_inf = st.selectbox("🔬 Radiólogo Informante", opciones_inf, index=0, key="est_inf")
        else:
            filtro_inf = "Todos"

    # Aplicar filtros locales
    df_est = df_filtered.copy()
    if filtro_sector != "Todos" and has_sector:
        df_est = df_est[df_est["Sector"] == filtro_sector]
    if filtro_doc != "Todos" and has_doc:
        df_est = df_est[df_est["Doctor Tratante"] == filtro_doc]
    if filtro_inf != "Todos" and has_informante:
        df_est = df_est[df_est["Doctor Informante"] == filtro_inf]

    st.markdown("---")

    # ── KPIs rápidos ─────────────────────────────────────────────────
    total_est = len(df_est)
    fac_est = df_est["TOTAL"].sum() if has_total else 0
    ticket_est = fac_est / total_est if total_est > 0 else 0
    n_sectores = df_est["Sector"].nunique() if has_sector else 0
    n_estudios = df_est["Estudio"].nunique() if has_estudio else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📋 Total Estudios", f"{total_est:,}")
    k2.metric("💵 Facturación", f"₲ {fac_est:,.0f}")
    k3.metric("🎫 Ticket Prom.", f"₲ {ticket_est:,.0f}")
    k4.metric("🏷️ Modalidades" if n_estudios == 0 else "📊 Tipos de Estudio", f"{n_sectores}" if n_estudios == 0 else f"{n_estudios}")

    st.markdown("---")

    # ───────────────────────────────────────────────────────────────────
    # SECCIÓN 1: Ranking de Estudios por Facturación y Volumen
    # ───────────────────────────────────────────────────────────────────
    # Intentar agrupar por columna "Estudio" si existe, sino por "Sector"
    group_col = "Estudio" if has_estudio else ("Sector" if has_sector else None)

    if group_col:
        st.markdown(f"#### 🏆 Ranking de {'Estudios' if has_estudio else 'Modalidades'} por Facturación")
        
        agg_dict = {group_col: "count"}
        rename_map = {group_col: "Volumen"}
        if has_total:
            df_rank_est = df_est.groupby(group_col).agg(
                Volumen=(group_col, "count"),
                Facturacion=("TOTAL", "sum")
            ).reset_index()
            df_rank_est["Ticket_Prom"] = df_rank_est["Facturacion"] / df_rank_est["Volumen"]
            df_rank_est = df_rank_est.sort_values("Facturacion", ascending=False)
        else:
            df_rank_est = df_est.groupby(group_col).size().reset_index(name="Volumen")
            df_rank_est = df_rank_est.sort_values("Volumen", ascending=False)

        top_n = min(20, len(df_rank_est))
        df_top = df_rank_est.head(top_n)

        rc1, rc2 = st.columns(2)
        with rc1:
            if has_total:
                fig_rank_fac = px.bar(
                    df_top.sort_values("Facturacion", ascending=True).tail(15),
                    y=group_col, x="Facturacion", orientation="h",
                    text="Facturacion", color="Facturacion",
                    color_continuous_scale=[[0, "#264C8D"], [1, "#A11C32"]],
                )
                fig_rank_fac.update_traces(
                    texttemplate="₲%{text:,.0f}", textposition="inside",
                    hovertemplate="<b>%{y}</b><br>Facturación: ₲%{x:,.0f}<extra></extra>",
                )
                fig_rank_fac.update_layout(
                    **PLOTLY_LAYOUT, showlegend=False,
                    title=f"Top {min(15, top_n)} por Facturación",
                    xaxis=dict(title="Facturación (₲)", gridcolor="rgba(48,54,61,0.4)"),
                    yaxis=dict(title=""),
                    height=500, coloraxis_showscale=False,
                )
                st.plotly_chart(fig_rank_fac, use_container_width=True, key="est_rank_fac")

        with rc2:
            fig_rank_vol = px.bar(
                df_top.sort_values("Volumen", ascending=True).tail(15),
                y=group_col, x="Volumen", orientation="h",
                text="Volumen", color="Volumen",
                color_continuous_scale=[[0, "#1f3a5f"], [1, "#58a6ff"]],
            )
            fig_rank_vol.update_traces(
                texttemplate="%{text:,}", textposition="inside",
                hovertemplate="<b>%{y}</b><br>Volumen: %{x:,}<extra></extra>",
            )
            fig_rank_vol.update_layout(
                **PLOTLY_LAYOUT, showlegend=False,
                title=f"Top {min(15, top_n)} por Volumen",
                xaxis=dict(title="Cantidad", gridcolor="rgba(48,54,61,0.4)"),
                yaxis=dict(title=""),
                height=500, coloraxis_showscale=False,
            )
            st.plotly_chart(fig_rank_vol, use_container_width=True, key="est_rank_vol")

        # Tabla resumen
        with st.expander("📋 Tabla completa de estudios", expanded=False):
            df_display = df_rank_est.copy()
            if has_total:
                df_display["Facturacion"] = df_display["Facturacion"].apply(lambda v: f"₲ {v:,.0f}")
                df_display["Ticket_Prom"] = df_display["Ticket_Prom"].apply(lambda v: f"₲ {v:,.0f}")
            st.dataframe(df_display, use_container_width=True, hide_index=True, height=350)

    st.markdown("---")

    # ───────────────────────────────────────────────────────────────────
    # SECCIÓN 2: ¿Qué médico envía más por cada tipo de estudio/sector?
    # ───────────────────────────────────────────────────────────────────
    if has_doc and has_sector:
        st.markdown("#### 👨‍⚕️ Top Derivantes por Modalidad")
        st.markdown("Descubre qué médico envía más pacientes a cada tipo de estudio.")

        # Agrupar
        df_doc_sec = df_est.groupby(["Sector", "Doctor Tratante"]).agg(
            Derivaciones=("Doctor Tratante", "count")
        ).reset_index()
        if has_total:
            df_doc_sec_fac = df_est.groupby(["Sector", "Doctor Tratante"])["TOTAL"].sum().reset_index(name="Facturacion")
            df_doc_sec = df_doc_sec.merge(df_doc_sec_fac, on=["Sector", "Doctor Tratante"], how="left")

        # Selector de modalidad para explorar
        modalidades_disponibles = sorted(df_doc_sec["Sector"].unique().tolist())
        sel_modal = st.selectbox("🏷️ Selecciona la Modalidad a explorar", modalidades_disponibles, key="modal_explore")

        df_modal = df_doc_sec[df_doc_sec["Sector"] == sel_modal].sort_values("Derivaciones", ascending=False).head(10)

        mc1, mc2 = st.columns(2)
        with mc1:
            fig_doc_modal = px.bar(
                df_modal.sort_values("Derivaciones", ascending=True),
                y="Doctor Tratante", x="Derivaciones", orientation="h",
                text="Derivaciones", color="Derivaciones",
                color_continuous_scale=[[0, "#1f3a5f"], [1, "#3fb950"]],
            )
            fig_doc_modal.update_traces(
                texttemplate="%{text:,}", textposition="inside",
                hovertemplate="<b>%{y}</b><br>Derivaciones: %{x:,}<extra></extra>",
            )
            fig_doc_modal.update_layout(
                **PLOTLY_LAYOUT, showlegend=False,
                title=f"Top 10 Derivantes → {sel_modal}",
                xaxis=dict(title="Derivaciones", gridcolor="rgba(48,54,61,0.4)"),
                yaxis=dict(title=""),
                height=400, coloraxis_showscale=False,
            )
            st.plotly_chart(fig_doc_modal, use_container_width=True, key="doc_modal_vol")

        with mc2:
            if has_total and "Facturacion" in df_modal.columns:
                fig_doc_fac = px.bar(
                    df_modal.sort_values("Facturacion", ascending=True),
                    y="Doctor Tratante", x="Facturacion", orientation="h",
                    text="Facturacion", color="Facturacion",
                    color_continuous_scale=[[0, "#264C8D"], [1, "#A11C32"]],
                )
                fig_doc_fac.update_traces(
                    texttemplate="₲%{text:,.0f}", textposition="inside",
                    hovertemplate="<b>%{y}</b><br>Facturación: ₲%{x:,.0f}<extra></extra>",
                )
                fig_doc_fac.update_layout(
                    **PLOTLY_LAYOUT, showlegend=False,
                    title=f"Top 10 por Facturación → {sel_modal}",
                    xaxis=dict(title="Facturación (₲)", gridcolor="rgba(48,54,61,0.4)"),
                    yaxis=dict(title=""),
                    height=400, coloraxis_showscale=False,
                )
                st.plotly_chart(fig_doc_fac, use_container_width=True, key="doc_modal_fac")
            else:
                st.info("Columna TOTAL no disponible para facturación.")

    st.markdown("---")

    # ───────────────────────────────────────────────────────────────────
    # SECCIÓN 3: Composición de facturación por modalidad (Torta)
    # ───────────────────────────────────────────────────────────────────
    if has_sector and has_total:
        st.markdown("#### 🧩 Composición de la Facturación por Modalidad")
        
        pc1, pc2 = st.columns(2)
        
        df_pie_fac = df_est.groupby("Sector")["TOTAL"].sum().reset_index(name="Facturacion").sort_values("Facturacion", ascending=False)
        df_pie_vol = df_est.groupby("Sector").size().reset_index(name="Volumen").sort_values("Volumen", ascending=False)
        
        with pc1:
            fig_pie_fac = px.pie(
                df_pie_fac, names="Sector", values="Facturacion", hole=0.45,
            )
            fig_pie_fac.update_traces(
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>Facturación: ₲%{value:,.0f}<br>%{percent}<extra></extra>",
            )
            fig_pie_fac.update_layout(**PLOTLY_LAYOUT, title="Participación en Facturación", height=400, showlegend=False)
            st.plotly_chart(fig_pie_fac, use_container_width=True, key="est_pie_fac")

        with pc2:
            fig_pie_vol = px.pie(
                df_pie_vol, names="Sector", values="Volumen", hole=0.45,
            )
            fig_pie_vol.update_traces(
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>Volumen: %{value:,}<br>%{percent}<extra></extra>",
            )
            fig_pie_vol.update_layout(**PLOTLY_LAYOUT, title="Participación en Volumen", height=400, showlegend=False)
            st.plotly_chart(fig_pie_vol, use_container_width=True, key="est_pie_vol")

    st.markdown("---")

    # ───────────────────────────────────────────────────────────────────
    # SECCIÓN 4: Evolución mensual por modalidad seleccionada
    # ───────────────────────────────────────────────────────────────────
    if has_sector and "Fecha" in df_est.columns:
        st.markdown("#### 📈 Evolución Mensual por Modalidad")
        
        df_evo_sec = (
            df_est.groupby([pd.Grouper(key="Fecha", freq="ME"), "Sector"])
            .size()
            .reset_index(name="Volumen")
        )
        df_evo_sec["Periodo"] = df_evo_sec["Fecha"].dt.strftime("%Y-%m")
        
        fig_evo_sec = px.line(
            df_evo_sec, x="Periodo", y="Volumen", color="Sector",
            markers=True,
        )
        fig_evo_sec.update_layout(
            **PLOTLY_LAYOUT,
            title="Tendencia de Volumen por Modalidad",
            xaxis=dict(title="Período", gridcolor="rgba(48,54,61,0.4)"),
            yaxis=dict(title="Cantidad de Estudios", gridcolor="rgba(48,54,61,0.4)"),
            height=400,
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig_evo_sec, use_container_width=True, key="est_evo_sec")

# ── TAB 11 — Micro-Rentabilidad y Caja ─────────────────────────────────────
if tab11:
    st.markdown("### 💎 Micro-Rentabilidad y Caja")
    st.markdown("Análisis detallado de insumos, métodos de pago, rentabilidad por estudio e impacto de descuentos.")

    # ── Data cleansing for financial micro-columns ───────────────────────
    _micro_cols = {
        "Insumos": "Insumos",
        "Total a Pagar Insumos Seguro": "Ins_Seguro",
        "Total a Pagar Insumos Paciente": "Ins_Paciente",
        "Descuento": "Descuento",
    }
    df_micro = df_filtered.copy()
    for orig, alias in _micro_cols.items():
        if orig in df_micro.columns:
            df_micro[alias] = pd.to_numeric(df_micro[orig], errors="coerce").fillna(0)
        else:
            df_micro[alias] = 0

    # ── Sub-tabs for organized navigation ────────────────────────────────
    st11_cows, st11_insumos, st11_flujo, st11_desc = st.tabs([
        "🐄 Cash Cows",
        "🧪 Insumos y Cobertura",
        "💳 Flujo de Caja",
        "🏷️ Impacto de Descuentos",
    ])

    # ════════════════════════════════════════════════════════════════════
    # 11A — TOP 10 ESTUDIOS "CASH COWS"
    # ════════════════════════════════════════════════════════════════════
    with st11_cows:
        st.markdown("#### 🐄 Top 10 Estudios Generadores de Ingreso")
        st.markdown("Los estudios que más contribuyen a la facturación bruta de la clínica.")

        has_estudio_m = "Estudio" in df_micro.columns
        has_total_m = "TOTAL" in df_micro.columns
        group_cow = "Estudio" if has_estudio_m else ("Sector" if "Sector" in df_micro.columns else None)

        if group_cow and has_total_m:
            df_cows = (
                df_micro.groupby(group_cow)
                .agg(
                    Ingresos=("TOTAL", "sum"),
                    Volumen=(group_cow, "count"),
                )
                .reset_index()
                .sort_values("Ingresos", ascending=False)
                .head(10)
            )
            df_cows["Ticket_Prom"] = df_cows["Ingresos"] / df_cows["Volumen"]

            # KPIs
            cow_total = df_cows["Ingresos"].sum()
            cow_vol = df_cows["Volumen"].sum()
            cow_ticket = cow_total / cow_vol if cow_vol else 0
            ck1, ck2, ck3 = st.columns(3)
            ck1.metric("💵 Ingreso Top 10", f"₲ {cow_total:,.0f}")
            ck2.metric("📋 Volumen Top 10", f"{cow_vol:,}")
            ck3.metric("🎫 Ticket Prom. Top 10", f"₲ {cow_ticket:,.0f}")

            st.markdown("---")

            # Horizontal bar chart
            df_cows_chart = df_cows.sort_values("Ingresos", ascending=True)
            fig_cows = go.Figure()
            fig_cows.add_trace(go.Bar(
                y=df_cows_chart[group_cow],
                x=df_cows_chart["Ingresos"],
                orientation="h",
                text=df_cows_chart.apply(
                    lambda r: f"₲{r['Ingresos']:,.0f}  ({int(r['Volumen']):,} est.)", axis=1
                ),
                textposition="outside",
                textfont=dict(size=11),
                marker=dict(
                    color=df_cows_chart["Ingresos"],
                    colorscale=[[0, "#264C8D"], [0.5, "#A11C32"], [1, "#f0883e"]],
                    line=dict(width=0),
                ),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Ingreso: ₲%{x:,.0f}<br>"
                    "Volumen: %{customdata[0]:,}<br>"
                    "Ticket Prom: ₲%{customdata[1]:,.0f}"
                    "<extra></extra>"
                ),
                customdata=df_cows_chart[["Volumen", "Ticket_Prom"]].values,
            ))
            fig_cows.update_layout(
                **PLOTLY_LAYOUT,
                title=None,
                height=max(420, len(df_cows_chart) * 48),
                yaxis=dict(title=""),
                xaxis=dict(title="Ingresos (₲)", gridcolor="rgba(48,54,61,0.4)"),
            )
            st.plotly_chart(fig_cows, use_container_width=True, key="micro_cows")

            # Summary table
            with st.expander("📋 Tabla completa Cash Cows", expanded=False):
                df_cows_tbl = df_cows.copy()
                df_cows_tbl["Ingresos"] = df_cows_tbl["Ingresos"].apply(lambda v: f"₲ {v:,.0f}")
                df_cows_tbl["Ticket_Prom"] = df_cows_tbl["Ticket_Prom"].apply(lambda v: f"₲ {v:,.0f}")
                st.dataframe(
                    df_cows_tbl.rename(columns={"Ticket_Prom": "Ticket Promedio"}),
                    use_container_width=True, hide_index=True,
                )
        else:
            st.info("Columnas 'Estudio' (o 'Sector') y 'TOTAL' necesarias para este análisis.")

    # ════════════════════════════════════════════════════════════════════
    # 11B — ANÁLISIS DE INSUMOS Y COBERTURA
    # ════════════════════════════════════════════════════════════════════
    with st11_insumos:
        st.markdown("#### 🧪 Análisis de Insumos y Cobertura")
        st.markdown("¿Quién absorbe el costo de los materiales (ej. contrastes)? ¿El seguro o el paciente?")

        total_insumos = df_micro["Insumos"].sum()
        total_ins_seguro = df_micro["Ins_Seguro"].sum()
        total_ins_paciente = df_micro["Ins_Paciente"].sum()

        # KPIs
        ik1, ik2, ik3 = st.columns(3)
        ik1.metric("🧪 Gasto Bruto en Insumos", f"₲ {total_insumos:,.0f}")
        ik2.metric("🛡️ Cubierto por Seguro", f"₲ {total_ins_seguro:,.0f}")
        ik3.metric("👤 A cargo del Paciente", f"₲ {total_ins_paciente:,.0f}")

        st.markdown("---")

        col_ins_a, col_ins_b = st.columns(2)

        with col_ins_a:
            # Donut: Seguro vs Paciente coverage
            df_ins_split = pd.DataFrame({
                "Pagador": ["Seguro Médico", "Paciente"],
                "Monto": [total_ins_seguro, total_ins_paciente],
            })
            # Filter out zero rows for cleaner chart
            df_ins_split = df_ins_split[df_ins_split["Monto"] > 0]

            if not df_ins_split.empty:
                fig_ins_donut = px.pie(
                    df_ins_split, names="Pagador", values="Monto", hole=0.45,
                    color="Pagador",
                    color_discrete_map={"Seguro Médico": "#58a6ff", "Paciente": "#f0883e"},
                )
                fig_ins_donut.update_layout(
                    **PLOTLY_LAYOUT, title="Cobertura de Insumos",
                    height=400, showlegend=True,
                    legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"),
                )
                fig_ins_donut.update_traces(
                    textinfo="percent+value", textfont_size=13,
                    texttemplate="%{percent}<br>₲%{value:,.0f}",
                    hovertemplate="<b>%{label}</b><br>Monto: ₲%{value:,.0f}<br>%{percent}<extra></extra>",
                )
                st.plotly_chart(fig_ins_donut, use_container_width=True, key="micro_ins_donut")
            else:
                st.info("No hay datos de insumos con valores > 0.")

        with col_ins_b:
            # Stacked bar by Sector if available
            if "Sector" in df_micro.columns:
                df_ins_sec = (
                    df_micro.groupby("Sector")
                    .agg(
                        Seguro=("Ins_Seguro", "sum"),
                        Paciente=("Ins_Paciente", "sum"),
                    )
                    .reset_index()
                )
                df_ins_sec = df_ins_sec[(df_ins_sec["Seguro"] > 0) | (df_ins_sec["Paciente"] > 0)]

                if not df_ins_sec.empty:
                    df_ins_melt = df_ins_sec.melt(
                        id_vars="Sector", value_vars=["Seguro", "Paciente"],
                        var_name="Pagador", value_name="Monto",
                    )
                    fig_ins_stack = px.bar(
                        df_ins_melt, x="Sector", y="Monto", color="Pagador",
                        barmode="stack", text="Monto",
                        color_discrete_map={"Seguro": "#58a6ff", "Paciente": "#f0883e"},
                    )
                    fig_ins_stack.update_traces(
                        texttemplate="₲%{text:,.0f}", textposition="inside", textfont_size=10,
                        hovertemplate="<b>%{x}</b><br>%{data.name}: ₲%{y:,.0f}<extra></extra>",
                    )
                    fig_ins_stack.update_layout(
                        **PLOTLY_LAYOUT, title="Insumos por Sector — Seguro vs. Paciente",
                        height=400,
                        xaxis=dict(title="", tickangle=-35),
                        yaxis=dict(title="Monto (₲)", gridcolor="rgba(48,54,61,0.4)"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                    )
                    st.plotly_chart(fig_ins_stack, use_container_width=True, key="micro_ins_stack")
                else:
                    st.info("Sin datos de insumos por sector con valores > 0.")
            else:
                st.info("Columna 'Sector' no disponible para desglose.")

    # ════════════════════════════════════════════════════════════════════
    # 11C — FLUJO DE CAJA (MÉTODOS DE PAGO)
    # ════════════════════════════════════════════════════════════════════
    with st11_flujo:
        st.markdown("#### 💳 Flujo de Caja — Distribución por Método de Pago")
        st.markdown("Visualiza la liquidez de la clínica según los distintos canales de cobro.")

        has_metodo = "Método de Pago" in df_micro.columns
        has_total_f = "TOTAL" in df_micro.columns

        if has_metodo and has_total_f:
            df_pago = (
                df_micro.groupby("Método de Pago")
                .agg(
                    Ingreso=("TOTAL", "sum"),
                    Operaciones=("TOTAL", "count"),
                )
                .reset_index()
                .sort_values("Ingreso", ascending=False)
            )

            # KPIs
            n_metodos = len(df_pago)
            top_metodo = df_pago.iloc[0]["Método de Pago"] if len(df_pago) else "-"
            top_metodo_pct = (
                df_pago.iloc[0]["Ingreso"] / df_pago["Ingreso"].sum() * 100
                if len(df_pago) and df_pago["Ingreso"].sum() > 0 else 0
            )
            fk1, fk2, fk3 = st.columns(3)
            fk1.metric("💳 Métodos de Pago", f"{n_metodos}")
            fk2.metric("🏆 Canal Principal", f"{top_metodo}")
            fk3.metric("📊 Participación Líder", f"{top_metodo_pct:.1f}%")

            st.markdown("---")

            col_f1, col_f2 = st.columns(2)

            with col_f1:
                # Donut chart
                fig_pago_donut = px.pie(
                    df_pago, names="Método de Pago", values="Ingreso", hole=0.5,
                    color_discrete_sequence=[
                        "#3fb950", "#58a6ff", "#f0883e", "#bc8cff",
                        "#f778ba", "#79c0ff", "#ffa657", "#ff7b72",
                    ],
                )
                fig_pago_donut.update_layout(
                    **PLOTLY_LAYOUT, title="Distribución de Ingresos",
                    height=420, showlegend=True,
                    legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
                )
                fig_pago_donut.update_traces(
                    textinfo="percent+label", textfont_size=11,
                    texttemplate="%{label}<br>%{percent}",
                    hovertemplate="<b>%{label}</b><br>Ingreso: ₲%{value:,.0f}<br>%{percent}<extra></extra>",
                )
                st.plotly_chart(fig_pago_donut, use_container_width=True, key="micro_pago_donut")

            with col_f2:
                # Bar chart for detail
                df_pago_bar = df_pago.sort_values("Ingreso", ascending=True)
                fig_pago_bar = px.bar(
                    df_pago_bar, y="Método de Pago", x="Ingreso", orientation="h",
                    text="Ingreso", color="Ingreso",
                    color_continuous_scale=["#1a1e2e", "#3fb950"],
                )
                fig_pago_bar.update_traces(
                    texttemplate="₲%{text:,.0f}", textposition="outside", textfont_size=11,
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Ingreso: ₲%{x:,.0f}<extra></extra>"
                    ),
                )
                fig_pago_bar.update_layout(
                    **PLOTLY_LAYOUT, title="Ingreso por Canal",
                    height=max(350, len(df_pago_bar) * 45),
                    yaxis=dict(title=""),
                    xaxis=dict(title="Ingresos (₲)", gridcolor="rgba(48,54,61,0.4)"),
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_pago_bar, use_container_width=True, key="micro_pago_bar")

            # Summary table
            with st.expander("📋 Detalle por Método de Pago", expanded=False):
                df_pago_tbl = df_pago.copy()
                df_pago_tbl["% Participación"] = (
                    df_pago_tbl["Ingreso"] / df_pago_tbl["Ingreso"].sum() * 100
                ).apply(lambda v: f"{v:.1f}%")
                df_pago_tbl["Ingreso"] = df_pago_tbl["Ingreso"].apply(lambda v: f"₲ {v:,.0f}")
                st.dataframe(df_pago_tbl, use_container_width=True, hide_index=True)
        else:
            st.info("Columna 'Método de Pago' o 'TOTAL' no disponible para este análisis.")

    # ════════════════════════════════════════════════════════════════════
    # 11D — IMPACTO DE DESCUENTOS
    # ════════════════════════════════════════════════════════════════════
    with st11_desc:
        st.markdown("#### 🏷️ Impacto de Descuentos Comerciales")
        st.markdown("Cuantifica el dinero cedido en descuentos y dónde se concentran las rebajas.")

        total_descuento = df_micro["Descuento"].sum()
        total_rev_desc = df_micro["TOTAL"].sum() if "TOTAL" in df_micro.columns else 0
        pct_desc = (total_descuento / total_rev_desc * 100) if total_rev_desc > 0 else 0
        n_con_desc = (df_micro["Descuento"] > 0).sum()
        pct_estudios_desc = (n_con_desc / len(df_micro) * 100) if len(df_micro) > 0 else 0

        dk1, dk2, dk3, dk4 = st.columns(4)
        dk1.metric("🏷️ Total Descuentos", f"₲ {total_descuento:,.0f}")
        dk2.metric("📉 % sobre Facturación", f"{pct_desc:.2f}%")
        dk3.metric("📋 Estudios con Descuento", f"{n_con_desc:,}")
        dk4.metric("📊 % Estudios con Desc.", f"{pct_estudios_desc:.1f}%")

        st.markdown("---")

        # Sub-tabs: by Sector vs by Month
        desc_tab_sector, desc_tab_mes = st.tabs(["🏢 Por Sector", "📅 Por Mes"])

        with desc_tab_sector:
            if "Sector" in df_micro.columns:
                df_desc_sec = (
                    df_micro[df_micro["Descuento"] > 0]
                    .groupby("Sector")
                    .agg(
                        Total_Descuento=("Descuento", "sum"),
                        Cantidad=("Descuento", "count"),
                    )
                    .reset_index()
                    .sort_values("Total_Descuento", ascending=False)
                )

                if not df_desc_sec.empty:
                    fig_desc_sec = px.bar(
                        df_desc_sec.sort_values("Total_Descuento", ascending=True),
                        y="Sector", x="Total_Descuento", orientation="h",
                        text="Total_Descuento", color="Total_Descuento",
                        color_continuous_scale=[[0, "#1f3a5f"], [0.5, "#bc8cff"], [1, "#f778ba"]],
                    )
                    fig_desc_sec.update_traces(
                        texttemplate="₲%{text:,.0f}", textposition="outside", textfont_size=11,
                        hovertemplate=(
                            "<b>%{y}</b><br>"
                            "Descuentos: ₲%{x:,.0f}<br>"
                            "Operaciones: %{customdata[0]:,}"
                            "<extra></extra>"
                        ),
                        customdata=df_desc_sec.sort_values("Total_Descuento", ascending=True)[["Cantidad"]].values,
                    )
                    fig_desc_sec.update_layout(
                        **PLOTLY_LAYOUT, title="Descuentos por Sector",
                        height=max(380, len(df_desc_sec) * 45),
                        yaxis=dict(title=""),
                        xaxis=dict(title="Descuento Total (₲)", gridcolor="rgba(48,54,61,0.4)"),
                        coloraxis_showscale=False,
                    )
                    st.plotly_chart(fig_desc_sec, use_container_width=True, key="micro_desc_sec")
                else:
                    st.info("No se encontraron descuentos en el período filtrado.")
            else:
                st.info("Columna 'Sector' no disponible.")

        with desc_tab_mes:
            if "Fecha" in df_micro.columns and df_micro["Fecha"].notna().any():
                df_desc_mes = (
                    df_micro[df_micro["Descuento"] > 0]
                    .groupby(pd.Grouper(key="Fecha", freq="ME"))
                    .agg(
                        Total_Descuento=("Descuento", "sum"),
                        Cantidad=("Descuento", "count"),
                    )
                    .reset_index()
                )
                df_desc_mes["Periodo"] = df_desc_mes["Fecha"].dt.strftime("%Y-%m")

                if not df_desc_mes.empty:
                    fig_desc_mes = go.Figure()
                    fig_desc_mes.add_trace(go.Bar(
                        x=df_desc_mes["Periodo"],
                        y=df_desc_mes["Total_Descuento"],
                        name="Descuento",
                        marker=dict(
                            color=df_desc_mes["Total_Descuento"],
                            colorscale=[[0, "#1f3a5f"], [0.5, "#bc8cff"], [1, "#f778ba"]],
                            line=dict(width=0),
                        ),
                        text=df_desc_mes["Total_Descuento"].apply(lambda v: f"₲{v:,.0f}"),
                        textposition="outside",
                        textfont=dict(size=11),
                        hovertemplate=(
                            "<b>%{x}</b><br>"
                            "Descuento: ₲%{y:,.0f}<br>"
                            "Operaciones: %{customdata[0]:,}"
                            "<extra></extra>"
                        ),
                        customdata=df_desc_mes[["Cantidad"]].values,
                    ))
                    fig_desc_mes.add_trace(go.Scatter(
                        x=df_desc_mes["Periodo"],
                        y=df_desc_mes["Cantidad"],
                        name="Operaciones con Desc.",
                        mode="lines+markers",
                        line=dict(color="#f0883e", width=3, dash="dot"),
                        marker=dict(size=8, symbol="diamond"),
                        yaxis="y2",
                        hovertemplate="<b>%{x}</b><br>Operaciones: %{y:,}<extra></extra>",
                    ))
                    fig_desc_mes.update_layout(
                        **PLOTLY_LAYOUT, title="Evolución Mensual de Descuentos",
                        height=450,
                        yaxis=dict(title="Descuento (₲)", gridcolor="rgba(48,54,61,0.4)"),
                        yaxis2=dict(title="Operaciones", overlaying="y", side="right",
                                    gridcolor="rgba(48,54,61,0.1)"),
                        xaxis=dict(gridcolor="rgba(48,54,61,0.4)"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                    )
                    st.plotly_chart(fig_desc_mes, use_container_width=True, key="micro_desc_mes")
                else:
                    st.info("No se encontraron descuentos en el período filtrado.")
            else:
                st.info("Columna 'Fecha' no disponible para evolución temporal.")

# ── TAB 9 — Panel Admin ────────────────────────────────────────────────────
if user_role == "admin":
    if tab9:
        st.markdown("### ⚙️ Administración y Auditoría")
        st.markdown("A continuación, puedes observar el registro de acciones que han realizado los diferentes usuarios (visualizar, acceso, etc.) así como el listado de usuarios con acceso a la plataforma.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📜 Registro de Actividad (Log)")
            logs_df = auth.get_logs()
            st.dataframe(logs_df, use_container_width=True, hide_index=True, height=400)
            
        with col2:
            st.markdown("#### 👥 Usuarios Registrados")
            users_df = auth.get_users()
            st.dataframe(users_df, use_container_width=True, hide_index=True)
            # Download users.json for permanent backup
            users_json_path = "data/users.json"
            if os.path.exists(users_json_path):
                with open(users_json_path, "r", encoding="utf-8") as f:
                    users_data = f.read()
                st.download_button(
                    "💾 Descargar Backup de Usuarios",
                    data=users_data,
                    file_name="users.json",
                    mime="application/json",
                    use_container_width=True,
                )
            st.caption("ℹ️ Los usuarios se guardan en el repositorio y persisten entre reinicios.")

        st.markdown("---")
        st.markdown("#### 🔗 Fusión de Médicos Duplicados")
        st.markdown("Si ves al mismo médico escrito de varias formas (ej. *'CELSO FRETES'* y *'CELSO FRETES RAMIREZ'*), puedes unificarlos permanentemente a un solo nombre.")
        
        aliases_file = "data/aliases_medicos.json"
        aliases_actuales = {}
        if os.path.exists(aliases_file):
            try:
                with open(aliases_file, "r", encoding="utf-8") as f:
                    aliases_actuales = json.load(f)
            except Exception:
                pass

        if "Doctor Tratante" in df.columns:
            doctores_unicos = sorted(df["Doctor Tratante"].dropna().astype(str).unique().tolist())
            
            c_fus1, c_fus2, c_fus3 = st.columns([2, 2, 1])
            with c_fus1:
                doc_destino = st.selectbox("1️⃣ Nombre que se MANTENDRÁ (Final)", ["Selecciona..."] + doctores_unicos, key="dest_trat")
            with c_fus2:
                doc_origen = st.selectbox("2️⃣ Nombre a ELIMINAR/FUSIONAR (Extra)", ["Selecciona..."] + doctores_unicos, key="orig_trat")
            with c_fus3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Fusionar y Aplicar", use_container_width=True, type="primary", key="btn_trat"):
                    if doc_destino != "Selecciona..." and doc_origen != "Selecciona..." and doc_destino != doc_origen:
                        aliases_actuales[doc_origen] = doc_destino
                        os.makedirs(os.path.dirname(aliases_file), exist_ok=True)
                        with open(aliases_file, "w", encoding="utf-8") as f:
                            json.dump(aliases_actuales, f, indent=4)
                        st.success(f"¡Fusionado! '{doc_origen}' ahora operará como '{doc_destino}'.")
                        st.cache_data.clear()
                        st.rerun()
                    elif doc_destino == doc_origen and doc_destino != "Selecciona...":
                        st.warning("Ambos nombres son iguales. Selecciona un nombre a eliminar distinto del destino.")
                    else:
                        st.warning("Selecciones inválidas.")
            
        st.markdown("---")
        st.markdown("#### 🔗 Fusión de Médicos Radiólogos (Informantes)")
        st.markdown("Si ves al mismo radiólogo escrito de varias formas, puedes unificarlos permanentemente a un solo nombre.")
        
        if "Doctor Informante" in df.columns:
            radiologos_unicos = sorted(df["Doctor Informante"].dropna().astype(str).unique().tolist())
            
            c_fus1_r, c_fus2_r, c_fus3_r = st.columns([2, 2, 1])
            with c_fus1_r:
                doc_destino_r = st.selectbox("1️⃣ Nombre que se MANTENDRÁ (Final)", ["Selecciona..."] + radiologos_unicos, key="dest_rad")
            with c_fus2_r:
                doc_origen_r = st.selectbox("2️⃣ Nombre a ELIMINAR/FUSIONAR (Extra)", ["Selecciona..."] + radiologos_unicos, key="orig_rad")
            with c_fus3_r:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Fusionar y Aplicar", use_container_width=True, type="primary", key="btn_rad"):
                    if doc_destino_r != "Selecciona..." and doc_origen_r != "Selecciona..." and doc_destino_r != doc_origen_r:
                        aliases_actuales[doc_origen_r] = doc_destino_r
                        os.makedirs(os.path.dirname(aliases_file), exist_ok=True)
                        with open(aliases_file, "w", encoding="utf-8") as f:
                            json.dump(aliases_actuales, f, indent=4)
                        st.success(f"¡Fusionado! '{doc_origen_r}' operará como '{doc_destino_r}'.")
                        st.cache_data.clear()
                        st.rerun()
                    elif doc_destino_r == doc_origen_r and doc_destino_r != "Selecciona...":
                        st.warning("Ambos nombres son iguales.")
                    else:
                        st.warning("Selecciones inválidas.")

        if aliases_actuales:
            st.markdown("---")
            with st.expander("🛠️ Ver TODAS las Fusiones Activas (Historial y Deshacer)", expanded=False):
                st.info("Aquí aparecen todos los nombres que han sido fusionados, tanto médicos tratantes como radiólogos.")
                for origen, destino in list(aliases_actuales.items()):
                    c_li1, c_li2 = st.columns([4, 1])
                    c_li1.write(f"🗑️ Eliminado: `{origen}` ➡️ 🎯 Operando como: `{destino}`")
                    if c_li2.button("Deshacer", key=f"del_{origen}", use_container_width=True):
                        del aliases_actuales[origen]
                        with open(aliases_file, "w", encoding="utf-8") as f:
                            json.dump(aliases_actuales, f, indent=4)
                        st.cache_data.clear()
                        st.rerun()

