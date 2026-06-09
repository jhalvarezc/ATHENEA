# ui/charts.py - Generador de Gráficos Analíticos Premium para ATHENEA
import streamlit as st
import pandas as pd

# Diccionarios globales de traducción amigable para visualizaciones
DICCIONARIO_FUENTES = {
    'Data_Lake_CSV': '📁 Histórico (CSV)',
    'Cargue_Operador_Excel': '📥 Ingesta (Excel)',
    'Excel_Importado': '📥 Ingesta (Excel)'
}

DICCIONARIO_ESTADOS = {
    'en_bodega': '📦 En Bodega',
    'en_transito': '🚛 En Tránsito',
    'en_novedad': '⚠️ En Novedad',
    'entregado': '✅ Entregado',
    'preparacion': '📝 En Preparación',
    'en_revision_doc': '🔍 En Revisión Doc'
}

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_DISPONIBLE = True
except ImportError:
    PLOTLY_DISPONIBLE = False

def aplicar_estilos_plotly(fig):
    """Aplica la plantilla corporativa ATHENEA Dark a cualquier figura de Plotly."""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(
            family="'Plus Jakarta Sans', 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif",
            size=11,
            color='#cbd5e1'
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
            font=dict(size=10, color='#94a3b8')
        ),
        hoverlabel=dict(
            bgcolor="#0f172a",
            bordercolor="rgba(255, 255, 255, 0.1)",
            font=dict(color="#ffffff", size=12)
        )
    )
    # Configuración de ejes sutiles
    fig.update_xaxes(
        gridcolor='rgba(255, 255, 255, 0.04)',
        zerolinecolor='rgba(255, 255, 255, 0.08)',
        tickfont=dict(color='#94a3b8'),
        title_font=dict(color='#cbd5e1')
    )
    fig.update_yaxes(
        gridcolor='rgba(255, 255, 255, 0.04)',
        zerolinecolor='rgba(255, 255, 255, 0.08)',
        tickfont=dict(color='#94a3b8'),
        title_font=dict(color='#cbd5e1')
    )
    return fig

def categorizar_riesgo(row):
    """Categoriza un envío según las auditorías del motor Prolog."""
    is_critico = False
    is_atencion = False
    
    # Evaluar prioridad / criticidad alta
    if row.get('prioridad_alta') == True:
        is_critico = True
    if str(row.get('diagnostico_ia', '')).strip().lower() in ['critico_financiero', 'riesgo_alto']:
        is_critico = True
    if str(row.get('estado_auditoria', '')).strip().lower() in ['riesgo_alto', 'critico_financiero']:
        is_critico = True
    if 'alertas_detalladas' in row and pd.notna(row['alertas_detalladas']):
        alertas = str(row['alertas_detalladas'])
        if any(w in alertas for w in ['Riesgo', 'Tarifa', 'Fraude']):
            is_critico = True
            
    # Evaluar sobrecosto / alertas financieras (Riesgo medio)
    if row.get('alerta_costo') == True:
        is_atencion = True
    if str(row.get('estado_auditoria', '')).strip().lower() == 'riesgo_medio':
        is_atencion = True
    if 'alertas_detalladas' in row and pd.notna(row['alertas_detalladas']):
        alertas = str(row['alertas_detalladas'])
        if any(w in alertas for w in ['Retraso', 'Vehículo']):
            is_atencion = True
            
    if is_critico:
        return '🚨 Crítico / SLA'
    elif is_atencion:
        return '⚠️ Flete / Alerta'
    else:
        return '✅ Operación Normal'

def renderizar_grafico_canal(df):
    """1. Volumen de Carga por Canal de Captura (Donut Chart)"""
    st.markdown("<p style='color: #8b949e; font-weight:bold; font-size:1.05rem; margin-bottom:0;'>Volumen por Origen de Datos</p>", unsafe_allow_html=True)
    
    if df is None or df.empty:
        st.caption("Sin datos suficientes.")
        return
        
    fuente_col = 'fuente' if 'fuente' in df.columns else ('fuente_datos' if 'fuente_datos' in df.columns else None)
    if not fuente_col:
        st.caption("Campo de procedencia ausente.")
        return

    counts = df[fuente_col].value_counts().reset_index()
    counts.columns = ['Origen', 'Cantidad']
    counts['Origen'] = counts['Origen'].map(lambda x: DICCIONARIO_FUENTES.get(x, str(x)))
    
    if PLOTLY_DISPONIBLE:
        fig = px.pie(
            counts,
            names='Origen',
            values='Cantidad',
            hole=0.45,
            color_discrete_sequence=['#3b82f6', '#06b6d4', '#6366f1']
        )
        fig.update_traces(textinfo='percent', textposition='inside')
        aplicar_estilos_plotly(fig)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        # Fallback resiliente
        chart_data = counts.set_index('Origen')['Cantidad']
        st.bar_chart(chart_data, color="#3b82f6")

