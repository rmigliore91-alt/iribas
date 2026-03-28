import streamlit as st
import auth

def init_sidebar_auth():
    with st.sidebar:
        st.markdown("### 🔐 Sesión Activa")
        st.markdown(f"👤 **{st.session_state['user']['email']}**")
        
        role_indicator = "👑 Administrador" if st.session_state["user"]["role"] == "admin" else "👀 Visor"
        st.markdown(f"🔰 **Rol:** `{role_indicator}`")
        
        if st.button("Cerrar Sesión", use_container_width=True):
            auth.log_action(st.session_state["user"]["email"], "Cerró sesión")
            st.session_state["user"] = None
            st.rerun()
        st.markdown("---")
