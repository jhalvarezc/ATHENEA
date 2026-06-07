# app.py - Dashboard ATHENEA Enterprise (Dark Theme & CSS Profesional)
import streamlit as st
import pandas as pd
import pydeck as pdk
from pyswip import Prolog

# 1. Configuración de la Ventana y Layout Ejecutivo
st.set_page_config(page_title="ATHENEA Dashboard", page_icon="🧠", layout="wide")

# ==========================================================
# 🎨 INYECCIÓN DE CSS: ESTILO MAPCN (DARK ENTERPRISE)
# ==========================================================
st.markdown("""
<style>
    /* Fondo principal de la aplicación */
    .stApp {
        background-color: #0b0f19; 
    }
    
    /* Fondo de la barra lateral (Sidebar) */
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }

    /* Diseño Avanzado de Tarjetas para KPIs (Métricas) */
    [data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
        transition: transform 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: #58a6ff;
    }

    /* Personalización de Títulos y Tipografías */
    h1, h2, h3, p, label {
        color: #e6edf3 !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Estilo Neón para Título Principal */
    .titulo-athenea {
        color: #e6edf3;
        font-weight: 800;
        margin-bottom: 5px;
    }

    /* Ocultar elementos predeterminados de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Contenedores de Tablas de Datos (DataFrames) */
    .stDataFrame {
        background-color: #161b22;
        border-radius: 10px;
        padding: 5px;
    }
</style>
""", unsafe_allow_html=True)

# 2. Encabezado de la Plataforma
st.markdown("<h1 class='titulo-athenea'>🧠 ATHENEA - Centro de Inteligencia Logística</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #8b949e; margin-top:-10px;'>Plataforma analítica con geolocalización en tiempo real y auditoría lógica de envíos.</p>", unsafe_allow_html=True)
st.markdown("---")

# 3. Motor de Inferencia Lógica (Prolog)
@st.cache_resource
def inicializar_base_conocimiento():
    prolog = Prolog()
    prolog.consult("logic.pl")
    return prolog

prolog = inicializar_base_conocimiento()

def consultar_regla(cadena_prolog):
    try: 
        return list(prolog.query(cadena_prolog))
    except Exception: 
        return []

# 4. Sincronización Automática de Base de Datos Dinámica
def sincronizar_datos():
    # Limpieza de aserciones previas en la sesión
    consultar_regla("retractall(estado_envio(_,_))")
    consultar_regla("retractall(limite_entrega(_,_))")
    consultar_regla("retractall(costo_flete(_,_))")
    consultar_regla("retractall(destino_envio(_,_))")
    
    df = pd.read_csv("envios.csv")
    for _, row in df.iterrows():
        g = str(row['guia']).strip()
        e = str(row['estado']).strip()
        l = int(row['limite_entrega'])
        c = int(row['costo_flete'])
        d = str(row['destino']).strip()
        
        prolog.assertz(f"estado_envio({g}, {e})")
        prolog.assertz(f"limite_entrega({g}, {l})")
        prolog.assertz(f"costo_flete({g}, {c})")
        prolog.assertz(f"destino_envio({g}, {d})")
    return df

