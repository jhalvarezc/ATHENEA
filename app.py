# app.py - Dashboard ATHENEA Enterprise (Rutas Reales por Carretera)
import streamlit as st
import pandas as pd
import pydeck as pdk
import requests
from pyswip import Prolog

# 1. Configuración de la Ventana y Layout
st.set_page_config(page_title="ATHENEA Dashboard", page_icon="🧠", layout="wide")

# ==========================================================
# 🎨 INYECCIÓN DE CSS: ESTILO DARK ENTERPRISE
# ==========================================================
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; }
    [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #1f2937; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 18px; }
    h1, h2, h3, p, label { color: #e6edf3 !important; font-family: 'Inter', sans-serif; }
    .titulo-athenea { color: #e6edf3; font-weight: 800; margin-bottom: 5px; }
    .stDataFrame { background-color: #161b22; border-radius: 10px; padding: 5px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='titulo-athenea'>🧠 ATHENEA - Centro de Inteligencia Logística</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #8b949e; margin-top:-10px;'>Auditoría de despachos y tránsito con geolocalización de rutas reales.</p>", unsafe_allow_html=True)
st.markdown("---")

# ==========================================================
# 🛣️ MOTOR DE RUTAS POR CARRETERA (OSRM API)
# ==========================================================
@st.cache_data(show_spinner=False)
def obtener_ruta_calle(lon_origen, lat_origen, lon_destino, lat_destino):
    """Obtiene la ruta trazada por carreteras usando la API pública de OSRM."""
    url = f"http://router.project-osrm.org/route/v1/driving/{lon_origen},{lat_origen};{lon_destino},{lat_destino}?overview=full&geometries=geojson"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get('code') == 'Ok':
            # Retorna la lista de coordenadas que forman el trazado de la carretera
            return data['routes'][0]['geometry']['coordinates']
    except Exception as e:
        pass
    # Si falla la conexión, retorna una línea recta como respaldo
    return [[lon_origen, lat_origen], [lon_destino, lat_destino]]

# 2. Motor de Inferencia Lógica (Prolog)
@st.cache_resource
def inicializar_base_conocimiento():
    prolog = Prolog()
    try:
        prolog.consult("logic.pl")
    except Exception as e:
        pass
    return prolog

prolog = inicializar_base_conocimiento()

def consultar_regla(cadena_prolog):
    try: 
        return list(prolog.query(cadena_prolog))
    except Exception: 
        return []

# 3. Sincronización Automática de Base de Datos
def sincronizar_datos():
    consultar_regla("retractall(estado_envio(_,_))")
    consultar_regla("retractall(limite_entrega(_,_))")
    consultar_regla("retractall(costo_flete(_,_))")
    consultar_regla("retractall(destino_envio(_,_))")
    consultar_regla("retractall(origen_envio(_,_))")
    consultar_regla("retractall(fecha_despacho(_,_))")
    
    try:
        df = pd.read_csv("envios.csv")
    except:
        return pd.DataFrame()

    for _, row in df.iterrows():
        g = str(row['guia']).strip()
        e = str(row['estado']).strip()
        c = int(row['costo_flete'])
        o = str(row['origen']).strip()
        d = str(row['destino']).strip()
        
        d_dia, d_mes, d_ano = int(row['despacho_dia']), int(row['despacho_mes']), int(row['despacho_ano'])
        l_dia, l_mes, l_ano = int(row['limite_dia']), int(row['limite_mes']), int(row['limite_ano'])
        
        prolog.assertz(f"estado_envio('{g}', {e})")
        prolog.assertz(f"costo_flete('{g}', {c})")
        prolog.assertz(f"origen_envio('{g}', '{o}')")
        prolog.assertz(f"destino_envio('{g}', '{d}')")
        prolog.assertz(f"fecha_despacho('{g}', fecha({d_dia}, {d_mes}, {d_ano}))")
        prolog.assertz(f"limite_entrega('{g}', fecha({l_dia}, {l_mes}, {l_ano}))")
        
    return df

try:
    datos_crudos = sincronizar_datos()

    if datos_crudos.empty:
        st.warning("No hay datos. Asegúrate de ejecutar generar_datos.py.")
        st.stop()

    # --- CONSULTA MAESTRA AL MOTOR PROLOG ---
    resultados_prolog = consultar_regla("analisis_ruta_completa(Guia, Origen, Destino, Diagnostico, fecha(7, 6, 2026))")
    
    dict_diagnosticos = {}
    for r in resultados_prolog:
        guia_val = r['Guia'].decode('utf-8') if isinstance(r['Guia'], bytes) else str(r['Guia'])
        diag_val = r['Diagnostico'].decode('utf-8') if isinstance(r['Diagnostico'], bytes) else str(r['Diagnostico'])
        dict_diagnosticos[guia_val] = diag_val
        
    datos_crudos['diagnostico_ia'] = datos_crudos['guia'].map(dict_diagnosticos)

    # 4. Panel Lateral (Controles de Operación)
    st.sidebar.markdown("<h2 style='font-size:1.2rem; color:#58a6ff;'>🔍 Controles de Operación</h2>", unsafe_allow_html=True)
    busqueda_guia = st.sidebar.text_input("Buscar código de guía:", "").strip()
    
    estados_seleccionados = st.sidebar.multiselect("Filtrar por Estado:", datos_crudos['estado'].unique().tolist(), default=datos_crudos['estado'].unique().tolist())
    ciudades_seleccionadas = st.sidebar.multiselect("Filtrar por Destino:", datos_crudos['destino'].unique().tolist(), default=datos_crudos['destino'].unique().tolist())
    
    max_flete = int(datos_crudos['costo_flete'].max()) if not datos_crudos.empty else 10000
    flete_minimo_filtro = st.sidebar.slider("Filtrar fletes mayores a ($):", 0, max_flete, 0)
    
    filtro_diagnostico = st.sidebar.multiselect(
        "Filtrar por Diagnóstico IA:", 
        datos_crudos['diagnostico_ia'].unique().tolist(), 
        default=datos_crudos['diagnostico_ia'].unique().tolist()
    )

    # Aplicar filtros
    datos_filtrados = datos_crudos[
        (datos_crudos['estado'].isin(estados_seleccionados)) &
        (datos_crudos['destino'].isin(ciudades_seleccionadas)) &
        (datos_crudos['costo_flete'] >= flete_minimo_filtro) &
        (datos_crudos['diagnostico_ia'].isin(filtro_diagnostico))
    ]
    
    if busqueda_guia:
        datos_filtrados = datos_filtrados[datos_filtrados['guia'].str.contains(busqueda_guia, case=False)]

    # 5. KPIs Dinámicos Superiores
    conteo_despacho = len(datos_filtrados[datos_filtrados['diagnostico_ia'] == 'retraso_despacho'])
    conteo_transporte = len(datos_filtrados[datos_filtrados['diagnostico_ia'] == 'retraso_transporte'])
    conteo_critico = len(datos_filtrados[datos_filtrados['diagnostico_ia'] == 'critico_financiero'])
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("📦 Guías Auditadas", f"{len(datos_filtrados):,}")
    kpi2.metric("🏢 Retrasos en Bodega", conteo_despacho)
    kpi3.metric("🚚 Retrasos en Carretera", conteo_transporte)
    kpi4.metric("🚨 Alertas Críticas", conteo_critico)

    st.markdown("---")

    # ==========================================================
    # 🌍 SECCIÓN CENTRAL: MONITOREO DE RED GEOGRÁFICA (INDIVIDUAL)
    # ==========================================================
    st.markdown("<h2 style='font-size:1.5rem;'>🗺️ Monitoreo de Red Geográfica</h2>", unsafe_allow_html=True)
    
    mapa_col, graf_col = st.columns([5, 3])

    with mapa_col:
        st.markdown("<p style='color: #8b949e; font-weight:bold;'>Ubicación Física Automatizada y Rutas de Transporte</p>", unsafe_allow_html=True)
        
        lista_guias = sorted(datos_filtrados['guia'].unique().tolist())
        
        if lista_guias:
            guia_seleccionada = st.selectbox("🔍 Selecciona una guía para trazar ruta detallada:", lista_guias)
            
            fila_guia = datos_filtrados[datos_filtrados['guia'] == guia_seleccionada].iloc[0]
            
            st.info(f"📍 **Detalle de Guía:** {fila_guia['guia']} | **Estado:** {str(fila_guia['estado']).upper()} | **Origen:** {str(fila_guia['origen']).capitalize()} | **Destino:** {str(fila_guia['destino']).capitalize()} | **Flete:** ${fila_guia['costo_flete']} USD")
            
            def color_por_diagnostico(diag):
                if diag == 'critico_financiero': return [239, 68, 68, 255]    # Rojo
                elif diag == 'retraso_despacho': return [234, 179, 8, 255]    # Amarillo
                elif diag == 'retraso_transporte': return [249, 115, 22, 255] # Naranja
                elif diag == 'en_transito_optimo': return [16, 185, 129, 255] # Verde
                elif diag == 'entregado_ok': return [59, 130, 246, 255]       # Azul
                else: return [156, 163, 175, 200]

            # 🛣️ Extraer trazado real por calles desde la API
            coordenadas_carretera = obtener_ruta_calle(
                float(fila_guia['origen_longitude']), float(fila_guia['origen_latitude']),
                float(fila_guia['destino_longitude']), float(fila_guia['destino_latitude'])
            )

            df_ruta_unica = pd.DataFrame([{
                'path': coordenadas_carretera,
                'color_rgba': color_por_diagnostico(fila_guia['diagnostico_ia'])
            }])

            # Usar PathLayer en lugar de ArcLayer para dibujar la carretera
            capa_calles = pdk.Layer(
                "PathLayer",
                data=df_ruta_unica,
                get_path="path",
                get_color="color_rgba",
                width_scale=20,
                width_min_pixels=4, # Grosor mínimo para que siempre sea visible
                pickable=True
            )

            # Capas de puntos para marcar el Origen y Destino
            df_puntos = pd.DataFrame([
                {'coordenadas': [float(fila_guia['origen_longitude']), float(fila_guia['origen_latitude'])], 'color': [255, 255, 255]},
                {'coordenadas': [float(fila_guia['destino_longitude']), float(fila_guia['destino_latitude'])], 'color': color_por_diagnostico(fila_guia['diagnostico_ia'])}
            ])

            capa_nodos = pdk.Layer(
                "ScatterplotLayer",
                data=df_puntos,
                get_position="coordenadas",
                get_fill_color="color",
                get_radius=5000,
                radius_min_pixels=6
            )

            # Ajustamos el pitch (inclinación) para ver mejor las carreteras
            view_state = pdk.ViewState(
                latitude=(float(fila_guia['origen_latitude']) + float(fila_guia['destino_latitude'])) / 2, 
                longitude=(float(fila_guia['origen_longitude']) + float(fila_guia['destino_longitude'])) / 2, 
                zoom=5.5, 
                pitch=30 
            )

            st.pydeck_chart(pdk.Deck(
                map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
                initial_view_state=view_state,
                layers=[capa_calles, capa_nodos],
                tooltip={"text": "Ruta por carretera detectada"}
            ))
        else:
            st.warning("No hay guías que coincidan con los filtros actuales.")

    with graf_col:
        st.markdown("<p style='color: #8b949e; font-weight:bold;'>Volúmenes de Carga por Nodo Destino</p>", unsafe_allow_html=True)
        conteo_destinos = datos_filtrados['destino'].value_counts()
        if not conteo_destinos.empty:
            st.bar_chart(conteo_destinos, color="#58a6ff")

    st.markdown("---")

    # ==========================================================
    # 📋 CUADRANTE 2x2 DE AUDITORÍA LOGÍSTICA
    # ==========================================================
    columnas_ocultas = ['origen_latitude', 'origen_longitude', 'destino_latitude', 'destino_longitude']
    columnas_visibles = [col for col in datos_filtrados.columns if col not in columnas_ocultas]
    columnas_ordenadas = ['guia', 'origen', 'destino', 'diagnostico_ia', 'estado', 'costo_flete'] + [col for col in columnas_visibles if col not in ['guia', 'origen', 'destino', 'diagnostico_ia', 'estado', 'costo_flete']]

    f1_A, f1_B = st.columns(2)
    with f1_A:
        st.markdown("<h3 style='font-size:1.1rem; color:#eab308;'>🏢 Auditoría de Latencia (Retrasos en Bodega)</h3>", unsafe_allow_html=True)
        df_bodega = datos_filtrados[datos_filtrados['diagnostico_ia'] == 'retraso_despacho'][columnas_ordenadas]
        st.dataframe(df_bodega, use_container_width=True)
        
    with f1_B:
        st.markdown("<h3 style='font-size:1.1rem; color:#f97316;'>🚚 Riesgos de Flete Crítico (Retrasos en Carretera)</h3>", unsafe_allow_html=True)
        df_transporte = datos_filtrados[datos_filtrados['diagnostico_ia'] == 'retraso_transporte'][columnas_ordenadas]
        st.dataframe(df_transporte, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    f2_A, f2_B = st.columns(2)
    with f2_A:
        st.markdown("<h3 style='font-size:1.1rem; color:#ef4444;'>🚨 Auditoría de Rutas Críticas de Entrega (Regla C)</h3>", unsafe_allow_html=True)
        df_criticos = datos_filtrados[datos_filtrados['diagnostico_ia'] == 'critico_financiero'][columnas_ordenadas]
        st.dataframe(df_criticos, use_container_width=True)
        
    with f2_B:
        st.markdown("<h3 style='font-size:1.1rem; color:#3b82f6;'>✅ Sobrecostos por Tarifas Excesivas (Regla D)</h3>", unsafe_allow_html=True)
        df_ok = datos_filtrados[datos_filtrados['diagnostico_ia'] == 'entregado_ok'][columnas_ordenadas]
        st.dataframe(df_ok, use_container_width=True)

    st.markdown("---")
    
    st.markdown("<h2 style='font-size:1.4rem;'>📋 Registro Completo de Trazabilidad Logística</h2>", unsafe_allow_html=True)
    st.dataframe(datos_filtrados[columnas_ordenadas], use_container_width=True)

except Exception as e:
    st.error(f"Error crítico en la aplicación: {e}")