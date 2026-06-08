# drivers/osrm_driver.py - Motor de georuta OSRM para ATHENEA
import streamlit as st
import requests

@st.cache_data(show_spinner=False)
def obtener_ruta_calle(lon_origen, lat_origen, lon_destino, lat_destino):
    """Obtiene el trazado real por carreteras usando OSRM."""
    url = f"http://router.project-osrm.org/route/v1/driving/{lon_origen},{lat_origen};{lon_destino},{lat_destino}?overview=full&geometries=geojson"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get('code') == 'Ok':
            return data['routes'][0]['geometry']['coordinates']
    except Exception:
        pass
    # Backup por si falla la API: Línea recta original
    return [[lon_origen, lat_origen], [lon_destino, lat_destino]]
