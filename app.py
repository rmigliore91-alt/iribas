import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
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
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

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
# CACHED AGGREGATION HELPERS (Tab 6 performance)
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
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


@st.cache_data
def compute_detail_all(df_rad_ser):
    """Pre-compute per-radiologist + per-sector breakdown for all radiologists at once."""
    df = df_rad_ser
    detail = (
        df.groupby(["Doctor Informante", "Sector"])
        .agg(Estudios=("Sector", "count"), Puntaje=("Puntaje_Dificultad", "sum"))
        .reset_index()
    )
    return detail


@st.cache_data
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


@st.cache_data
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
    cleaned = (
        series.astype(str)
        .str.strip()
        .str.replace("-", "", regex=False)
        .str.replace(".", "", regex=False)    # remove thousands dots if any
        .str.replace(",", "", regex=False)    # remove thousands commas
        .str.replace("$", "", regex=False)
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce").fillna(0)


# ──────────────────────────────────────────────────────────────────────────────
# DATA LOADING & PREPROCESSING
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(file):
    """Load CSV adapted to the actual file format from the medical center."""
    df = pd.read_csv(file, encoding="utf-8-sig")  # handles BOM

    # ── Strip whitespace from column names ───────────────────────────────
    df.columns = df.columns.str.strip()

    # ── Handle duplicate 'Hora' columns ──────────────────────────────────
    cols = list(df.columns)
    hora_count = 0
    for i, c in enumerate(cols):
        if c == "Hora":
            hora_count += 1
            if hora_count == 2:
                cols[i] = "Hora_Num"
    df.columns = cols

    # ── Strip whitespace from all string values ─────────────────────────
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    # ── Drop fully empty trailing columns ────────────────────────────────
    df = df.dropna(axis=1, how="all")

    # ── Fecha: parse D/MM/YY format ──────────────────────────────────────
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True, errors="coerce")
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
        df["Doctor Informante"] = df["Doctor Informante"].str.upper().str.strip()

    # ── Difficulty score per study ───────────────────────────────────────
    if "Sector" in df.columns:
        df["Puntaje_Dificultad"] = df["Sector"].map(DIFICULTAD_SECTOR).fillna(DIFICULTAD_DEFAULT)

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
# SIDEBAR – DATA UPLOAD & FILTERS
# ──────────────────────────────────────────────────────────────────────────────
CACHE_FILE_PATH = "data/last_uploaded.csv"

with st.sidebar:
    if user_role == "admin":
        st.markdown("## 📂 Gestión de Datos (Admin)")
        uploaded_file = st.file_uploader(
            "Sube un nuevo archivo CSV consolidado",
            type=["csv"],
            help="Sustituirá la base de datos actual para todos los usuarios."
        )

        if uploaded_file is not None:
            os.makedirs(os.path.dirname(CACHE_FILE_PATH), exist_ok=True)
            with open(CACHE_FILE_PATH, "wb") as f:
                f.write(uploaded_file.getbuffer())
            file_to_load = uploaded_file
            auth.log_action(user_email, "Subió un nuevo archivo CSV")
        elif os.path.exists(CACHE_FILE_PATH):
            file_to_load = CACHE_FILE_PATH
            st.success("✅ Base de datos activa y en línea.")
        else:
            file_to_load = None
            
        if file_to_load is not None:
            st.markdown("---")
            if st.button("🗑️ Borrar Datos y Reiniciar App"):
                if os.path.exists(CACHE_FILE_PATH):
                    os.remove(CACHE_FILE_PATH)
                auth.log_action(user_email, "Eliminó la base de datos CSV")
                st.rerun()
    else:
        st.markdown("## 📂 Estado de Datos")
        if os.path.exists(CACHE_FILE_PATH):
            file_to_load = CACHE_FILE_PATH
            st.success("✅ Base de datos activa y en línea.")
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
# LOAD & FILTER
# ──────────────────────────────────────────────────────────────────────────────
df = load_data(file_to_load)
df_filtered = df.copy()

