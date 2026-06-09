# dashboard/metrics_ui.py - Componentes visuales de estadísticas y KPIs
import streamlit as st
import pandas as pd

def renderizar_metricas(df_filtrado_raw):
    """
    Renderiza los filtros horizontales, KPIs dinámicos y los gráficos de la operación en el Dashboard.
    """
    if df_filtrado_raw is None or df_filtrado_raw.empty:
        st.warning("⚠️ No hay datos para mostrar métricas.")
        return

    # Inyectar la barra de filtros horizontal
    from ui.filters import renderizar_barra_filtros
    df_filtrado = renderizar_barra_filtros(df_filtrado_raw, key_prefix="exec_metrics", mostrar_flete=True)

    if df_filtrado is None or df_filtrado.empty:
        st.warning("⚠️ No hay registros de envíos que coincidan con los filtros aplicados.")
        return

    # Renderizar el tablero analítico unificado (KPIs a la izquierda, gráficos a la derecha)
    from ui.charts import renderizar_tablero_analitico
    renderizar_tablero_analitico(df_filtrado, 'admin')
