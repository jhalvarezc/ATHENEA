# dashboard/map_ui.py - Componentes de mapas y visualización geográfica
import streamlit as st
import pandas as pd
import pydeck as pdk
import requests

COORDENADAS_CIUDADES = {
    'BOGOTA': {'lat': 4.7110, 'lon': -74.0721},
    'MEDELLIN': {'lat': 6.2442, 'lon': -75.5812},
    'CALI': {'lat': 3.4516, 'lon': -76.5320},
    'BARRANQUILLA': {'lat': 10.9685, 'lon': -74.7813},
    'BUCARAMANGA': {'lat': 7.1254, 'lon': -73.1198},
    'CARTAGENA': {'lat': 10.3910, 'lon': -75.4794},
    'PEREIRA': {'lat': 4.8133, 'lon': -75.6961}
}

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

def renderizar_mapa(df_filtrado):
    """
    Dibuja un mapa interactivo con PyDeck trazando las rutas de la guía seleccionada.
    """
    st.markdown("<h2 style='font-size:1.5rem;'>🗺️ Monitoreo de Red Geográfica</h2>", unsafe_allow_html=True)
    
    if df_filtrado is None or df_filtrado.empty:
        st.warning("No hay datos geográficos disponibles.")
        return

    list_guias = sorted(df_filtrado['guia_id'].unique().tolist())
    
    if list_guias:
        guia_seleccionada = st.selectbox("🎯 Selecciona una guía para trazar ruta detallada:", list_guias)
        fila_guia = df_filtrado[df_filtrado['guia_id'] == guia_seleccionada].iloc[0]
        
        ciudad_orig = str(fila_guia['origen']).split('/')[0].strip().upper()
        ciudad_dest = str(fila_guia['destino']).split('/')[0].strip().upper()
        
        st.info(f"📍 **Detalle Actual:** {fila_guia['guia_id']} | **Origen:** {ciudad_orig} | **Destino:** {ciudad_dest} | **Flete:** ${fila_guia['costo_flete']:,} COP")
        
        # Obtener coordenadas de forma segura
        orig_lat = COORDENADAS_CIUDADES.get(ciudad_orig, COORDENADAS_CIUDADES["BOGOTA"])["lat"]
        orig_lon = COORDENADAS_CIUDADES.get(ciudad_orig, COORDENADAS_CIUDADES["BOGOTA"])["lon"]
        dest_lat = COORDENADAS_CIUDADES.get(ciudad_dest, COORDENADAS_CIUDADES["BOGOTA"])["lat"]
        dest_lon = COORDENADAS_CIUDADES.get(ciudad_dest, COORDENADAS_CIUDADES["BOGOTA"])["lon"]
        
        coordenadas_carretera = obtener_ruta_calle(orig_lon, orig_lat, dest_lon, dest_lat)
        
        if coordenadas_carretera:
            # Color de la línea según estado de auditoría
            estado_aud = str(fila_guia.get('estado_auditoria', 'riesgo_bajo')).lower()
            if estado_aud == 'riesgo_alto':
                color_linea = [239, 68, 68, 255] # Rojo
            elif estado_aud == 'riesgo_medio':
                color_linea = [242, 140, 15, 255] # Naranja
            else:
                color_linea = [88, 166, 255, 255] # Azul
                
            df_ruta_mapa = pd.DataFrame([{'path': coordenadas_carretera, 'color': color_linea}])
            
            capa_camino_carreteras = pdk.Layer(
                "PathLayer", 
                data=df_ruta_mapa, 
                get_path="path", 
                get_color="color", 
                width_scale=20, 
                width_min_pixels=4
            )
            
            view_state = pdk.ViewState(
                latitude=(orig_lat + dest_lat) / 2,
                longitude=(orig_lon + dest_lon) / 2,
                zoom=5.3,
                pitch=20
            )
            
            st.pydeck_chart(pdk.Deck(
                map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json", 
                initial_view_state=view_state, 
                layers=[capa_camino_carreteras]
            ))
        else:
            st.error("⚠️ No se pudo trazar la ruta terrestre.")
    else:
        st.warning("No existen registros válidos con las restricciones aplicadas.")
