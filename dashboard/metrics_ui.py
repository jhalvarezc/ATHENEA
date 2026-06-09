# dashboard/metrics_ui.py - Componentes visuales de estadísticas y KPIs
import streamlit as st
import pandas as pd

def renderizar_metricas(df_filtrado):
    """
    Renderiza los KPIs dinámicos y los gráficos de la operación en el Dashboard.
    """
    if df_filtrado is None or df_filtrado.empty:
        st.warning("⚠️ No hay datos para mostrar métricas.")
        return

    # 1. Indicadores principales (KPIs)
    kpi1, kpi2, kpi3 = st.columns(3)
    
    total_audits = len(df_filtrado)
    kpi1.metric("📦 Total Líneas Auditadas", f"{total_audits:,}")
    
    # Alertas basadas en auditoría
    if 'alertas_detalladas' in df_filtrado.columns:
        urgentes = len(df_filtrado[df_filtrado['alertas_detalladas'].astype(str).str.contains('Retraso|Vehículo', case=False, na=False)])
        sobrecostos = len(df_filtrado[df_filtrado['alertas_detalladas'].astype(str).str.contains('Riesgo|Tarifa|Fraude', case=False, na=False)])
    else:
        # Fallback si no está la columna usando los niveles de riesgo
        urgentes = len(df_filtrado[df_filtrado['estado_auditoria'] == 'riesgo_medio'])
        sobrecostos = len(df_filtrado[df_filtrado['estado_auditoria'] == 'riesgo_alto'])
        
    kpi2.metric("⚡ SLA Crítico (Retrasos)", urgentes)
    kpi3.metric("💰 Fletes con Sobreprecio", sobrecostos)

    st.markdown("---")
    
    # 2. Gráficos (Cuadrícula Premium 2x2)
    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        with st.container(border=True):
            try:
                from ui.charts import renderizar_grafico_canal
                renderizar_grafico_canal(df_filtrado)
            except Exception as e:
                st.error(f"Error cargando gráfica de procedencia: {e}")
        
        with st.container(border=True):
            try:
                from ui.charts import renderizar_grafico_costos
                renderizar_grafico_costos(df_filtrado)
            except Exception as e:
                st.error(f"Error cargando gráfica de costos: {e}")

    with col_graf2:
        with st.container(border=True):
            try:
                from ui.charts import renderizar_grafico_estados
                renderizar_grafico_estados(df_filtrado)
            except Exception as e:
                st.error(f"Error cargando gráfica de estados: {e}")
        
        with st.container(border=True):
            try:
                from ui.charts import renderizar_grafico_ia
                renderizar_grafico_ia(df_filtrado)
            except Exception as e:
                st.error(f"Error cargando gráfica de auditoría IA: {e}")
