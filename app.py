# app.py - Dashboard Modularizado ATHENEA (Orquestador Central de UI)
import streamlit as st
import pandas as pd
import pydeck as pdk

# Importación segura de tus nuevos componentes modulares
from modules.ui_styles import aplicar_estilos_dark, renderizar_encabezado
from modules.osrm_engine import obtener_ruta_calle
from modules.prolog_engine import consultar_regla
from modules.data_manager import sincronizar_datos

# 1. Configuración de Ventana e Inyección de Estilos HTML/CSS
st.set_page_config(
    page_title="ATHENEA Dashboard", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)
aplicar_estilos_dark()
renderizar_encabezado()

# Diccionario de coordenadas por defecto para ciudades de Colombia (Blindaje en caso de NaN)
COORDENADAS_CIUDADES = {
    "BOGOTA": {"lat": 4.6097, "lon": -74.0817},
    "MEDELLIN": {"lat": 6.2442, "lon": -75.5812},
    "CALI": {"lat": 3.4516, "lon": -76.5320},
    "BARRANQUILLA": {"lat": 10.9685, "lon": -74.7813},
    "BUCARAMANGA": {"lat": 7.1254, "lon": -73.1198},
    "CARTAGENA": {"lat": 10.3910, "lon": -75.4794},
    "PEREIRA": {"lat": 4.8133, "lon": -75.6961}
}

