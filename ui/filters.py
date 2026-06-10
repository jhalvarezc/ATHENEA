# ui/filters.py - Barra de filtros horizontal interactiva para ATHENEA
import streamlit as st
import pandas as pd

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

def renderizar_barra_filtros(df, key_prefix="app", mostrar_flete=True):
    """
    Dibuja una barra de filtros horizontal premium.
    Retorna el DataFrame filtrado.
    """
    if df is None or df.empty:
        return df

    # Asegurar que las columnas clave existan para evitar KeyErrors
    df_clean = df.copy()
    if 'fuente' not in df_clean.columns:
        df_clean['fuente'] = 'Data_Lake_CSV'
    df_clean['fuente'] = df_clean['fuente'].fillna('Data_Lake_CSV').astype(str)
    
    if 'estado' not in df_clean.columns:
        df_clean['estado'] = 'en_transito'
    df_clean['estado'] = df_clean['estado'].fillna('en_transito').astype(str)
    
    if 'destino' not in df_clean.columns:
        df_clean['destino'] = 'bogota'
    df_clean['destino'] = df_clean['destino'].fillna('bogota').astype(str)

    if 'costo_flete' not in df_clean.columns:
        df_clean['costo_flete'] = 0.0
    df_clean['costo_flete'] = pd.to_numeric(df_clean['costo_flete'], errors='coerce').fillna(0)

    # Crear el panel contenedor de filtros
    with st.container(border=True):
        st.markdown("<p style='margin:0 0 10px 0; font-size:0.9rem; font-weight:700; color:#38bdf8;'>⚙️ FILTROS DE OPERACIÓN Y BÚSQUEDA</p>", unsafe_allow_html=True)
        
        # Grid de columnas para los selectores horizontales
        if mostrar_flete:
            col_search, col_estado, col_destino, col_origen, col_flete = st.columns([1.5, 1.2, 1.2, 1.2, 1.4])
        else:
            col_search, col_estado, col_destino, col_origen = st.columns([1.8, 1.4, 1.4, 1.4])
            col_flete = None
            
        with col_search:
            busqueda_guia = st.text_input(
                "🔍 Buscar guía / remisión:",
                "",
                key=f"{key_prefix}_search_input",
                placeholder="Escribe código de guía...",
                help="Ingresa el número de guía exacto para localizar un envío específico."
            ).strip()

        with col_estado:
            estados_disp = df_clean['estado'].unique().tolist()
            estados_map = {DICCIONARIO_ESTADOS.get(e, str(e).replace('_', ' ').title()): e for e in estados_disp if pd.notna(e)}
            estados_sel_amigables = st.multiselect(
                "📦 Estado Lógico:",
                options=list(estados_map.keys()),
                default=[],
                placeholder="Todos",
                key=f"{key_prefix}_multisel_estados",
                help="Filtra los envíos según su estado actual en la operación logística."
            )
            estados_sel = [estados_map[e] for e in estados_sel_amigables]

        with col_destino:
            destinos_disp = df_clean['destino'].unique().tolist()
            destinos_map = {str(d).split('/')[0].strip().title(): d for d in destinos_disp if pd.notna(d)}
            destinos_sel_amigables = st.multiselect(
                "📍 Ciudad Destino:",
                options=list(destinos_map.keys()),
                default=[],
                placeholder="Todos",
                key=f"{key_prefix}_multisel_destinos",
                help="Selecciona una o más ciudades para ver los envíos dirigidos a esos destinos."
            )
            destinos_sel = [destinos_map[d] for d in destinos_sel_amigables]

        with col_origen:
            fuentes_disp = df_clean['fuente'].unique().tolist()
            fuentes_map = {DICCIONARIO_FUENTES.get(f, f): f for f in fuentes_disp if pd.notna(f)}
            fuentes_sel_amigables = st.multiselect(
                "📁 Origen de Datos:",
                options=list(fuentes_map.keys()),
                default=[],
                placeholder="Todos",
                key=f"{key_prefix}_multisel_fuentes",
                help="Filtra los datos por la fuente de origen, como histórico CSV o cargues de Excel."
            )
            fuentes_sel = [fuentes_map[f] for f in fuentes_sel_amigables]

        flete_minimo = 0
        if col_flete is not None:
            with col_flete:
                max_flete = int(df_clean['costo_flete'].max()) if len(df_clean) > 0 else 100000
                if max_flete <= 0:
                    max_flete = 100000
                flete_minimo = st.slider(
                    "💰 Fletes mayores a ($):",
                    0,
                    max_flete,
                    0,
                    key=f"{key_prefix}_slider_flete",
                    help="Desliza para ver envíos cuyo costo de flete es mayor al valor seleccionado."
                )

    # Aplicar filtros al DataFrame
    # Blindaje contra listas de selección vacías (si el usuario limpia la selección, no mostrar nada o mostrar todo. Mostraremos todo si se limpia para mejor UX)
    if not estados_sel:
        estados_sel = df_clean['estado'].unique().tolist()
    if not destinos_sel:
        destinos_sel = df_clean['destino'].unique().tolist()
    if not fuentes_sel:
        fuentes_sel = df_clean['fuente'].unique().tolist()

    df_filtrado = df_clean[
        (df_clean['estado'].isin(estados_sel)) &
        (df_clean['destino'].isin(destinos_sel)) &
        (df_clean['fuente'].isin(fuentes_sel)) &
        (df_clean['costo_flete'] >= flete_minimo)
    ]

    if busqueda_guia:
        df_filtrado = df_filtrado[df_filtrado['guia'].str.contains(busqueda_guia, case=False)]

    return df_filtrado
