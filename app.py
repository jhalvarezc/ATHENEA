# app.py - Dashboard Modularizado ATHENEA
import streamlit as st
import pandas as pd
import pydeck as pdk

# Importación de los componentes modulares creados
from modules.ui_styles import aplicar_estilos_dark, renderizar_encabezado
from modules.osrm_engine import obtener_ruta_calle
from modules.prolog_engine import consultar_regla
from modules.data_manager import sincronizar_datos

# 1. Setup e Inyección Visual
st.set_page_config(page_title="ATHENEA Dashboard", page_icon="🧠", layout="wide")
aplicar_estilos_dark()
renderizar_encabezado()

try:
    # 2. Sincronización e Inferencia del Cerebro Lógico
    datos_crudos = sincronizar_datos()
    if datos_crudos.empty:
        st.warning("⚠️ No se detectaron registros en envios.csv.")
        st.stop()

    # Procesar diagnósticos lógicos de Prolog
    resultados_prolog = consultar_regla("analisis_ruta_completa(Guia, Origen, Destino, Diagnostico, fecha(7, 6, 2026))")
    dict_diagnosticos = {}
    for r in resultados_prolog:
        guia_val = r['Guia'].decode('utf-8') if isinstance(r['Guia'], bytes) else str(r['Guia'])
        diag_val = r['Diagnostico'].decode('utf-8') if isinstance(r['Diagnostico'], bytes) else str(r['Diagnostico'])
        dict_diagnosticos[guia_val] = diag_val
        
    datos_crudos['diagnostico_ia'] = datos_crudos['guia'].map(dict_diagnosticos).fillna('sin_diagnostico')

    # 3. Sidebar (Controles de Operación)
    st.sidebar.markdown("<h2 style='font-size:1.2rem; color:#58a6ff;'>🔍 Controles de Operación</h2>", unsafe_allow_html=True)
    busqueda_guia = st.sidebar.text_input("Buscar código de guía:", "").strip()
    
    estados_sel = st.sidebar.multiselect("Filtrar por Estado:", datos_crudos['estado'].unique().tolist(), default=datos_crudos['estado'].unique().tolist())
    ciudades_sel = st.sidebar.multiselect("Filtrar por Destino:", datos_crudos['destino'].unique().tolist(), default=datos_crudos['destino'].unique().tolist())
    
    max_flete = int(datos_crudos['costo_flete'].max())
    flete_minimo = st.sidebar.slider("Filtrar fletes mayores a ($):", 0, max_flete, 0)

    # Aplicación de Filtros al Dataset
    datos_filtrados = datos_crudos[
        (datos_crudos['estado'].isin(estados_sel)) &
        (datos_crudos['destino'].isin(ciudades_sel)) &
        (datos_crudos['costo_flete'] >= flete_minimo)
    ]
    if busqueda_guia:
        datos_filtrados = datos_filtrados[datos_filtrados['guia'].astype(str).str.contains(busqueda_guia, case=False)]

    # Mensaje de éxito del Motor de Inferencia en Sidebar
    st.sidebar.markdown("---")
    st.sidebar.success("🟢 ATHENEA Inference Engine: Activo")

    # 4. KPIs Principales superiores
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("📦 Guías Auditadas", f"{len(datos_filtrados):,}")
    kpi2.metric("🏢 Retrasos en Bodega", len(datos_filtrados[datos_filtrados['diagnostico_ia'] == 'retraso_despacho']))
    kpi3.metric("🚚 Retrasos en Carretera", len(datos_filtrados[datos_filtrados['diagnostico_ia'] == 'retraso_transporte']))
    kpi4.metric("🚨 Alertas Críticas", len(datos_filtrados[datos_filtrados['diagnostico_ia'] == 'critico_financiero']))

    st.markdown("---")

    # 5. Sección de Visualización Geográfica (Mapas y Gráficos)
    st.markdown("<h2 style='font-size:1.5rem;'>🗺️ Monitoreo de Red Geográfica</h2>", unsafe_allow_html=True)
    mapa_col, graf_col = st.columns([5, 3])

    # Generamos la lista de guías seguras basadas en el filtro actual
    list_guias = sorted(datos_filtrados['guia'].unique().tolist())

    with mapa_col:
        if list_guias:
            guia_seleccionada = st.selectbox("🎯 Selecciona una guía para trazar ruta en carretera:", list_guias)
            fila_guia = datos_filtrados[datos_filtrados['guia'] == guia_seleccionada].iloc[0]
            
            # Trazado OSRM Modularizado por carreteras reales
            coordenadas_carretera = obtener_ruta_calle(
                float(fila_guia['origen_longitude']), float(fila_guia['origen_latitude']),
                float(fila_guia['destino_longitude']), float(fila_guia['destino_latitude'])
            )

            df_ruta = pd.DataFrame([{'path': coordenadas_carretera, 'color': [88, 166, 255, 255]}])
            capa_calles = pdk.Layer("PathLayer", data=df_ruta, get_path="path", get_color="color", width_scale=20, width_min_pixels=4)
            
            view_state = pdk.ViewState(
                latitude=(float(fila_guia['origen_latitude']) + float(fila_guia['destino_latitude'])) / 2,
                longitude=(float(fila_guia['origen_longitude']) + float(fila_guia['destino_longitude'])) / 2,
                zoom=5.5
            )
            st.pydeck_chart(pdk.Deck(map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json", initial_view_state=view_state, layers=[capa_calles]))
        else:
            st.warning("No hay guías disponibles para los filtros seleccionados.")

    with graf_col:
        st.markdown("<p style='color: #8b949e; font-weight:bold;'>Volumen por Ciudad Destino</p>", unsafe_allow_html=True)
        if not datos_filtrados.empty:
            st.bar_chart(datos_filtrados['destino'].value_counts(), color="#58a6ff")

    # 6. Cuadrante de Tablas de Auditoría
    st.markdown("---")
    columnas_ordenadas = ['guia', 'origen', 'destino', 'diagnostico_ia', 'estado', 'costo_flete']
    
    f2_A, f2_B = st.columns(2)
    with f2_A:
        st.markdown("<h3 style='font-size:1.1rem; color:#ef4444;'>🚨 Auditoría de Riesgos Críticos</h3>", unsafe_allow_html=True)
        st.dataframe(datos_filtrados[datos_filtrados['diagnostico_ia'] == 'critico_financiero'][columnas_ordenadas], use_container_width=True)
    with f2_B:
        st.markdown("<h3 style='font-size:1.1rem; color:#3b82f6;'>✅ Entregas en Destino</h3>", unsafe_allow_html=True)
        st.dataframe(datos_filtrados[datos_filtrados['diagnostico_ia'] == 'entregado_ok'][columnas_ordenadas], use_container_width=True)

    st.markdown("---")
    st.markdown("<h2 style='font-size:1.4rem;'>📋 Registro Completo de Trazabilidad Logística</h2>", unsafe_allow_html=True)
    st.dataframe(datos_filtrados[columnas_ordenadas], use_container_width=True)

except Exception as e:
    st.error(f"Error crítico en la aplicación: {e}")