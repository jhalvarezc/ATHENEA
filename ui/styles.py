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
    <div style="padding: 1.5rem 0 1rem 0; margin-bottom: 1.5rem; border-bottom: 1px solid rgba(255, 255, 255, 0.06);">
        <h1 style="font-size: 2.6rem !important; font-weight: 800 !important; margin: 0 !important; letter-spacing: -0.03em !important; background: linear-gradient(135deg, #38bdf8 0%, #3b82f6 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; display: flex; align-items: center; gap: 12px;">
            <span style="-webkit-text-fill-color: initial;">🧠</span> ATHENEA
        </h1>
        <p style="color: #94a3b8; font-size: 1.1rem; margin-top: 0.4rem !important; margin-bottom: 0 !important; font-weight: 500;">
            Centro de Inteligencia Logística &bull; Motor de Auditoría Inferencia
        </p>
    </div>
    """, unsafe_allow_html=True)

def normalizar_ciudad(nombre):
    """Normaliza el nombre de la ciudad eliminando acentos/tildes y convirtiendo a mayúsculas."""
    if not nombre:
        return ""
    import unicodedata
    s = unicodedata.normalize('NFKD', str(nombre)).encode('ASCII', 'ignore').decode('utf-8')
    return s.strip().upper()