def renderizar_grafico_estados(df):
    """2. Distribución de Envíos por Estado Lógico (Vertical Bar Chart)"""
    st.markdown("<p style='color: #8b949e; font-weight:bold; font-size:1.05rem; margin-bottom:0;'>Distribución de Estados Operativos</p>", unsafe_allow_html=True)
    
    if df is None or df.empty:
        st.caption("Sin datos suficientes.")
        return

    if 'estado' not in df.columns:
        st.caption("Campo de estado ausente.")
        return

    counts = df['estado'].value_counts().reset_index()
    counts.columns = ['Estado_Raw', 'Cantidad']
    counts['Estado'] = counts['Estado_Raw'].map(lambda x: DICCIONARIO_ESTADOS.get(x, str(x).replace('_', ' ').title()))
    
    # Mapa de colores empresariales específicos por estado
    color_discrete_map = {
        '📦 En Bodega': '#64748b',       # Gris/Slate
        '🚛 En Tránsito': '#3b82f6',     # Azul
        '⚠️ En Novedad': '#ef4444',      # Rojo
        '✅ Entregado': '#10b981',       # Verde Esmeralda
        '📝 En Preparación': '#8b5cf6',   # Púrpura
        '🔍 En Revisión Doc': '#f59e0b'   # Ámbar
    }

    if PLOTLY_DISPONIBLE:
        fig = px.bar(
            counts,
            x='Estado',
            y='Cantidad',
            color='Estado',
            color_discrete_map=color_discrete_map,
            category_orders={"Estado": list(color_discrete_map.keys())}
        )
        fig.update_layout(showlegend=False)
        fig.update_traces(
            marker_line_color='rgba(255,255,255,0.1)',
            marker_line_width=1,
            opacity=0.9
        )
        aplicar_estilos_plotly(fig)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        chart_data = counts.set_index('Estado')['Cantidad']
        st.bar_chart(chart_data, color="#3b82f6")

def renderizar_grafico_costos(df):
    """3. Costo Acumulado de Flete por Ciudad de Destino (Horizontal Bar Chart)"""
    st.markdown("<p style='color: #8b949e; font-weight:bold; font-size:1.05rem; margin-bottom:0;'>Fletes Acumulados por Destino (COP)</p>", unsafe_allow_html=True)
    
    if df is None or df.empty:
        st.caption("Sin datos suficientes.")
        return

    costo_col = 'costo_flete' if 'costo_flete' in df.columns else None
    destino_col = 'destino' if 'destino' in df.columns else None
    
    if not costo_col or not destino_col:
        st.caption("Campos de costos o destino ausentes.")
        return

    # Limpiar y agrupar top destinos por costo
    df_clean = df.copy()
    df_clean[costo_col] = pd.to_numeric(df_clean[costo_col], errors='coerce').fillna(0)
    df_clean['Destino'] = df_clean[destino_col].astype(str).str.title()
    
    df_grouped = df_clean.groupby('Destino')[costo_col].sum().reset_index()
    df_grouped = df_grouped.sort_values(by=costo_col, ascending=True).tail(8) # Top 8 ciudades de llegada
    df_grouped.columns = ['Destino', 'Flete Total']

    if PLOTLY_DISPONIBLE:
        fig = px.bar(
            df_grouped,
            x='Flete Total',
            y='Destino',
            orientation='h',
            color='Flete Total',
            color_continuous_scale=['#065f46', '#10b981', '#34d399'] # Degradado esmeralda
        )
        fig.update_layout(coloraxis_showscale=False)
        fig.update_traces(
            texttemplate='$%{x:,.0f}', 
            textposition='outside',
            cliponaxis=False
        )
        aplicar_estilos_plotly(fig)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        chart_data = df_grouped.set_index('Destino')['Flete Total']
        st.bar_chart(chart_data, color="#10b981")

def renderizar_grafico_ia(df):
    """4. Distribución de Auditorías e Inferencias de IA Prolog (Donut/Bar Chart)"""
    st.markdown("<p style='color: #8b949e; font-weight:bold; font-size:1.05rem; margin-bottom:0;'>Diagnóstico de Auditoría (IA Prolog)</p>", unsafe_allow_html=True)
    
    if df is None or df.empty:
        st.caption("Sin datos suficientes.")
        return

    # Aplicar categorización de riesgos
    df_cat = df.copy()
    df_cat['Riesgo_IA'] = df_cat.apply(categorizar_riesgo, axis=1)
    
    counts = df_cat['Riesgo_IA'].value_counts().reset_index()
    counts.columns = ['Auditoria', 'Cantidad']
    
    color_map = {
        '🚨 Crítico / SLA': '#ef4444',
        '⚠️ Flete / Alerta': '#f59e0b',
        '✅ Operación Normal': '#10b981'
    }

    if PLOTLY_DISPONIBLE:
        fig = px.pie(
            counts,
            names='Auditoria',
            values='Cantidad',
            hole=0.45,
            color='Auditoria',
            color_discrete_map=color_map,
            category_orders={"Auditoria": list(color_map.keys())}
        )
        fig.update_traces(textinfo='percent', textposition='inside')
        aplicar_estilos_plotly(fig)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        chart_data = counts.set_index('Auditoria')['Cantidad']
        st.bar_chart(chart_data, color="#ef4444")