with st.sidebar:
    st.markdown("---")
    st.markdown("## 🎛️ Filtros Globales")

    # Date range
    if "Fecha" in df.columns and df["Fecha"].notna().any():
        min_d = df["Fecha"].min().date()
        max_d = df["Fecha"].max().date()
        rango = st.date_input("📅 Rango de Fechas", [min_d, max_d])
        if len(rango) == 2:
            df_filtered = df_filtered[
                (df_filtered["Fecha"].dt.date >= rango[0])
                & (df_filtered["Fecha"].dt.date <= rango[1])
            ]

    # Mes
    if "Mes" in df.columns:
        meses_disp = sorted(df["Mes"].dropna().unique())
        sel_meses = st.multiselect("🗓️ Mes", meses_disp, default=meses_disp)
        if sel_meses:
            df_filtered = df_filtered[df_filtered["Mes"].isin(sel_meses)]

    # Sector
    if "Sector" in df.columns:
        sectores = sorted(df["Sector"].dropna().unique())
        sel_sectores = st.multiselect("🏷️ Sector", sectores, default=sectores)
        if sel_sectores:
            df_filtered = df_filtered[df_filtered["Sector"].isin(sel_sectores)]

    # Seguro
    if "Seguro" in df.columns:
        seguros = sorted(df["Seguro"].dropna().unique())
        sel_seguros = st.multiselect("🛡️ Seguro", seguros, default=seguros)
        if sel_seguros:
            df_filtered = df_filtered[df_filtered["Seguro"].isin(sel_seguros)]

    # Doctor Tratante
    if "Doctor Tratante" in df.columns:
        doctores = sorted(df["Doctor Tratante"].dropna().unique())
        sel_docs = st.multiselect("👨‍⚕️ Doctor Tratante", doctores, default=doctores)
        if sel_docs:
            df_filtered = df_filtered[df_filtered["Doctor Tratante"].isin(sel_docs)]

    st.markdown("---")
    st.caption(f"Registros filtrados: **{len(df_filtered):,}** / {len(df):,}")

# ── Empty-filter guard ───────────────────────────────────────────────────────
if df_filtered.empty:
    st.warning("⚠️ No hay datos para los filtros seleccionados. Ajusta los parámetros en la barra lateral.")
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────────────────────────────────────
# Determine tabs based on role
tab_titles = [
    "📈 Evolución Histórica",
    "🔥 Mapa de Calor",
    "💰 Financiero",
    "🏢 Rendimiento Sector",
    "🩺 Red de Derivación",
    "🔬 Radiólogos Informantes",
    "🛡️ Ranking Seguros",
    "⚖️ Comparativa",
]

if user_role == "admin":
    tab_titles.append("⚙️ Panel Admin")

tabs = st.tabs(tab_titles)
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = tabs[:8]
if user_role == "admin":
    tab9 = tabs[8]

# ── TAB 1 — Evolución Histórica ─────────────────────────────────────────────
with tab1:
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
with tab2:
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
with tab3:
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

# ── TAB 4 — Rendimiento por Sector ──────────────────────────────────────────
with tab4:
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
with tab5:
    st.markdown("### Top 15 Doctores Tratantes — Volumen y Facturación")
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
with tab6:
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
with tab7:
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

# ── TAB 8 — Comparativa entre Períodos ─────────────────────────────────────
with tab8:
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
                start_a, end_a = rango_a
                start_b, end_b = rango_b
                
                df_a = df[(df["Fecha"].dt.date >= start_a) & (df["Fecha"].dt.date <= end_a)]
                df_b = df[(df["Fecha"].dt.date >= start_b) & (df["Fecha"].dt.date <= end_b)]

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

# ── TAB 9 — Panel Admin ────────────────────────────────────────────────────
if user_role == "admin":
    with tab9:
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

