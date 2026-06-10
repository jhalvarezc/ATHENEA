# ui/styles.py - Estilos e información geográfica para la interfaz de ATHENEA
import streamlit as st

COORDENADAS_CIUDADES = {
    'BOGOTA': {'lat': 4.7110, 'lon': -74.0721},
    'MEDELLIN': {'lat': 6.2442, 'lon': -75.5812},
    'CALI': {'lat': 3.4516, 'lon': -76.5320},
    'BARRANQUILLA': {'lat': 10.9685, 'lon': -74.7813},
    'BUCARAMANGA': {'lat': 7.1254, 'lon': -73.1198},
    'CARTAGENA': {'lat': 10.3910, 'lon': -75.4794},
    'PEREIRA': {'lat': 4.8133, 'lon': -75.6961}
}

def aplicar_estilos_dark():
    """Inyecta el CSS avanzado para la interfaz empresarial desde ui/styles.css."""
    import os
    ruta_css = os.path.join(os.path.dirname(__file__), "styles.css")
    try:
        if os.path.exists(ruta_css):
            with open(ruta_css, "r", encoding="utf-8") as f:
                css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception:
        pass

def renderizar_encabezado():
    """Muestra el Header corporativo de ATHENEA."""
    st.markdown("""
    <div style="padding: 1.5rem 0; margin-bottom: 2rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); position: relative;">
        <!-- Glowing light bar above title -->
        <div style="position: absolute; bottom: -1px; left: 0; width: 60px; height: 1px; background: #38bdf8; box-shadow: 0 0 10px #38bdf8;"></div>
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
            <div>
                <h1 style="font-family: 'Outfit', sans-serif !important; font-size: 2.8rem !important; font-weight: 900 !important; margin: 0 !important; letter-spacing: -0.03em !important; background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #6366f1 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; display: flex; align-items: center; gap: 14px;">
                    <span style="-webkit-text-fill-color: initial; filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.3));">🧠</span> ATHENEA
                </h1>
                <p style="color: #94a3b8; font-size: 1.05rem; margin-top: 0.5rem !important; margin-bottom: 0 !important; font-weight: 500; font-family: 'Plus Jakarta Sans', sans-serif;">
                    Centro de Inteligencia Logística <span style="color: #6366f1;">&bull;</span> Motor de Auditoría de Inferencia IA
                </p>
            </div>
            <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 8px 16px; border-radius: 12px; display: flex; align-items: center; gap: 8px; backdrop-filter: blur(4px);">
                <span style="width: 8px; height: 8px; background-color: #10b981; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px #10b981;"></span>
                <span style="font-size: 0.75rem; font-weight: 700; color: #a7f3d0; letter-spacing: 0.05em; text-transform: uppercase;">Servidor Activo</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def normalizar_ciudad(nombre):
    """Normaliza el nombre de la ciudad eliminando acentos/tildes y convirtiendo a mayúsculas."""
    if not nombre:
        return ""
    import unicodedata
    s = unicodedata.normalize('NFKD', str(nombre)).encode('ASCII', 'ignore').decode('utf-8')
    return s.strip().upper()
