# ui/view_operador.py - Vista de Operador (Básico) de ATHENEA
import streamlit as st
import pandas as pd
import os
import time
import unicodedata
from brain.prolog_driver import auditar_envio

def renderizar_vista_operador():
    """
    Renderiza la interfaz del operador básico para ingestar y auditar
    archivos Excel de transporte.
    """
    st.markdown("### 📥 Panel de Operaciones - Ingestar y Auditar Excel")
    st.write("Sube un archivo Excel (.xlsx/.xls) para procesar e ingestar datos en la plataforma.")
    
    if 'excel_preliminar' not in st.session_state:
        st.session_state['excel_preliminar'] = None
    if 'last_uploaded_file_key' not in st.session_state:
        st.session_state['last_uploaded_file_key'] = None
        
    # Componente de carga centralizado
    uploaded_file = st.file_uploader("📊 Selecciona un archivo Excel", type=["xlsx", "xls"], help="Sube el archivo de envíos en formato Excel para procesarlo.")
    
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
            if st.button("✅ Confirmar cargue", type="primary", use_container_width=True, help="Aprueba y carga los datos revisados al sistema central."):
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
            if st.button("❌ Denegar cargue", type="secondary", use_container_width=True, help="Descarta los datos actuales y cancela el proceso de carga."):
                st.session_state['excel_preliminar'] = None
                st.session_state['last_uploaded_file_key'] = None
                st.info("Cargue preliminar denegado.")
                time.sleep(1.5)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
