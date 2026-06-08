# modules/ui_styles.py
import streamlit as st

def aplicar_estilos_dark():
    """Inyecta el CSS avanzado para la interfaz empresarial."""
    st.markdown("""
    <style>
        .stApp { background-color: #0b0f19; }
        [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #1f2937; }
        [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 18px; }
        h1, h2, h3, p, label { color: #e6edf3 !important; font-family: 'Inter', sans-serif; }
        .titulo-athenea { color: #e6edf3; font-weight: 800; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

def renderizar_encabezado():
    """Muestra el Header corporativo de ATHENEA."""
    st.markdown("<h1 class='titulo-athenea'>🧠 ATHENEA - Centro de Inteligencia Logística</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8b949e; margin-top:-10px;'>Auditoría de despachos y tránsito con geolocalización de rutas reales.</p>", unsafe_allow_html=True)
    st.markdown("---")