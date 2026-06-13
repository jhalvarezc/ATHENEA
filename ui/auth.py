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
        # 1. Inyectar CSS/HTML animado del fondo (Lluvia de Luz) y Estilos Custom
        st.markdown("""
        <style>
        /* Deshabilitar Sidebar y cabeceras nativas en el login */
        [data-testid="stSidebar"] { display: none !important; }
        header { display: none !important; }
        .block-container {
            max-width: 480px !important;
            padding-top: 15vh !important;
            padding-bottom: 5vh !important;
        }
        
        /* Fondo con gradiente y animación de lluvia de luz */
        .login-rain-bg {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(180deg, #020205 0%, #08031d 50%, #010006 100%) !important;
            z-index: -1000;
            overflow: hidden;
        }
        
        /* Hilos de luz descendentes (light rain) */
        .rain-streak {
            position: absolute;
            width: 1px;
            height: 150px;
            background: linear-gradient(to bottom, rgba(56, 189, 248, 0) 0%, rgba(56, 189, 248, 0.6) 60%, rgba(139, 92, 246, 0.6) 80%, rgba(236, 72, 153, 0) 100%);
            animation: fallAnimation 4s linear infinite;
        }
        
        @keyframes fallAnimation {
            0% { transform: translateY(-150px); opacity: 0; }
            10% { opacity: 0.8; }
            90% { opacity: 0.8; }
            100% { transform: translateY(110vh); opacity: 0; }
        }
        
        /* Variaciones de velocidad y posición */
        .rain-streak:nth-child(1) { left: 8%; animation-duration: 3.2s; animation-delay: 0.2s; }
        .rain-streak:nth-child(2) { left: 18%; animation-duration: 4.5s; animation-delay: 1.5s; }
        .rain-streak:nth-child(3) { left: 28%; animation-duration: 2.8s; animation-delay: 0.5s; }
        .rain-streak:nth-child(4) { left: 42%; animation-duration: 5s; animation-delay: 2s; }
        .rain-streak:nth-child(5) { left: 56%; animation-duration: 3s; animation-delay: 0.1s; }
        .rain-streak:nth-child(6) { left: 68%; animation-duration: 4.2s; animation-delay: 1.2s; }
        .rain-streak:nth-child(7) { left: 78%; animation-duration: 2.5s; animation-delay: 0.8s; }
        .rain-streak:nth-child(8) { left: 88%; animation-duration: 3.8s; animation-delay: 2.3s; }
        .rain-streak:nth-child(9) { left: 96%; animation-duration: 3.4s; animation-delay: 0.4s; }

        /* Glassmorphism Login Form Container */
        div[data-testid="stForm"] {
            background: rgba(15, 23, 42, 0.45) !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 20px !important;
            padding: 32px !important;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6) !important;
            margin-top: 1rem;
        }
        
        /* Ocultar el texto de ayuda del form 'Press Enter to submit form' */
        [data-testid="stFormInstruction"] {
            display: none !important;
        }
        
        /* Botones de acción del Login */
        div[data-testid="stFormSubmitButton"] button {
            background: #ffffff !important;
            color: #0f172a !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            letter-spacing: 0.02em !important;
            padding: 12px 24px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(255, 255, 255, 0.15) !important;
            margin-top: 10px !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(56, 189, 248, 0.4) !important;
            background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%) !important;
        }
        
        /* Inputs del Login - Estilo Limpio sin bordes dobles */
        div[data-baseweb="input"] {
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 10px !important;
            background-color: rgba(15, 23, 42, 0.4) !important;
            transition: all 0.2s ease-in-out !important;
        }
        div[data-baseweb="input"] > div {
            background-color: transparent !important;
            border: none !important;
        }
        div[data-baseweb="input"]:focus-within {
            border-color: #38bdf8 !important;
            box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2) !important;
        }
        input {
            color: #ffffff !important;
            caret-color: #38bdf8 !important;
        }
        </style>

        <div class="login-rain-bg">
            <div class="rain-streak"></div>
            <div class="rain-streak"></div>
            <div class="rain-streak"></div>
            <div class="rain-streak"></div>
            <div class="rain-streak"></div>
            <div class="rain-streak"></div>
            <div class="rain-streak"></div>
            <div class="rain-streak"></div>
            <div class="rain-streak"></div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            st.markdown("<p style='text-align:center; font-size:1.1rem; font-weight:700; margin-bottom:15px; color:#ffffff;'>🔐 AUTENTICACIÓN LOGÍSTICA</p>", unsafe_allow_html=True)
            username = st.text_input("Usuario", placeholder="Ingresa tu usuario...", help="Ingresa tu nombre de usuario para iniciar sesión.")
            password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña...", help="Ingresa tu contraseña asociada a tu cuenta.")
            submit = st.form_submit_button("Ingresar", use_container_width=True, help="Haz clic para autenticar y acceder al panel principal.")
            
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