try:
    datos_crudos = sincronizar_datos()
    fecha_hoy = 20260607  # Sincronizado al entorno temporal simulado
    
    # --- Deducciones del Motor Prolog ---
    retrasos = [r['Guia'].decode('utf-8') if isinstance(r['Guia'], bytes) else r['Guia'] for r in consultar_regla(f"alerta_retraso(Guia, {fecha_hoy})")]
    criticos = [r['Guia'].decode('utf-8') if isinstance(r['Guia'], bytes) else r['Guia'] for r in consultar_regla("alerta_critica(Guia)")]
    rutas_criticas = [r['Guia'].decode('utf-8') if isinstance(r['Guia'], bytes) else r['Guia'] for r in consultar_regla("alerta_ruta_critica(Guia)")]
    tarifas_excesivas = [r['Guia'].decode('utf-8') if isinstance(r['Guia'], bytes) else r['Guia'] for r in consultar_regla("alerta_tarifa_excesiva(Guia)")]

    # 5. Panel Lateral de Control y Filtros Coherentes
    st.sidebar.markdown("<h2 style='font-size:1.2rem; color:#58a6ff;'>🔍 Controles de Operación</h2>", unsafe_allow_html=True)
    busqueda_guia = st.sidebar.text_input("Buscar código de guía:", "").strip()
    
    estados_seleccionados = st.sidebar.multiselect("Filtrar por Estado:", datos_crudos['estado'].unique().tolist(), default=datos_crudos['estado'].unique().tolist())
    ciudades_seleccionadas = st.sidebar.multiselect("Filtrar por Destino:", datos_crudos['destino'].unique().tolist(), default=datos_crudos['destino'].unique().tolist())
    flete_minimo_filtro = st.sidebar.slider("Filtrar fletes mayores a ($):", 0, int(datos_crudos['costo_flete'].max()), 0)

    # Filtrado dinámico del DataFrame
    datos_filtrados = datos_crudos[
        (datos_crudos['estado'].isin(estados_seleccionados)) &
        (datos_crudos['destino'].isin(ciudades_seleccionadas)) &
        (datos_crudos['costo_flete'] >= flete_minimo_filtro)
    ]
    if busqueda_guia:
        datos_filtrados = datos_filtrados[datos_filtrados['guia'].str.contains(busqueda_guia, case=False)]

    # 6. Indicadores Clave de Rendimiento (KPIs Globales)
    total_fuga = datos_filtrados[datos_filtrados['guia'].isin(criticos)]['costo_flete'].sum() + datos_filtrados[datos_filtrados['guia'].isin(tarifas_excesivas)]['costo_flete'].sum()
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("📦 Total Auditado", f"{len(datos_filtrados):,}")
    kpi2.metric("⏱️ Alertas de Retraso", len(datos_filtrados[datos_filtrados['guia'].isin(retrasos)]))
    kpi3.metric("🎯 Rutas Críticas Activas", len(datos_filtrados[datos_filtrados['guia'].isin(rutas_criticas)]))
    kpi4.metric("💰 Capital en Riesgo Crítico", f"${total_fuga:,} USD")

    st.markdown("---")

    # ==========================================================
    # 🌍 CAPA GEOGRÁFICA INTERACTIVA Y VOLÚMENES URBANOS
    # ==========================================================
    st.markdown("<h2 style='font-size:1.5rem;'>🗺️ Monitoreo de Red Geográfica (Estilo Corporativo)</h2>", unsafe_allow_html=True)
    mapa_col, graf_col = st.columns([5, 3])

    with mapa_col:
        st.markdown("<p style='color: #8b949e;'>Ubicación Física Automatizada y Alertas de Flujo (Verde: OK | Naranja: Sobreprecio | Rojo: Crítico)</p>", unsafe_allow_html=True)
        if not datos_filtrados.empty and 'latitude' in datos_filtrados.columns and 'longitude' in datos_filtrados.columns:
            
            df_mapa = datos_filtrados.copy()
            
            def asignar_color_alerta(row):
                g = row['guia']
                if g in retrasos or g in criticos:
                    return [239, 68, 68, 210]      # Rojo Brillante para Alertas Críticas
                elif g in tarifas_excesivas:
                    return [245, 158, 11, 210]    # Naranja Mandarina para Tarifas Excesivas
                else:
                    return [16, 185, 129, 180]    # Verde Esmeralda para Estados Normales
            
            df_mapa['color'] = df_mapa.apply(asignar_color_alerta, axis=1)
            
            # CONFIGURACIÓN CORRECTA DE PYDECK CON CARTO-DARKMATTER
            st.pydeck_chart(pdk.Deck(
                map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json", # ✅ URL directa infalible
                initial_view_state=pdk.ViewState(
                    latitude=4.5709,   # Centrado geográfico óptimo de Colombia
                    longitude=-74.2973,
                    zoom=5.0,
                    pitch=35,
                ),
                layers=[
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=df_mapa,
                        get_position="[longitude, latitude]",
                        get_color="color",
                        get_radius=22000,
                        pickable=True
                    )
                ],
                tooltip={"text": "Guía: {guia}\nDestino: {destino}\nCosto Flete: ${costo_flete} USD\nEstado: {estado}"}
            ))
        else:
            st.info("No hay datos geográficos para renderizar. Revisa los filtros o ejecuta generar_datos.py.")

    with graf_col:
        st.markdown("<p style='color: #8b949e; font-weight:bold;'>Volúmenes de Carga por Nodo Destino</p>", unsafe_allow_html=True)
        conteo_destinos = datos_filtrados['destino'].value_counts()
        if not conteo_destinos.empty:
            st.bar_chart(conteo_destinos, color="#58a6ff")

    st.markdown("---")

    # 7. Matrices de Análisis de Riesgos Estructuradas en Paneles 2x2
    f1_A, f1_B = st.columns(2)
    with f1_A:
        st.markdown("<h3 style='font-size:1.2rem; color:#ff7b72;'>⏱️ Análisis de Latencia (Retrasos Inminentes)</h3>", unsafe_allow_html=True)
        st.dataframe(datos_filtrados[datos_filtrados['guia'].isin(retrasos)], use_container_width=True)
    with f1_B:
        st.markdown("<h3 style='font-size:1.2rem; color:#ff7b72;'>🚨 Riesgos de Flete Crítico (Regla B)</h3>", unsafe_allow_html=True)
        st.dataframe(datos_filtrados[datos_filtrados['guia'].isin(criticos)], use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    f2_A, f2_B = st.columns(2)
    with f2_A:
        st.markdown("<h3 style='font-size:1.2rem; color:#ffb454;'>🎯 Auditoría de Rutas Críticas de Entrega (Regla C)</h3>", unsafe_allow_html=True)
        st.dataframe(datos_filtrados[datos_filtrados['guia'].isin(rutas_criticas)], use_container_width=True)
    with f2_B:
        st.markdown("<h3 style='font-size:1.2rem; color:#ffb454;'>📈 Sobrecostos por Tarifas Excesivas (Regla D)</h3>", unsafe_allow_html=True)
        st.dataframe(datos_filtrados[datos_filtrados['guia'].isin(tarifas_excesivas)], use_container_width=True)

    # 8. Visor Total del Data Lake
    st.markdown("---")
    st.markdown("<h2 style='font-size:1.4rem;'>📋 Registro Completo de Trazabilidad Logística</h2>", unsafe_allow_html=True)
    st.dataframe(datos_filtrados, use_container_width=True)

except Exception as e:
    st.error(f"Error crítico en la sincronización del Dashboard: {e}")

# Footer de la barra lateral indicando salud del motor lógico
st.sidebar.markdown("---")
st.sidebar.markdown("<div style='color:#10b981; font-weight:bold; font-size:0.9rem;'>✅ ATHENEA Inference Engine: Activo</div>", unsafe_allow_html=True)