try:
    # 2. Sincronización Unificada de Datos (Data Lake CSV + PDFs Extraídos)
    datos_unificados = sincronizar_datos()
    
    if datos_unificados is None or (isinstance(datos_unificados, pd.DataFrame) and datos_unificados.empty):
        st.warning("⚠️ No se detectaron registros válidos en la base de datos unificada.")
        st.stop()

    # --- 🛡️ SUPER BLINDAJE CONTRA KEYERROR Y TIPOS DE DATOS ---
    if 'fuente' not in datos_unificados.columns:
        datos_unificados['fuente'] = 'Data_Lake_CSV'
    datos_unificados['fuente'] = datos_unificados['fuente'].fillna('Data_Lake_CSV')
    datos_unificados['guia'] = datos_unificados['guia'].astype(str).str.strip()
    # ------------------------------------------------------------------

    # 3. Consulta Maestra de Diagnósticos en el Motor Prolog
    resultados_prolog = consultar_regla("analisis_ruta_completa(Guia, Origen, Destino, Diagnostico, fecha(7, 6, 2026))")
    
    dict_diagnosticos = {}
    for r in resultados_prolog:
        guia_val = r['Guia'].decode('utf-8') if isinstance(r['Guia'], bytes) else str(r['Guia'])
        diag_val = r['Diagnostico'].decode('utf-8') if isinstance(r['Diagnostico'], bytes) else str(r['Diagnostico'])
        dict_diagnosticos[guia_val.strip()] = diag_val
        
    datos_unificados['diagnostico_ia'] = datos_unificados['guia'].map(dict_diagnosticos).fillna('en_verificacion')

    # 4. Panel Control de Operaciones (Sidebar)
    st.sidebar.markdown("<h2 style='font-size:1.2rem; color:#58a6ff;'>🔍 Controles de Operación</h2>", unsafe_allow_html=True)
    busqueda_guia = st.sidebar.text_input("Buscar código de guía / remisión:", "").strip()
    
    fuentes_disponibles = datos_unificados['fuente'].unique().tolist()
    fuentes_sel = st.sidebar.multiselect("Filtrar por Origen de Datos:", fuentes_disponibles, default=fuentes_disponibles)
    
    estados_disponibles = datos_unificados['estado'].unique().tolist() if 'estado' in datos_unificados.columns else ['en_ruta']
    estados_sel = st.sidebar.multiselect("Filtrar por Estado Lógico:", estados_disponibles, default=estados_disponibles)
    
    ciudades_disponibles = datos_unificados['destino'].unique().tolist() if 'destino' in datos_unificados.columns else []
    ciudades_sel = st.sidebar.multiselect("Filtrar por Destino:", ciudades_disponibles, default=ciudades_disponibles)
    
    max_flete = int(datos_unificados['costo_flete'].max()) if 'costo_flete' in datos_unificados.columns else 100000
    flete_minimo = st.sidebar.slider("Filtrar fletes mayores a ($):", 0, max_flete, 0)

    datos_filtrados = datos_unificados[
        (datos_unificados['fuente'].isin(fuentes_sel)) &
        (datos_unificados['estado'].isin(estados_sel)) &
        (datos_unificados['destino'].isin(ciudades_sel)) &
        (datos_unificados['costo_flete'] >= flete_minimo)
    ]
    
    if busqueda_guia:
        datos_filtrados = datos_filtrados[datos_filtrados['guia'].str.contains(busqueda_guia, case=False)]

    st.sidebar.markdown("---")
    st.sidebar.success("🟢 ATHENEA Inference Engine: Activo")

    # 5. Panel de Control de Indicadores (KPIs Dinámicos)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("📦 Total Líneas Auditadas", f"{len(datos_filtrados):,}")
    kpi2.metric("📄 Guías desde PDFs (OCR)", len(datos_filtrados[datos_filtrados['fuente'] == 'PDF_Digitalizado']))
    kpi3.metric("⏳ Retrasos Logísticos", len(datos_filtrados[datos_filtrados['diagnostico_ia'].isin(['retraso_despacho', 'retraso_transporte'])]))
    kpi4.metric("🚨 Anomalías Críticas", len(datos_filtrados[datos_filtrados['diagnostico_ia'] == 'critico_financiero']))

    st.markdown("---")

    # 6. Monitoreo Geográfico de Redes y Canales (Mapa + Gráfico)
    st.markdown("<h2 style='font-size:1.5rem;'>🗺️ Monitoreo de Red Geográfica</h2>", unsafe_allow_html=True)
    mapa_col, graf_col = st.columns([5, 3])

    list_guias = sorted(datos_filtrados['guia'].unique().tolist())

    with mapa_col:
        if list_guias:
            guia_seleccionada = st.selectbox("🎯 Selecciona una guía para trazar ruta detallada:", list_guias)
            fila_guia = datos_filtrados[datos_filtrados['guia'] == guia_seleccionada].iloc[0]
            
            st.info(f"📍 **Detalle Actual:** {fila_guia['guia']} | **Origen:** {str(fila_guia['origen']).upper()} | **Destino:** {str(fila_guia['destino']).upper()} | **Flete:** ${fila_guia['costo_flete']:,} COP | **Fuente:** {fila_guia['fuente']}")
            
            # --- 🛡️ BLINDAJE GEOGRÁFICO CONTRA COORDENADAS NaN ---
            try:
                ciudad_orig = str(fila_guia['origen']).split('/')[0].strip().upper()
                ciudad_dest = str(fila_guia['destino']).split('/')[0].strip().upper()

                if 'origen_latitude' not in fila_guia or pd.isna(fila_guia['origen_latitude']) or float(fila_guia['origen_latitude']) == 0:
                    orig_lat = COORDENADAS_CIUDADES.get(ciudad_orig, COORDENADAS_CIUDADES["BOGOTA"])["lat"]
                    orig_lon = COORDENADAS_CIUDADES.get(ciudad_orig, COORDENADAS_CIUDADES["BOGOTA"])["lon"]
                else:
                    orig_lat = float(fila_guia['origen_latitude'])
                    orig_lon = float(fila_guia['origen_longitude'])

                if 'destino_latitude' not in fila_guia or pd.isna(fila_guia['destino_latitude']) or float(fila_guia['destino_latitude']) == 0:
                    dest_lat = COORDENADAS_CIUDADES.get(ciudad_dest, COORDENADAS_CIUDADES["BOGOTA"])["lat"]
                    dest_lon = COORDENADAS_CIUDADES.get(ciudad_dest, COORDENADAS_CIUDADES["BOGOTA"])["lon"]
                else:
                    dest_lat = float(fila_guia['destino_latitude'])
                    dest_lon = float(fila_guia['destino_longitude'])
            except Exception:
                orig_lat, orig_lon = 4.6097, -74.0817
                dest_lat, dest_lon = 6.2442, -75.5812
            # ----------------------------------------------------

            coordenadas_carretera = obtener_ruta_calle(orig_lon, orig_lat, dest_lon, dest_lat)
            color_linea = [242, 140, 15, 255] if fila_guia['fuente'] == 'PDF_Digitalizado' else [88, 166, 255, 255]

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
            st.warning("No existen registros válidos con las restricciones aplicadas en los controles.")

    with graf_col:
        st.markdown("<p style='color: #8b949e; font-weight:bold;'>Volumen de Carga por Canal de Captura</p>", unsafe_allow_html=True)
        if not datos_filtrados.empty:
            st.bar_chart(datos_filtrados['fuente'].value_counts(), color="#f28c0f")
        else:
            st.caption("No hay datos para graficar con los filtros actuales.")

    # 7. Tablas de Control de Auditorías Específicas
    st.markdown("---")
    columnas_mostrar = ['guia', 'origen', 'destino', 'estado', 'costo_flete', 'diagnostico_ia', 'fuente']
    
    f2_A, f2_B = st.columns(2)
    with f2_A:
        st.markdown("<h3 style='font-size:1.1rem; color:#ef4444;'>🚨 Auditoría de Riesgos y Alertas Críticas</h3>", unsafe_allow_html=True)
        df_alertas = datos_filtrados[datos_filtrados['diagnostico_ia'] == 'critico_financiero'][columnas_mostrar]
        st.dataframe(df_alertas, use_container_width=True)
        
    with f2_B:
        st.markdown("<h3 style='font-size:1.1rem; color:#3b82f6;'>📋 Documentos Nuevos en Revisión Digital (PDF)</h3>", unsafe_allow_html=True)
        df_revisiones = datos_filtrados[datos_filtrados['fuente'] == 'PDF_Digitalizado'][columnas_mostrar]
        st.dataframe(df_revisiones, use_container_width=True)

    # 8. Repositorio de Trazabilidad Total Completo
    st.markdown("---")
    st.markdown("<h2 style='font-size:1.4rem;'>📋 Repositorio Central de Trazabilidad Logística</h2>", unsafe_allow_html=True)
    st.dataframe(datos_filtrados[columnas_mostrar], use_container_width=True)

# Aquí cerramos de manera limpia el bloque try-except
except Exception as e:
    st.error(f"Error general en la orquestación modular: {e}")