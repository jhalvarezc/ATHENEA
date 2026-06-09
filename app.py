# app.py - Dashboard Modularizado ATHENEA (Orquestador Central de UI)
import streamlit as st
import pandas as pd
import pydeck as pdk
import os
import time

# Importación segura de tus componentes modulares
from ui.styles import aplicar_estilos_dark, renderizar_encabezado, COORDENADAS_CIUDADES, normalizar_ciudad
from drivers.osrm_driver import obtener_ruta_calle
from brain.prolog_driver import consultar_regla
from storage.csv_manager import obtener_datos_consolidados
from ui.auth import requerir_autenticacion

# 1. Configuración de Ventana e Inyección de Estilos HTML/CSS
st.set_page_config(
    page_title="ATHENEA Dashboard", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)
aplicar_estilos_dark()
renderizar_encabezado()

# ==========================================
# 🔒 SISTEMA DE LOGIN BLOQUEANTE
# ==========================================
rol_usuario = requerir_autenticacion()

# Botón de cierre de sesión en la barra lateral
st.sidebar.markdown(f"**Rol actual:** `{st.session_state.get('rol')}`")
st.sidebar.markdown('<div class="logout-btn-container">', unsafe_allow_html=True)
if st.sidebar.button("🔓 Cerrar Sesión", use_container_width=True):
    st.session_state["usuario_autenticado"] = False
    st.session_state["rol"] = None
    st.rerun()
st.sidebar.markdown('</div>', unsafe_allow_html=True)
st.sidebar.markdown("---")

# ==========================================
# 🎛️ CONTROL DE VISTAS POR ROL
# ==========================================

