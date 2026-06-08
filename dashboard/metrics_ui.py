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
    
    # 2. Gráficos
    st.markdown("<p style='color: #8b949e; font-weight:bold; font-size:1.1rem;'>Volumen de Carga por Origen de Datos</p>", unsafe_allow_html=True)
    fuente_col = 'fuente' if 'fuente' in df_filtrado.columns else ('fuente_datos' if 'fuente_datos' in df_filtrado.columns else None)
    if fuente_col:
        st.bar_chart(df_filtrado[fuente_col].value_counts(), color="#f28c0f")
    else:
        st.caption("No hay datos de procedencia para graficar.")
