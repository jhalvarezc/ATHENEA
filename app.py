# app.py - Dashboard Modularizado ATHENEA (Orquestador Central de UI)
import streamlit as st
import pandas as pd
import pydeck as pdk

# Importación segura de tus componentes modulares
from ui.styles import aplicar_estilos_dark, renderizar_encabezado, COORDENADAS_CIUDADES
from drivers.osrm_driver import obtener_ruta_calle
from drivers.prolog_driver import consultar_regla
from storage.csv_manager import sincronizar_datos

# 1. Configuración de Ventana e Inyección de Estilos HTML/CSS
st.set_page_config(
    page_title="ATHENEA Dashboard", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)
aplicar_estilos_dark()
renderizar_encabezado()

# Ya importado arriba desde ui.styles

# Sugerencia: Mover COORDENADAS_CIUDADES a un archivo config/geo_config.py
# Ya importado arriba desde ui.styles

try:
    # 2. Sincronización Unificada de Datos (Ya viene enriquecida con la IA de Prolog de data_manager)
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
    # NOTA: Cambiamos dinámicamente a minúsculas en el mapeo para acoplar la data del OCR
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

    # 5. Panel de Control de Indicadores (KPIs Dinámicos con Nuevas Funciones)
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("📦 Total Líneas Auditadas", f"{len(datos_filtrados):,}")
    
    # KPIs alimentados directamente por el Paso 3 de Prolog:
    urgentes = len(datos_filtrados[datos_filtrados['prioridad_alta'] == True]) if 'prioridad_alta' in datos_filtrados.columns else 0
    kpi2.metric("⚡ SLA Crítico (Urgentes)", urgentes)
    
    sobrecostos = len(datos_filtrados[datos_filtrados['alerta_costo'] == True]) if 'alerta_costo' in datos_filtrados.columns else 0
    kpi3.metric("💰 Fletes con Sobreprecio", sobrecostos)

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
            
            if coordenadas_carretera and len(coordenadas_carretera) > 0:
                color_linea = [88, 166, 255, 255]
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
                st.error("⚠️ No se pudo trazar la ruta terrestre. Verifique las coordenadas de los nodos.")
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
    
    # 🛡️ Blindaje de Columnas: Filtramos solo las que existen para evitar KeyError
    columnas_validas = [col for col in columnas_mostrar if col in datos_filtrados.columns]
    
    f2_A, f2_B = st.columns(2)
    with f2_A:
        st.markdown("<h3 style='font-size:1.1rem; color:#ef4444;'>🚨 Auditoría de Riesgos y Alertas Críticas</h3>", unsafe_allow_html=True)
        df_alertas = datos_filtrados[datos_filtrados['diagnostico_ia'] == 'critico_financiero']
        if not df_alertas.empty:
            st.dataframe(df_alertas[columnas_validas], use_container_width=True)
        else:
            st.info("No se detectaron alertas críticas con los filtros actuales.")
        
    with f2_B:
        st.markdown("<h3 style='font-size:1.1rem; color:#f28c0f;'>💰 Tarifas Fuera de Estándar (Prolog)</h3>", unsafe_allow_html=True)
        if 'alerta_costo' in datos_filtrados.columns:
            df_caros = datos_filtrados[datos_filtrados['alerta_costo'] == True]
            if not df_caros.empty:
                st.dataframe(df_caros[columnas_validas], use_container_width=True)
            else:
                st.info("No hay fletes con sobreprecio detectados.")
        else:
            st.caption("Esperando inicialización de métricas de costo.")

    # 8. Repositorio de Trazabilidad Total Completo
    st.markdown("---")
    st.markdown("<h2 style='font-size:1.4rem;'>📋 Repositorio Central de Trazabilidad Logística</h2>", unsafe_allow_html=True)
    st.dataframe(datos_filtrados[columnas_validas], use_container_width=True)

except Exception as e:
    st.error(f"Error general en la orquestación modular: {e}")