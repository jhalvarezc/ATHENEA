# ui/charts.py - Generador de Gráficos Analíticos Premium para ATHENEA
import streamlit as st
import pandas as pd

# Diccionarios globales de traducción amigable para visualizaciones
DICCIONARIO_FUENTES = {
    'Data_Lake_CSV': '📁 Histórico (CSV)',
    'Cargue_Operador_Excel': '📥 Cargues (Excel)',
    'Excel_Importado': '📥 Cargues (Excel)'
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
        margin=dict(l=10, r=10, t=40, b=10),
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

# --- GRÁFICOS COMPATIBLES ANTERIORES (Por retrocompatibilidad) ---
def renderizar_grafico_canal(df):
    if df is None or df.empty:
        st.caption("Sin datos.")
        return
    fig = plot_donut_costo(df)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def renderizar_grafico_estados(df):
    if df is None or df.empty:
        st.caption("Sin datos.")
        return
    fig = plot_bar_cantidad_origen(df)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def renderizar_grafico_costos(df):
    if df is None or df.empty:
        st.caption("Sin datos.")
        return
    fig = plot_bar_costo_ruta(df)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def renderizar_grafico_ia(df):
    if df is None or df.empty:
        st.caption("Sin datos.")
        return
    df_cat = df.copy()
    df_cat['Riesgo_IA'] = df_cat.apply(categorizar_riesgo, axis=1)
    counts = df_cat['Riesgo_IA'].value_counts().reset_index()
    counts.columns = ['Auditoria', 'Cantidad']
    color_map = {
        '🚨 Crítico / SLA': '#ef4444',
        '⚠️ Flete / Alerta': '#f59e0b',
        '✅ Operación Normal': '#10b981'
    }
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

# --- NUEVOS ELEMENTOS DEL TABLERO CONTROL CENTER ---

def renderizar_kpis_verticales(df):
    """Calcula y dibuja la barra vertical de 4 KPIs del panel izquierdo."""
    total = len(df)
    finalizados = len(df[df['estado'] == 'entregado'])
    pendientes = len(df[~df['estado'].isin(['entregado', 'en_novedad'])])
    devueltos = len(df[df['estado'] == 'en_novedad'])
    
    pct_fin = (finalizados / total * 100) if total > 0 else 0
    pct_pen = (pendientes / total * 100) if total > 0 else 0
    pct_dev = (devueltos / total * 100) if total > 0 else 0
    
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; gap: 15px;">
        <div class="kpi-card-sidebar">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="kpi-title">Número de Envíos</span>
                <span class="kpi-icon">🚛</span>
            </div>
            <div class="kpi-value">{total:,}</div>
        </div>
        <div class="kpi-card-sidebar">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="kpi-title">Envíos Finalizados</span>
                <span class="kpi-icon">✅</span>
            </div>
            <div class="kpi-value">{finalizados:,}</div>
            <div class="kpi-percentage">{pct_fin:.1f}% del total</div>
        </div>
        <div class="kpi-card-sidebar">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="kpi-title">Envíos Pendientes</span>
                <span class="kpi-icon">⚠️</span>
            </div>
            <div class="kpi-value">{pendientes:,}</div>
            <div class="kpi-percentage">{pct_pen:.1f}% del total</div>
        </div>
        <div class="kpi-card-sidebar">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="kpi-title">Envíos Devueltos</span>
                <span class="kpi-icon">❌</span>
            </div>
            <div class="kpi-value">{devueltos:,}</div>
            <div class="kpi-percentage">{pct_dev:.1f}% del total</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def plot_envios_fecha(df):
    """Gráfico de línea suavizado de cantidad de envíos por fecha con línea de promedio."""
    df_date = df.copy()
    
    # Crear campo de fecha de despacho seguro
    for f in ['despacho_ano', 'despacho_mes', 'despacho_dia']:
        if f not in df_date.columns:
            df_date[f] = 1 if 'dia' in f or 'mes' in f else 2026
            
    df_date['fecha_dt'] = pd.to_datetime(
        df_date['despacho_ano'].astype(str) + '-' + 
        df_date['despacho_mes'].astype(str).str.zfill(2) + '-' + 
        df_date['despacho_dia'].astype(str).str.zfill(2), 
        errors='coerce'
    )
    df_date = df_date.dropna(subset=['fecha_dt'])
    
    if df_date.empty:
        # Fallback en caso de que no haya fechas
        df_date = pd.DataFrame([{'fecha_dt': pd.Timestamp('2026-06-01'), 'Cantidad': 1}])
        df_grouped = df_date.groupby('fecha_dt').size().reset_index(name='Cantidad')
        df_grouped['Periodo'] = 'Jun 2026'
    else:
        # Agrupar por mes y año para simular histórico
        df_date['Periodo'] = df_date['fecha_dt'].dt.strftime('%b %Y')
        df_date['YearMonth'] = df_date['fecha_dt'].dt.to_period('M')
        df_grouped = df_date.groupby(['YearMonth', 'Periodo']).size().reset_index(name='Cantidad')
        df_grouped = df_grouped.sort_values('YearMonth')

    # Si hay pocos periodos, agrupar por día para que se dibuje una gráfica de línea bonita
    if len(df_grouped) <= 1 and not df_date.empty:
        df_grouped = df_date.groupby('fecha_dt').size().reset_index(name='Cantidad')
        df_grouped['Periodo'] = df_grouped['fecha_dt'].dt.strftime('%d %b')
        df_grouped = df_grouped.sort_values('fecha_dt')

    fig = go.Figure()
    
    # Añadir traza con spline suavizado y relleno
    fig.add_trace(go.Scatter(
        x=df_grouped['Periodo'],
        y=df_grouped['Cantidad'],
        mode='lines+markers',
        line=dict(shape='spline', color='#38bdf8', width=3),
        fill='tozeroy',
        fillcolor='rgba(56, 189, 248, 0.08)',
        name='Envíos'
    ))
    
    # Calcular promedio
    avg_val = df_grouped['Cantidad'].mean() if not df_grouped.empty else 0
    fig.add_hline(
        y=avg_val, 
        line_dash="dash", 
        line_color="rgba(239, 68, 68, 0.7)", 
        annotation_text=f"Promedio: {avg_val:.1f}",
        annotation_position="top left",
        annotation_font=dict(color="#94a3b8", size=9)
    )
    
    fig.update_layout(
        title=dict(text="Cantidad de Envíos por Fecha", font=dict(size=13, color="#ffffff")),
        margin=dict(l=10, r=10, t=40, b=10),
        height=220
    )
    aplicar_estilos_plotly(fig)
    return fig

def plot_donut_costo(df):
    """Donut chart del costo total de flete distribuido por procedencia (fuente)."""
    df_clean = df.copy()
    if 'fuente' not in df_clean.columns:
        df_clean['fuente'] = 'Data_Lake_CSV'
    df_clean['fuente'] = df_clean['fuente'].fillna('Data_Lake_CSV').astype(str)
    
    cost_col = 'costo_flete' if 'costo_flete' in df_clean.columns else None
    if not cost_col:
        return go.Figure()
        
    df_grouped = df_clean.groupby('fuente')[cost_col].sum().reset_index()
    df_grouped.columns = ['Origen', 'Costo']
    df_grouped['Origen'] = df_grouped['Origen'].map(lambda x: DICCIONARIO_FUENTES.get(x, str(x)))
    
    fig = px.pie(
        df_grouped,
        names='Origen',
        values='Costo',
        hole=0.55,
        color_discrete_sequence=['#38bdf8', '#6366f1', '#10b981']
    )
    fig.update_traces(
        textinfo='percent',
        textposition='inside',
        marker=dict(line=dict(color='rgba(2,6,23,0.5)', width=2))
    )
    fig.update_layout(
        title=dict(text="Distribución de Costo de Flete", font=dict(size=13, color="#ffffff")),
        margin=dict(l=10, r=10, t=40, b=10),
        height=220,
        showlegend=True,
        legend=dict(
            orientation="h",
            y=-0.2,
            x=0.5,
            xanchor="center"
        )
    )
    aplicar_estilos_plotly(fig)
    return fig

def plot_bar_costo_ruta(df):
    """Gráfico de barras de flete acumulado por ciudad de destino."""
    cost_col = 'costo_flete' if 'costo_flete' in df.columns else None
    dest_col = 'destino' if 'destino' in df.columns else None
    
    if not cost_col or not dest_col:
        return go.Figure()
        
    df_clean = df.copy()
    df_clean['Destino'] = df_clean[dest_col].astype(str).str.title()
    df_grouped = df_clean.groupby('Destino')[cost_col].sum().reset_index()
    df_grouped = df_grouped.sort_values(by=cost_col, ascending=False).head(8)
    
    fig = px.bar(
        df_grouped,
        x='Destino',
        y=cost_col,
        text_auto='.2s',
        color=cost_col,
        color_continuous_scale=['#1d4ed8', '#3b82f6', '#60a5fa'] # Degradado de azul
    )
    fig.update_layout(
        title=dict(text="Costo Acumulado de Flete por Ruta", font=dict(size=13, color="#ffffff")),
        margin=dict(l=10, r=10, t=40, b=10),
        height=250,
        coloraxis_showscale=False
    )
    aplicar_estilos_plotly(fig)
    # Hacer las barras más delgadas y pulidas
    fig.update_traces(
        marker=dict(line=dict(color='rgba(255,255,255,0.05)', width=1)),
        width=0.45
    )
    return fig

def plot_bar_cantidad_origen(df):
    """Gráfico de barras de cantidad de envíos despachados por origen con línea de promedio."""
    orig_col = 'origen' if 'origen' in df.columns else None
    if not orig_col:
        return go.Figure()
        
    df_clean = df.copy()
    df_clean['Origen'] = df_clean[orig_col].astype(str).str.title()
    df_grouped = df_clean.groupby('Origen').size().reset_index(name='Cantidad')
    df_grouped = df_grouped.sort_values(by='Cantidad', ascending=False).head(8)
    
    fig = px.bar(
        df_grouped,
        x='Origen',
        y='Cantidad',
        text_auto=True,
        color='Cantidad',
        color_continuous_scale=['#4f46e5', '#6366f1', '#818cf8']
    )
    
    avg_val = df_grouped['Cantidad'].mean() if not df_grouped.empty else 0
    fig.add_hline(
        y=avg_val,
        line_dash="dash",
        line_color="rgba(16, 185, 129, 0.7)",
        annotation_text=f"Promedio: {avg_val:.1f}",
        annotation_position="top right",
        annotation_font=dict(color="#cbd5e1", size=9)
    )
    
    fig.update_layout(
        title=dict(text="Cantidad de Envíos por Origen (Despacho)", font=dict(size=13, color="#ffffff")),
        margin=dict(l=10, r=10, t=40, b=10),
        height=250,
        coloraxis_showscale=False
    )
    aplicar_estilos_plotly(fig)
    fig.update_traces(
        marker=dict(line=dict(color='rgba(255,255,255,0.05)', width=1)),
        width=0.45
    )
    return fig

def renderizar_tablero_analitico(df, rol_usuario):
    """
    Función maestra para orquestar y dibujar el tablero interactivo de control.
    Distribuye los elementos en un panel de KPIs lateral izquierdo y gráficos principales a la derecha.
    """
    if df is None or df.empty:
        st.warning("⚠️ No hay registros de envíos que coincidan con los filtros aplicados.")
        return

    # Sincronización del costo de flete
    df_clean = df.copy()
    if 'costo_flete' in df_clean.columns:
        df_clean['costo_flete'] = pd.to_numeric(df_clean['costo_flete'], errors='coerce').fillna(0)
    else:
        df_clean['costo_flete'] = 0.0

    # Grid principal: Columna de KPIs (20%) + Columna de gráficos (80%)
    col_sidebar, col_main = st.columns([1.3, 4.7])
    
    with col_sidebar:
        st.markdown("<p style='font-size:0.9rem; font-weight:700; color:#38bdf8; text-transform:uppercase; margin-bottom:10px;'>📊 RESUMEN</p>", unsafe_allow_html=True)
        renderizar_kpis_verticales(df_clean)
        
    with col_main:
        # Fila 1: Costo total (izquierda), Envíos por fecha (centro), Donut costo (derecha)
        r1_c1, r1_c2, r1_c3 = st.columns([1.2, 2.3, 1.5])
        
        with r1_c1:
            total_cost = df_clean['costo_flete'].sum()
            avg_cost = df_clean['costo_flete'].mean() if len(df_clean) > 0 else 0
            
            # Formatear a Pesos Colombianos según comentarios de aprobación
            flete_info_costo = f"$ {total_cost:,.0f}" if rol_usuario != 'basico' else "CONFIDENCIAL"
            flete_info_promedio = f"$ {avg_cost:,.0f}" if rol_usuario != 'basico' else "CONFIDENCIAL"
            
            st.markdown(f"""
            <div class="kpi-card-sidebar" style="height: 220px; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 20px;">
                <div class="kpi-title" style="margin-bottom: 12px; font-size: 0.85rem;">Costo Total de Envío</div>
                <div class="kpi-value" style="font-size: 1.85rem; color: #38bdf8; line-height: 1.2;">{flete_info_costo}</div>
                <div style="border-top: 1px solid rgba(255,255,255,0.08); width: 80%; margin: 15px 0;"></div>
                <div style="font-size: 0.85rem; color: #94a3b8; font-weight: 500;">Promedio: <span style="color: #ffffff; font-weight: 700;">{flete_info_promedio}</span></div>
            </div>
            """, unsafe_allow_html=True)
            
        with r1_c2:
            with st.container(border=True):
                fig_fecha = plot_envios_fecha(df_clean)
                st.plotly_chart(fig_fecha, use_container_width=True, config={'displayModeBar': False})
                
        with r1_c3:
            with st.container(border=True):
                if rol_usuario != 'basico':
                    fig_donut = plot_donut_costo(df_clean)
                    st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.markdown("""
                    <div class="kpi-card-sidebar" style="height: 220px; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;">
                        <span style="font-size: 2rem;">🔒</span>
                        <div class="kpi-title" style="margin-top: 10px;">Costos Restringidos</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        # Fila 2: Costo por ruta (con estadísticas al lado, izquierda), Cantidad de envíos por origen (derecha)
        r2_c1, r2_c2 = st.columns([2.5, 2.5])
        
        with r2_c1:
            with st.container(border=True):
                if rol_usuario != 'basico':
                    # Subgrid para colocar las estadísticas del costo a la izquierda tal cual la imagen
                    sub_col_stats, sub_col_chart = st.columns([1, 2.4])
                    
                    with sub_col_stats:
                        df_grouped_all = df_clean.groupby('destino')['costo_flete'].sum().reset_index()
                        
                        if not df_grouped_all.empty:
                            idx_max = df_grouped_all['costo_flete'].idxmax()
                            max_dest = df_grouped_all.loc[idx_max, 'destino'].title()
                            max_val = df_grouped_all.loc[idx_max, 'costo_flete']
                            
                            idx_min = df_grouped_all['costo_flete'].idxmin()
                            min_dest = df_grouped_all.loc[idx_min, 'destino'].title()
                            min_val = df_grouped_all.loc[idx_min, 'costo_flete']
                            
                            avg_route_val = df_grouped_all['costo_flete'].mean()
                        else:
                            max_dest, max_val = "N/A", 0
                            min_dest, min_val = "N/A", 0
                            avg_route_val = 0
                            
                        st.markdown(f"""
                        <div style="display: flex; flex-direction: column; gap: 8px; justify-content: center; height: 100%; padding-top: 10px;">
                            <div>
                                <span style="font-size: 0.72rem; color: #94a3b8; font-weight: 600; text-transform: uppercase;">📈 Máximo</span>
                                <div style="font-size: 0.8rem; font-weight: 700; color: #ffffff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{max_dest}</div>
                                <div style="font-size: 1.05rem; font-weight: 800; color: #38bdf8;">$ {max_val:,.0f}</div>
                            </div>
                            <div style="border-top: 1px solid rgba(255,255,255,0.06); margin: 3px 0;"></div>
                            <div>
                                <span style="font-size: 0.72rem; color: #94a3b8; font-weight: 600; text-transform: uppercase;">📊 Promedio</span>
                                <div style="font-size: 1.05rem; font-weight: 800; color: #ffffff;">$ {avg_route_val:,.0f}</div>
                            </div>
                            <div style="border-top: 1px solid rgba(255,255,255,0.06); margin: 3px 0;"></div>
                            <div>
                                <span style="font-size: 0.72rem; color: #94a3b8; font-weight: 600; text-transform: uppercase;">📉 Mínimo</span>
                                <div style="font-size: 0.8rem; font-weight: 700; color: #ffffff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{min_dest}</div>
                                <div style="font-size: 1.05rem; font-weight: 800; color: #818cf8;">$ {min_val:,.0f}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with sub_col_chart:
                        fig_bar_costo = plot_bar_costo_ruta(df_clean)
                        st.plotly_chart(fig_bar_costo, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.markdown("""
                    <div class="kpi-card-sidebar" style="height: 250px; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;">
                        <span style="font-size: 2.2rem;">🔒</span>
                        <div class="kpi-title" style="margin-top: 10px;">Costos de Ruta Restringidos</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
        with r2_c2:
            with st.container(border=True):
                fig_bar_orig = plot_bar_cantidad_origen(df_clean)
                st.plotly_chart(fig_bar_orig, use_container_width=True, config={'displayModeBar': False})

def renderizar_graficos_urgentes(df_urgentes):
    """
    Dibuja gráficos específicos para la sección de Guías Urgentes:
    1. Donut Chart de Diagnósticos de Inferencia.
    2. Bar Chart de cantidad de urgencias por Ciudad de Destino.
    """
    if df_urgentes is None or df_urgentes.empty:
        return
        
    st.markdown("<h3 style='font-size:1.2rem; margin-top:20px; color:#ef4444;'>📈 Análisis Estadístico de Urgencias</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            counts_diag = df_urgentes['Diagnóstico Inferencia'].value_counts().reset_index()
            counts_diag.columns = ['Diagnostico', 'Cantidad']
            
            fig = px.pie(
                counts_diag,
                names='Diagnostico',
                values='Cantidad',
                hole=0.5,
                color_discrete_sequence=['#ef4444', '#f59e0b', '#ec4899', '#8b5cf6', '#3b82f6']
            )
            fig.update_traces(
                textinfo='percent+value',
                textposition='inside',
                marker=dict(line=dict(color='rgba(2,6,23,0.5)', width=2))
            )
            fig.update_layout(
                title=dict(text="Distribución de Diagnósticos de Alerta", font=dict(size=12, color="#ffffff")),
                margin=dict(l=10, r=10, t=40, b=10),
                height=220,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    y=-0.2,
                    x=0.5,
                    xanchor="center",
                    font=dict(size=9)
                )
            )
            aplicar_estilos_plotly(fig)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
    with col2:
        with st.container(border=True):
            counts_dest = df_urgentes['Destino'].value_counts().reset_index()
            counts_dest.columns = ['Destino', 'Cantidad']
            counts_dest = counts_dest.sort_values(by='Cantidad', ascending=False)
            
            fig = px.bar(
                counts_dest,
                x='Destino',
                y='Cantidad',
                text_auto=True,
                color='Cantidad',
                color_continuous_scale=['#f43f5e', '#e11d48', '#be123c'] # Degradado de rojo crítico
            )
            fig.update_layout(
                title=dict(text="Alertas Críticas por Ciudad de Destino", font=dict(size=12, color="#ffffff")),
                margin=dict(l=10, r=10, t=40, b=10),
                height=220,
                coloraxis_showscale=False
            )
            aplicar_estilos_plotly(fig)
            fig.update_traces(
                marker=dict(line=dict(color='rgba(255,255,255,0.05)', width=1)),
                width=0.45
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
