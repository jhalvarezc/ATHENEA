# ui/view_admin.py - Vista de Administrador de ATHENEA
import streamlit as st
import pandas as pd
import pydeck as pdk
import os
import time

from ui.styles import COORDENADAS_CIUDADES, normalizar_ciudad
from drivers.osrm_driver import obtener_ruta_calle
from brain.prolog_driver import consultar_regla
from storage.csv_manager import obtener_datos_consolidados
from ui.filters import renderizar_barra_filtros
from ui.charts import renderizar_tablero_analitico, renderizar_graficos_urgentes
from brain.forecasting import predecir_operacion

def renderizar_vista_admin(rol_usuario):
    """
    Renderiza la interfaz del administrador con el monitoreo geográfico,
    las gráficas del Control Center, las alertas SLA y predicciones.
    """
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
        datos_filtrados = renderizar_barra_filtros(datos_unificados, key_prefix="admin_app", mostrar_flete=(rol_usuario != 'basico'))

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

        # ==========================================
        # 🩺 AUDITORÍA DE INTEGRIDAD DE DATOS (DATA HEALTH)
        # ==========================================
        with st.expander("🩺 Auditoría de Integridad de Datos (Data Health)"):
            st.markdown("### 🔍 Conciliación y Calidad de Datos (Reconciliation System)")
            st.write("Auditoría cruzada en caliente entre los archivos de carga del operador (`pendientes_aprobacion.csv`) y la base de datos unificada procesada por el motor de inferencia.")
            
            # 1. Cargar archivo crudo de pendientes de aprobación
            ruta_pendientes = os.path.join("storage", "data", "pendientes_aprobacion.csv")
            if os.path.exists(ruta_pendientes):
                try:
                    df_raw_pendientes = pd.read_csv(ruta_pendientes)
                except Exception as ex:
                    df_raw_pendientes = pd.DataFrame()
            else:
                df_raw_pendientes = pd.DataFrame()
                
            # 2. Filtrar los registros correspondientes en datos_unificados
            # En csv_manager.py, los pendientes se marcan con la fuente 'Cargue_Operador_Excel'
            df_processed_pendientes = datos_unificados[datos_unificados['fuente'] == 'Cargue_Operador_Excel']
            
            # 3. Métricas
            raw_count = len(df_raw_pendientes)
            processed_count = len(df_processed_pendientes)
            diff_count = abs(raw_count - processed_count)
            
            # Costo flete crudo
            raw_flete_col = 'costo_flete' if 'costo_flete' in df_raw_pendientes.columns else ('flete' if 'flete' in df_raw_pendientes.columns else None)
            if raw_flete_col:
                raw_flete_sum = pd.to_numeric(df_raw_pendientes[raw_flete_col], errors='coerce').fillna(0).sum()
            else:
                raw_flete_sum = 0.0
                
            processed_flete_sum = pd.to_numeric(df_processed_pendientes['costo_flete'], errors='coerce').fillna(0).sum()
            diff_flete = abs(raw_flete_sum - processed_flete_sum)
            
            # Completitud (Nulos en columnas clave)
            nulls_raw = 0
            if not df_raw_pendientes.empty:
                exist_cols = [c for c in ['guia', 'estado', 'origen', 'destino'] if c in df_raw_pendientes.columns]
                if exist_cols:
                    nulls_raw = df_raw_pendientes[exist_cols].isna().sum().sum()
            
            nulls_processed = 0
            if not df_processed_pendientes.empty:
                exist_cols_proc = [c for c in ['guia', 'estado', 'origen', 'destino'] if c in df_processed_pendientes.columns]
                if exist_cols_proc:
                    nulls_processed = df_processed_pendientes[exist_cols_proc].isna().sum().sum()
                    
            # Visualización de métricas
            col_m1, col_m2, col_m3 = st.columns(3)
            
            with col_m1:
                st.metric(
                    label="📋 Conteo de Registros",
                    value=f"{processed_count} / {raw_count}",
                    delta=f"Diff: -{diff_count}" if diff_count != 0 else "0 (Coincidencia Perfecta)",
                    delta_color="normal" if diff_count == 0 else "inverse"
                )
                
            with col_m2:
                st.metric(
                    label="💰 Flete Total Auditado",
                    value=f"$ {processed_flete_sum:,.0f} COP",
                    delta=f"Diff: -$ {diff_flete:,.0f} COP" if diff_flete != 0 else "0 (Conciliación Perfecta)",
                    delta_color="normal" if diff_flete == 0 else "inverse"
                )
                
            with col_m3:
                total_nulls = nulls_raw + nulls_processed
                st.metric(
                    label="🔍 Valores Nulos Detectados",
                    value=f"{total_nulls}",
                    delta="Limpieza Completa" if total_nulls == 0 else f"{total_nulls} nulos",
                    delta_color="normal" if total_nulls == 0 else "inverse"
                )
                
            # Estado global de integridad
            if diff_count == 0 and diff_flete == 0 and total_nulls == 0:
                st.success("✅ **La integridad de los datos es del 100%**. Los registros cargados por el operador y los procesados en el dashboard coinciden exactamente sin pérdidas ni fallos de tipado.")
            else:
                detalles_err = []
                if diff_count != 0:
                    detalles_err.append(f"Discrepancia en registros: se cargaron {raw_count} pero se procesaron {processed_count} (Diferencia de {diff_count} guías).")
                if diff_flete != 0:
                    detalles_err.append(f"Discrepancia financiera: suma cruda es $ {raw_flete_sum:,.0f} COP vs procesada $ {processed_flete_sum:,.0f} COP (Diferencia de $ {diff_flete:,.0f} COP).")
                if total_nulls != 0:
                    detalles_err.append(f"Se detectaron {total_nulls} valores nulos/inválidos en campos clave de los datasets.")
                    
                st.error("🚨 **Discrepancia detectada en la reconciliación de datos:**\n\n" + "\n".join([f"- {d}" for d in detalles_err]))

    except Exception as e:
        st.error(f"Error general en la orquestación modular: {e}")