# ---------------------------------------------------------
# VISTA 1: PERFIL OPERADOR
# ---------------------------------------------------------
if rol_usuario == "basico":
    st.markdown("### 📥 Panel de Operaciones - Ingestar y Auditar Excel")
    st.write("Sube un archivo Excel (.xlsx/.xls) para procesar e ingestar datos en la plataforma.")
    
    if 'excel_preliminar' not in st.session_state:
        st.session_state['excel_preliminar'] = None
    if 'last_uploaded_file_key' not in st.session_state:
        st.session_state['last_uploaded_file_key'] = None
        
    # Componente de carga centralizado
    uploaded_file = st.file_uploader("📊 Selecciona un archivo Excel", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        file_key = f"parsed_{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state['last_uploaded_file_key'] != file_key:
            try:
                # 1. Leer el archivo crudo
                df_cargado = pd.read_excel(uploaded_file)
                
                # 2. 🧠 MAPEO INTELIGENTE DE COLUMNAS (Diccionario de Sinónimos)
                sinonimos = {
                    'guia': ['guia_id', 'id_guia', 'numero_guia', 'remision', 'codigo', 'id'],
                    'estado': ['estado_envio', 'status', 'estado_actual', 'fase', 'estado_auditoria'],
                    'origen': ['ciudad_origen', 'desde', 'punto_origen', 'salida'],
                    'destino': ['ciudad_destino', 'hacia', 'punto_destino', 'llegada'],
                    'costo_flete': ['flete', 'costo', 'valor_flete', 'precio', 'tarifa']
                }
                
                nuevos_nombres = {}
                for col in df_cargado.columns:
                    col_limpia = str(col).lower().strip() # Quita espacios y mayúsculas
                    # Busca a qué columna oficial pertenece
                    for oficial, lista_sinonimos in sinonimos.items():
                        if col_limpia == oficial or col_limpia in lista_sinonimos:
                            nuevos_nombres[col] = oficial
                            break
                            
                # 3. Aplicar la traducción universal
                df_cargado = df_cargado.rename(columns=nuevos_nombres)
                
                # Guardar en memoria
                st.session_state['excel_preliminar'] = df_cargado
                st.session_state['last_uploaded_file_key'] = file_key
                st.rerun()
                
            except Exception as e:
                st.error(f"🚨 Ocurrió un error al intentar leer el Excel: {e}")
                st.info("Asegúrate de tener instalada la librería openpyxl en tu terminal (ejecuta: pip install openpyxl)")
            
    if st.session_state['excel_preliminar'] is not None and not st.session_state['excel_preliminar'].empty:
        st.warning("⚠️ Datos cargados en memoria preliminar. Revísalos y edítalos antes de confirmar.")
        
        columnas_ocultar = ['costo_flete', 'recomendaciones']
        
        # Leemos TODAS las columnas que trae el Excel realmente
        columnas_reales = st.session_state['excel_preliminar'].columns.tolist()
        
        # Mostramos todo, excepto las que están en la lista negra (dinero y recomendaciones)
        cols_mostrar = [c for c in columnas_reales if c not in columnas_ocultar]
        
        df_editado = st.data_editor(
            st.session_state['excel_preliminar'][cols_mostrar],
            num_rows="dynamic",
            use_container_width=True,
            key="editor_operador"
        )
        
        col_confirm, col_deny = st.columns(2)
        with col_confirm:
            st.markdown('<div class="confirm-btn-container">', unsafe_allow_html=True)
            if st.button("✅ Confirmar cargue", type="primary", use_container_width=True):
                from brain.prolog_driver import auditar_envio
                registros_editados = df_editado.to_dict(orient='records')
                exitos = 0
                
                for idx, reg in enumerate(registros_editados):
                    # Recuperar costo_flete y recomendaciones ocultos de la fila original
                    original_reg = st.session_state['excel_preliminar'].iloc[idx].to_dict()
                    if 'costo_flete' in original_reg:
                        reg['costo_flete'] = original_reg['costo_flete']
                    if 'recomendaciones' in original_reg:
                        reg['recomendaciones'] = original_reg['recomendaciones']
                    
                    # Rellenar fechas por defecto si faltan para evitar errores de Prolog
                    for f in ['despacho_dia', 'despacho_mes', 'despacho_ano', 'limite_dia', 'limite_mes', 'limite_ano']:
                        if f not in reg:
                            reg[f] = original_reg.get(f, 1 if 'dia' in f or 'mes' in f else 2026)
                    
                    # Normalizar nombres de ciudad para evitar tildes y duplicados
                    import unicodedata
                    def limpiar_txt(val):
                        if not val or pd.isna(val):
                            return ""
                        return unicodedata.normalize('NFKD', str(val)).encode('ASCII', 'ignore').decode('utf-8').strip().lower()
                    
                    if 'origen' in reg:
                        reg['origen'] = limpiar_txt(reg['origen'])
                    if 'destino' in reg:
                        reg['destino'] = limpiar_txt(reg['destino'])

                    # Auditar con Prolog
                    reg['estado_auditoria'] = auditar_envio(reg)
                    
                    # Guardar en pendientes de aprobación (storage/data/pendientes_aprobacion.csv)
                    ruta_pendientes = os.path.join("storage", "data", "pendientes_aprobacion.csv")
                    df_nuevo = pd.DataFrame([reg])
                    if os.path.exists(ruta_pendientes):
                        try:
                            df_existente = pd.read_csv(ruta_pendientes)
                            df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
                        except Exception:
                            df_final = df_nuevo
                    else:
                        df_final = df_nuevo
                    os.makedirs(os.path.dirname(ruta_pendientes), exist_ok=True)
                    df_final.to_csv(ruta_pendientes, index=False)
                    exitos += 1
                    
                st.success(f"¡Se han auditado e ingestado {exitos} registros con éxito!")
                st.session_state['excel_preliminar'] = None
                st.session_state['last_uploaded_file_key'] = None
                time.sleep(2)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
                
        with col_deny:
            st.markdown('<div class="deny-btn-container">', unsafe_allow_html=True)
            if st.button("❌ Denegar cargue", type="secondary", use_container_width=True):
                st.session_state['excel_preliminar'] = None
                st.session_state['last_uploaded_file_key'] = None
                st.info("Cargue preliminar denegado.")
                time.sleep(1.5)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# VISTA 2: PERFIL ADMINISTRADOR
# ---------------------------------------------------------
elif rol_usuario == "admin":
    try:
        # 2. Sincronización Unificada de Datos (Ya viene enriquecida con la IA de Prolog de data_manager)
        datos_unificados = obtener_datos_consolidados()
        
        if datos_unificados is None or (isinstance(datos_unificados, pd.DataFrame) and datos_unificados.empty):
            st.warning("⚠️ No se detectaron registros válidos en la base de datos unificada.")
            st.stop()

        # --- 🛡️ SUPER BLINDAJE CONTRA KEYERROR Y TIPOS DE DATOS ---
        if 'fuente' not in datos_unificados.columns:
            datos_unificados['fuente'] = 'Data_Lake_CSV'
        datos_unificados['fuente'] = datos_unificados['fuente'].fillna('Data_Lake_CSV').astype(str)
        if 'guia' not in datos_unificados.columns:
            datos_unificados['guia'] = 'Desconocida'
        datos_unificados['guia'] = datos_unificados['guia'].astype(str).str.strip()
        if 'costo_flete' in datos_unificados.columns:
            datos_unificados['costo_flete'] = pd.to_numeric(datos_unificados['costo_flete'], errors='coerce').fillna(0)
        # ------------------------------------------------------------------

        # 3. Consulta Maestra de Diagnósticos en el Motor Prolog
        resultados_prolog = consultar_regla("analisis_ruta_completa(Guia, Origen, Destino, Diagnostico, fecha(7, 6, 2026))")
        
        dict_diagnosticos = {}
        for r in resultados_prolog:
            guia_val = r['Guia'].decode('utf-8') if isinstance(r['Guia'], bytes) else str(r['Guia'])
            diag_val = r['Diagnostico'].decode('utf-8') if isinstance(r['Diagnostico'], bytes) else str(r['Diagnostico'])
            dict_diagnosticos[guia_val.strip()] = diag_val
            
        datos_unificados['diagnostico_ia'] = datos_unificados['guia'].map(dict_diagnosticos).fillna('en_verificacion')

        # Diccionarios de traducción amigable para filtros
        DICCIONARIO_FUENTES = {
            'Data_Lake_CSV': '📁 Histórico (CSV)',
            'Cargue_Operador_Excel': '📥 Cargues Operador (Excel)'
        }
        
        DICCIONARIO_ESTADOS = {
            'en_bodega': '📦 En Bodega',
            'en_transito': '🚛 En Tránsito',
            'en_novedad': '⚠️ En Novedad',
            'entregado': '✅ Entregado',
            'preparacion': '📝 En Preparación',
            'en_revision_doc': '🔍 En Revisión Doc'
        }

        # 4. Barra de Filtros Horizontal Premium (reemplaza controles incómodos de sidebar)
        from ui.filters import renderizar_barra_filtros
        datos_filtrados = renderizar_barra_filtros(datos_unificados, key_prefix="admin_app", mostrar_flete=(rol_usuario != 'basico'))

        st.sidebar.markdown("---")
        st.sidebar.success("🟢 ATHENEA Inference Engine: Activo")

        st.markdown("---")

        tab_operativo, tab_urgentes, tab_predicciones = st.tabs([
            "🗺️ Monitoreo Operativo y Gráficas", 
            "🚨 Guías Urgentes (SLA Crítico)",
            "🔮 Inferencia y Predicciones de Inferencia IA"
        ])

        with tab_operativo:
            # 6. Monitoreo Geográfico de Redes y Canales (Mapa + Gráfico)
            st.markdown("<h2 style='font-size:1.5rem;'>🗺️ Monitoreo de Red Geográfica</h2>", unsafe_allow_html=True)
            list_guias = sorted([str(g) for g in datos_filtrados['guia'].unique().tolist()])

            with st.container(border=True):
                if list_guias:
                    guia_seleccionada = st.selectbox("🎯 Selecciona una guía para trazar ruta detallada:", list_guias)
                    fila_guia = datos_filtrados[datos_filtrados['guia'] == guia_seleccionada].iloc[0]
                    
                    flete_info = f" | **Flete:** ${fila_guia['costo_flete']:,} COP" if rol_usuario != 'basico' else ""
                    st.info(f"📍 **Detalle Actual:** {fila_guia['guia']} | **Origen:** {str(fila_guia['origen']).upper()} | **Destino:** {str(fila_guia['destino']).upper()}{flete_info} | **Fuente:** {fila_guia['fuente']}")
                    
                    # --- 🛡️ BLINDAJE GEOGRÁFICO CONTRA COORDENADAS NaN ---
                    try:
                        ciudad_orig = str(fila_guia['origen']).split('/')[0].strip()
                        ciudad_dest = str(fila_guia['destino']).split('/')[0].strip()
                        
                        ciudad_orig_norm = normalizar_ciudad(ciudad_orig)
                        ciudad_dest_norm = normalizar_ciudad(ciudad_dest)

                        if 'origen_latitude' not in fila_guia or pd.isna(fila_guia['origen_latitude']) or float(fila_guia['origen_latitude']) == 0:
                            orig_lat = COORDENADAS_CIUDADES.get(ciudad_orig_norm, COORDENADAS_CIUDADES["BOGOTA"])["lat"]
                            orig_lon = COORDENADAS_CIUDADES.get(ciudad_orig_norm, COORDENADAS_CIUDADES["BOGOTA"])["lon"]
                        else:
                            orig_lat = float(fila_guia['origen_latitude'])
                            orig_lon = float(fila_guia['origen_longitude'])

                        if 'destino_latitude' not in fila_guia or pd.isna(fila_guia['destino_latitude']) or float(fila_guia['destino_latitude']) == 0:
                            dest_lat = COORDENADAS_CIUDADES.get(ciudad_dest_norm, COORDENADAS_CIUDADES["BOGOTA"])["lat"]
                            dest_lon = COORDENADAS_CIUDADES.get(ciudad_dest_norm, COORDENADAS_CIUDADES["BOGOTA"])["lon"]
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

            st.markdown("---")
            st.markdown("<h2 style='font-size:1.5rem;'>📊 Métricas y Análisis de la Operación</h2>", unsafe_allow_html=True)
            try:
                from ui.charts import renderizar_tablero_analitico
                renderizar_tablero_analitico(datos_filtrados, rol_usuario)
            except Exception as e:
                st.error(f"Error cargando el tablero de análisis: {e}")

            # 7. Tablas de Control de Auditorías Específicas
            st.markdown("---")
            columnas_ocultar = []
            if rol_usuario == 'basico':
                columnas_ocultar = ['costo_flete', 'recomendaciones']
                
            columnas_mostrar = ['guia', 'origen', 'destino', 'estado', 'costo_flete', 'diagnostico_ia', 'fuente', 'recomendaciones']
            columnas_mostrar = [c for c in columnas_mostrar if c not in columnas_ocultar]
            
            columnas_validas = [col for col in columnas_mostrar if col in datos_filtrados.columns]
            
            f2_A, f2_B = st.columns(2)
            with f2_A:
                with st.container(border=True):
                    st.markdown("<h3 style='font-size:1.1rem; color:#ef4444;'>🚨 Auditoría de Riesgos y Alertas Críticas</h3>", unsafe_allow_html=True)
                    df_alertas = datos_filtrados[datos_filtrados['diagnostico_ia'] == 'critico_financiero']
                    if not df_alertas.empty:
                        st.dataframe(df_alertas[columnas_validas], width="stretch")
                    else:
                        st.info("No se detectaron alertas críticas con los filtros actuales.")
                
            with f2_B:
                with st.container(border=True):
                    st.markdown("<h3 style='font-size:1.1rem; color:#f28c0f;'>💰 Tarifas Fuera de Estándar (Prolog)</h3>", unsafe_allow_html=True)
                    if 'alerta_costo' in datos_filtrados.columns:
                        df_caros = datos_filtrados[datos_filtrados['alerta_costo'] == True]
                        if not df_caros.empty:
                            st.dataframe(df_caros[columnas_validas], width="stretch")
                        else:
                            st.info("No hay fletes con sobreprecio detectados.")
                    else:
                        st.caption("Esperando inicialización de métricas de costo.")
     
            # 8. Repositorio de Trazabilidad Total Completo
            st.markdown("---")
            st.markdown("<h2 style='font-size:1.4rem;'>📋 Repositorio Central de Trazabilidad Logística</h2>", unsafe_allow_html=True)
            with st.container(border=True):
                st.dataframe(datos_filtrados[columnas_validas], width="stretch")

        with tab_urgentes:
            st.components.v1.html("""
            <div style="text-align: center; padding: 10px 0;">
                <h1 id="animated-title" style="font-family: 'Outfit', -apple-system, sans-serif; font-weight: 800; color: #ffffff; margin: 0; font-size: 2.2rem; opacity: 0; transform: translateY(30px); letter-spacing: -0.02em;">
                    🚨 Alertas de Guías Urgentes (SLA Crítico)
                </h1>
            </div>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
            <script>
                setTimeout(() => {
                    const title = document.getElementById('animated-title');
                    if (title) {
                        const text = title.textContent.trim();
                        title.innerHTML = '';
                        for (let char of text) {
                            const span = document.createElement('span');
                            span.textContent = char;
                            span.style.display = 'inline-block';
                            span.style.opacity = '0';
                            span.style.transform = 'translateY(30px)';
                            if (char === ' ') {
                                span.innerHTML = '&nbsp;';
                            }
                            title.appendChild(span);
                        }
                        title.style.opacity = '1';
                        title.style.transform = 'none';
                        
                        gsap.to(title.children, {
                            opacity: 1,
                            y: 0,
                            duration: 1.0,
                            stagger: 0.03,
                            ease: 'power3.out'
                        });
                    }
                }, 50);
            </script>
            """, height=80)
            
            st.write("Listado de envíos que requieren atención inmediata debido a demoras de tránsito, despacho o alertas de tarifas elevadas (motor de inferencia Prolog).")
            
            try:
                res_urg = consultar_regla("guia_urgente(Guia, Origen, Destino, Estado, Costo, Diagnostico)")
                list_urgentes = []
                for r in res_urg:
                    g = r['Guia'].decode('utf-8') if isinstance(r['Guia'], bytes) else str(r['Guia'])
                    o = r['Origen'].decode('utf-8') if isinstance(r['Origen'], bytes) else str(r['Origen'])
                    d = r['Destino'].decode('utf-8') if isinstance(r['Destino'], bytes) else str(r['Destino'])
                    est = r['Estado'].decode('utf-8') if isinstance(r['Estado'], bytes) else str(r['Estado'])
                    cost = float(r['Costo'])
                    diag = r['Diagnostico'].decode('utf-8') if isinstance(r['Diagnostico'], bytes) else str(r['Diagnostico'])
                    
                    list_urgentes.append({
                        'Guía': g,
                        'Origen': o.upper(),
                        'Destino': d.upper(),
                        'Estado': DICCIONARIO_ESTADOS.get(est, est.replace('_', ' ').title()),
                        'Costo Flete': cost,
                        'Diagnóstico Inferencia': diag
                    })
                df_urgentes_prolog = pd.DataFrame(list_urgentes)
                
                # Filtrar contra los datos_filtrados de la barra lateral
                if not df_urgentes_prolog.empty and not datos_filtrados.empty:
                    guias_activas = set(datos_filtrados['guia'].unique())
                    df_urgentes_prolog = df_urgentes_prolog[df_urgentes_prolog['Guía'].isin(guias_activas)]
            except Exception as e:
                st.error(f"Error consultando guías urgentes en Prolog: {e}")
                df_urgentes_prolog = pd.DataFrame()
                
            if not df_urgentes_prolog.empty:
                # 1. Renderizar Gráficos de Urgencias
                try:
                    from ui.charts import renderizar_graficos_urgentes
                    renderizar_graficos_urgentes(df_urgentes_prolog)
                except Exception as e:
                    st.error(f"Error cargando gráficos de urgencias: {e}")
                
                st.markdown("---")
                
                # 2. Formatear el costo de flete antes de mostrar y renderizar tabla
                df_urg_visual = df_urgentes_prolog.copy()
                df_urg_visual['Costo Flete'] = df_urg_visual['Costo Flete'].map(lambda x: f"${x:,.0f} COP")
                st.dataframe(df_urg_visual, use_container_width=True, hide_index=True)
            else:
                st.success("🟢 No se registran guías con alertas críticas o urgencias de SLA en el lote de datos seleccionado.")

        with tab_predicciones:
            st.markdown("<h2 style='font-size:1.5rem;'>🔮 Inferencia y Predicciones de Inferencia IA</h2>", unsafe_allow_html=True)
            st.write("Predicciones y análisis de tendencias calculados en tiempo real por el motor lógico de inferencia y forecast.")
            
            try:
                from brain.forecasting import predecir_operacion
                forecast = predecir_operacion(datos_filtrados)
            except Exception as e:
                st.error(f"Error cargando módulo predictivo: {e}")
                forecast = None
                
            if forecast:
                # Punto de Mayor Cuello de Botella (Alerta Principal)
                max_hub = forecast.get('max_hub')
                if max_hub:
                    st.error(f"🚨 **NODO CRÍTICO DE CUELLO DE BOTELLA:** Hub `{max_hub['ciudad']}` con **{max_hub['tasa_novedades']:.1f}%** de novedades. {max_hub['recomendacion']}")
                else:
                    st.success("🟢 **RED OPERATIVA ESTABLE:** No se detectan cuellos de botella críticos activos en los nodos logísticos.")
                
                st.markdown("---")
                
                pred_col1, pred_col2 = st.columns(2)
                
                with pred_col1:
                    with st.container(border=True):
                        st.markdown("<h3 style='font-size:1.2rem; color:#58a6ff;'>💰 Proyección de Costes Fiscales</h3>", unsafe_allow_html=True)
                        proyectado = forecast['costos']['proyectado']
                        categoria = forecast['costos']['categoria']
                        recomendacion = forecast['costos']['recomendacion']
                        
                        st.metric("Estimación Costo Final Año (12 meses)", f"${proyectado:,.0f} COP")
                        
                        if "Peligro" in categoria:
                            st.error(f"**Estado:** {categoria}")
                        elif "Precaucion" in categoria:
                            st.warning(f"**Estado:** {categoria}")
                        else:
                            st.success(f"**Estado:** {categoria}")
                        
                        st.info(f"💡 **Recomendación:** {recomendacion}")
                        
                with pred_col2:
                    with st.container(border=True):
                        st.markdown("<h3 style='font-size:1.2rem; color:#58a6ff;'>⚡ Proyección de Incumplimiento de SLA</h3>", unsafe_allow_html=True)
                        tasa_sla = forecast['sla']['tasa_fallo']
                        categoria_sla = forecast['sla']['categoria']
                        recom_sla = forecast['sla']['recomendacion']
                        
                        st.metric("Tasa de Fallo Proyectada en Entregas SLA", f"{tasa_sla:.1f}%")
                        
                        if "Critico" in categoria_sla:
                            st.error(f"**Estado:** {categoria_sla}")
                        elif "Riesgo" in categoria_sla:
                            st.warning(f"**Estado:** {categoria_sla}")
                        else:
                            st.success(f"**Estado:** {categoria_sla}")
                            
                        st.info(f"💡 **Recomendación:** {recom_sla}")
                        
                st.markdown("---")
                st.markdown("<h3 style='font-size:1.3rem;'>🏢 Predicción de Congestión en Hubs Logísticos</h3>", unsafe_allow_html=True)
                st.write("Análisis de probabilidad de colapso en nodos de llegada basado en la tasa acumulada de novedades.")
                
                hubs_data = forecast['hubs']
                if hubs_data:
                    df_hubs_visual = pd.DataFrame(hubs_data)
                    df_hubs_visual.columns = ["Hub (Ciudad)", "Tasa Novedades (%)", "Riesgo Predicho", "Recomendación Operativa"]
                    
                    df_hubs_visual["Tasa Novedades (%)"] = df_hubs_visual["Tasa Novedades (%)"].map(lambda x: f"{x:.1f}%")
                    
                    st.dataframe(df_hubs_visual, use_container_width=True, hide_index=True)
                else:
                    st.info("No hay datos de distribución geográfica para proyectar.")

    except Exception as e:
        st.error(f"Error general en la orquestación modular: {e}")