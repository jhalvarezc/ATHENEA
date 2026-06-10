# app.py - Dashboard Modularizado ATHENEA (Orquestador Central de UI)
import streamlit as st
from ui.styles import aplicar_estilos_dark, renderizar_encabezado
from ui.auth import requerir_autenticacion

# 1. Configuración de Ventana e Inyección de Estilos HTML/CSS
st.set_page_config(
    page_title="ATHENEA Dashboard", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)
aplicar_estilos_dark()
renderizar_encabezado()

# ==========================================
# 🔒 SISTEMA DE LOGIN BLOQUEANTE
# ==========================================
rol_usuario = requerir_autenticacion()

# Botón de cierre de sesión en la barra lateral
st.sidebar.markdown(f"**Rol actual:** `{st.session_state.get('rol')}`")
st.sidebar.markdown('<div class="logout-btn-container">', unsafe_allow_html=True)
if st.sidebar.button("🔓 Cerrar Sesión", use_container_width=True, help="Cierra tu sesión actual y vuelve a la pantalla de inicio"):
    st.session_state["usuario_autenticado"] = False
    st.session_state["rol"] = None
    st.rerun()
st.sidebar.markdown('</div>', unsafe_allow_html=True)
st.sidebar.markdown("---")

# Tarjeta de Estado del Motor de Inferencia (Diseño Premium & Animación Pulse)
st.sidebar.markdown("""
<div class="engine-status-card">
    <div class="pulse-container">
        <span class="pulse-dot"></span>
    </div>
    <div class="status-details">
        <span class="status-title">Motor de Inferencia</span>
        <span class="status-name">ATHENEA : Activo</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 🎛️ CONTROL DE VISTAS POR ROL
# ==========================================
if rol_usuario == "basico":
    from ui.view_operador import renderizar_vista_operador
    renderizar_vista_operador()
elif rol_usuario == "admin":
    from ui.view_admin import renderizar_vista_admin
    renderizar_vista_admin(rol_usuario)