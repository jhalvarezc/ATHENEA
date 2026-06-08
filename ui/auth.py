# ui/auth.py - Módulo de Autenticación y Control de Roles para ATHENEA
import streamlit as st
import time

# Base de datos simulada de usuarios
USUARIOS = {
    "admin": {"clave": "admin123", "rol": "admin"},
    "operador": {"clave": "operador123", "rol": "basico"}
}

def requerir_autenticacion():
    """
    Inicializa el estado de autenticación y bloquea la UI con un formulario de login
    si el usuario no está autenticado. Retorna el rol del usuario autenticado.
    """
    # Inicialización de variables de sesión
    if "usuario_autenticado" not in st.session_state:
        st.session_state["usuario_autenticado"] = False
    if "rol" not in st.session_state:
        st.session_state["rol"] = None

    if not st.session_state["usuario_autenticado"]:
        st.markdown("### 🔐 Iniciar Sesión - ATHENEA")
        with st.form("login_form"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar", use_container_width=True)
            
            if submit:
                user_info = USUARIOS.get(username)
                if user_info and user_info["clave"] == password:
                    st.session_state["usuario_autenticado"] = True
                    st.session_state["rol"] = user_info["rol"]
                    st.success(f"¡Bienvenido, {username.capitalize()}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
        st.stop()

    return st.session_state["rol"]
