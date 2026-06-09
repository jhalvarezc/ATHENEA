# dashboard/app.py - Orquestador principal de la UI en Streamlit
import sys
import os

# Forzar a Python a reconocer la raíz del proyecto ATHENEA
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st 
import pandas as pd
import shutil
import time

# Imports de la nueva arquitectura modular
from ingestion.excel_parser import parsear_excel
from brain.prolog_driver import auditar_envio
# Mapeo local de funciones CSV para el Dashboard (evitando modificar storage/csv_manager.py)
def leer_historico():
    ruta = os.path.join("storage", "data", "envios.csv")
    if os.path.exists(ruta):
        try:
            return pd.read_csv(ruta)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def leer_pendientes():
    ruta = os.path.join("storage", "data", "pendientes_aprobacion.csv")
    if os.path.exists(ruta):
        try:
            return pd.read_csv(ruta)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def guardar_pendiente_aprobacion(datos):
    ruta = os.path.join("storage", "data", "pendientes_aprobacion.csv")
    df_nuevo = pd.DataFrame([datos])
    if os.path.exists(ruta):
        try:
            df_existente = pd.read_csv(ruta)
            df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
        except Exception:
            df_final = df_nuevo
    else:
        df_final = df_nuevo
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    df_final.to_csv(ruta, index=False)

def guardar_aprobados(df_aprobados_list):
    ruta_oficial = os.path.join("storage", "data", "envios.csv")
    df_nuevo = pd.DataFrame(df_aprobados_list)
    if os.path.exists(ruta_oficial):
        try:
            df_historico = pd.read_csv(ruta_oficial)
            df_final = pd.concat([df_historico, df_nuevo], ignore_index=True)
        except Exception:
            df_final = df_nuevo
    else:
        df_final = df_nuevo
    os.makedirs(os.path.dirname(ruta_oficial), exist_ok=True)
    df_final.to_csv(ruta_oficial, index=False)

def limpiar_pendientes():
    ruta = os.path.join("storage", "data", "pendientes_aprobacion.csv")
    if os.path.exists(ruta):
        try:
            os.remove(ruta)
        except Exception:
            pass
from dashboard.metrics_ui import renderizar_metricas
from dashboard.map_ui import renderizar_mapa
from ui.auth import requerir_autenticacion

# Estilos visuales dark de la UI
def aplicar_estilos_dark():
    st.markdown("""
    <style>
        .stApp { background-color: #0b0f19; }
        [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #1f2937; }
        [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 18px; }
        h1, h2, h3, p, label { color: #e6edf3 !important; font-family: 'Inter', sans-serif; }
        .titulo-athenea { color: #e6edf3; font-weight: 800; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.set_page_config(
    page_title="ATHENEA Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)
aplicar_estilos_dark()

# --- SISTEMA DE LOGIN Y RBAC ---
rol_usuario = requerir_autenticacion()

# Botón de cierre de sesión en la barra lateral
st.sidebar.markdown(f"**Rol actual:** `{st.session_state.get('rol')}`")
if st.sidebar.button("🔓 Cerrar Sesión", use_container_width=True):
    st.session_state["usuario_autenticado"] = False
    st.session_state["rol"] = None
    st.rerun()
st.sidebar.markdown("---")

if rol_usuario == "basico":
    st.markdown("### 📥 Panel de Operaciones - Ingestar y Auditar Excel")
    st.write("Sube un archivo Excel (.xlsx/.xls) para procesar e ingestar datos en la plataforma.")
    
    if 'excel_preliminar' not in st.session_state:
        st.session_state['excel_preliminar'] = None
    if 'last_uploaded_file_key' not in st.session_state:
        st.session_state['last_uploaded_file_key'] = None
        
    uploaded_file = st.file_uploader("Selecciona un archivo Excel", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        file_key = f"parsed_{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state['last_uploaded_file_key'] != file_key:
            try:
                registros = parsear_excel(uploaded_file)
                st.session_state['excel_preliminar'] = pd.DataFrame(registros)
                st.session_state['last_uploaded_file_key'] = file_key
            except Exception as e:
                st.error(f"Error al leer el archivo Excel: {e}")
            
    if st.session_state['excel_preliminar'] is not None and not st.session_state['excel_preliminar'].empty:
        st.warning("⚠️ Datos cargados en memoria preliminar. Revísalos y edítalos antes de confirmar.")
        
        columnas_ocultar = ['costo_flete', 'recomendaciones']
        cols_visual = [
            'guia_id', 'origen', 'destino', 'estado_auditoria', 'costo_flete', 'recomendaciones',
            'despacho_dia', 'despacho_mes', 'despacho_ano',
            'limite_dia', 'limite_mes', 'limite_ano'
        ]
        cols_visual = [c for c in cols_visual if c in st.session_state['excel_preliminar'].columns]
        cols_mostrar = [c for c in cols_visual if c not in columnas_ocultar]
        
        df_editado = st.data_editor(
            st.session_state['excel_preliminar'][cols_mostrar],
            num_rows="dynamic",
            use_container_width=True,
            key="editor_operador"
        )
        
        col_confirm, col_deny = st.columns(2)
        with col_confirm:
            if st.button("✅ Confirmar cargue", type="primary", use_container_width=True):
                registros_editados = df_editado.to_dict(orient='records')
                exitos = 0
                
                for idx, reg in enumerate(registros_editados):
                    original_reg = st.session_state['excel_preliminar'].iloc[idx].to_dict()
                    reg['costo_flete'] = original_reg.get('costo_flete', 0)
                    reg['recomendaciones'] = original_reg.get('recomendaciones', '')
                    
                    for f in ['despacho_dia', 'despacho_mes', 'despacho_ano', 'limite_dia', 'limite_mes', 'limite_ano']:
                        if f not in reg:
                            reg[f] = original_reg.get(f, 1 if 'dia' in f or 'mes' in f else 2026)
                    
                    reg['estado_auditoria'] = auditar_envio(reg)
                    guardar_pendiente_aprobacion(reg)
                    exitos += 1
                    
                st.success(f"¡Se han auditado e ingestado {exitos} registros con éxito!")
                st.session_state['excel_preliminar'] = None
                st.session_state['last_uploaded_file_key'] = None
                time.sleep(2)
                st.rerun()
                
        with col_deny:
            if st.button("❌ Denegar cargue", type="secondary", use_container_width=True):
                st.session_state['excel_preliminar'] = None
                st.session_state['last_uploaded_file_key'] = None
                st.info("Cargue preliminar denegado.")
                time.sleep(1.5)
                st.rerun()

elif rol_usuario == "admin":
    # Menú lateral de navegación
    st.sidebar.markdown("<h2 style='font-size:1.2rem; color:#58a6ff;'>🧭 Navegación</h2>", unsafe_allow_html=True)
    opcion = st.sidebar.radio(
        "Selecciona una vista:",
        ["Cargar Datos (Excel)", "Ver Estadísticas", "Ver Mapa"]
    )
    
    df_historico = leer_historico()
    
    if opcion == "Cargar Datos (Excel)":
        st.markdown("### 📥 Cargar y Procesar Datos de Transporte")
        
        st.markdown("#### 📊 Importación desde Excel")
        st.write("Sube un archivo `.xlsx` o `.xls` para normalizar y auditar su contenido.")
        uploaded_file = st.file_uploader("Selecciona un archivo Excel", type=["xlsx", "xls"])
        
        if uploaded_file is not None:
            if st.button("🚀 Ingestar y Auditar Excel", use_container_width=True):
                try:
                    registros = parsear_excel(uploaded_file)
                    exitos = 0
                    for reg in registros:
                        reg['estado_auditoria'] = auditar_envio(reg)
                        guardar_pendiente_aprobacion(reg)
                        exitos += 1
                    st.success(f"¡Se procesaron y auditaron {exitos} filas de Excel!")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al procesar el archivo Excel: {e}")
    
        st.markdown("---")
        st.markdown("### 📥 Sala de Espera de Auditoría (Registros Pendientes)")
        
        df_pendientes = leer_pendientes()
        if not df_pendientes.empty:
            st.warning("⚠️ Registros detectados en sala de espera. Audita, corrige y aprueba el lote.")
            
            df_visual = df_pendientes.copy()
            
            def formatear_fecha(row, prefix):
                try:
                    dia = int(row[f'{prefix}_dia'])
                    mes = int(row[f'{prefix}_mes'])
                    ano = int(row[f'{prefix}_ano'])
                    return f"{dia:02d}/{mes:02d}/{ano:04d}"
                except Exception:
                    return "01/01/2026"
                    
            df_visual['fecha_despacho_legible'] = df_visual.apply(lambda r: formatear_fecha(r, 'despacho'), axis=1)
            df_visual['fecha_limite_legible'] = df_visual.apply(lambda r: formatear_fecha(r, 'limite'), axis=1)
            
            columnas_ocultar = []
            cols_visual = [
                'guia_id', 'origen', 'destino', 'estado_auditoria', 'alertas_detalladas', 'salud', 'categoria', 'recomendaciones', 'costo_flete',
                'fecha_despacho_legible', 'fecha_limite_legible'
            ]
            cols_visual = [c for c in cols_visual if c not in columnas_ocultar]
            cols_mostrar = [c for c in cols_visual if c in df_visual.columns]
            
            df_editado_visual = st.data_editor(
                df_visual[cols_mostrar],
                num_rows="dynamic",
                use_container_width=True,
                key="editor_OCR_Excel"
            )
            
            col_app, col_dec = st.columns(2)
            
            with col_app:
                if st.button("✅ Aprobar e Inyectar al Dashboard", type="primary", use_container_width=True):
                    for idx, row in df_editado_visual.iterrows():
                        if idx in df_pendientes.index:
                            for col in ['origen', 'destino', 'costo_flete']:
                                if col in df_editado_visual.columns:
                                    df_pendientes.at[idx, col] = row[col]
                                    
                            if 'fecha_despacho_legible' in df_editado_visual.columns:
                                try:
                                    d_partes = str(row['fecha_despacho_legible']).split('/')
                                    if len(d_partes) == 3:
                                        df_pendientes.at[idx, 'despacho_dia'] = int(d_partes[0])
                                        df_pendientes.at[idx, 'despacho_mes'] = int(d_partes[1])
                                        df_pendientes.at[idx, 'despacho_ano'] = int(d_partes[2])
                                except Exception:
                                    pass
                                    
                            if 'fecha_limite_legible' in df_editado_visual.columns:
                                try:
                                    l_partes = str(row['fecha_limite_legible']).split('/')
                                    if len(l_partes) == 3:
                                        df_pendientes.at[idx, 'limite_dia'] = int(l_partes[0])
                                        df_pendientes.at[idx, 'limite_mes'] = int(l_partes[1])
                                        df_pendientes.at[idx, 'limite_ano'] = int(l_partes[2])
                                except Exception:
                                    pass
                    
                    df_aprobados_list = df_pendientes.to_dict(orient='records')
                    for reg in df_aprobados_list:
                        reg['fuente'] = 'Excel_Importado'
                    
                    guardar_aprobados(df_aprobados_list)
                    limpiar_pendientes()
                                    
                    st.success("¡Base de datos histórica consolidada con éxito!")
                    time.sleep(2)
                    st.rerun()
    
            with col_dec:
                if st.button("🗑️ Descartar Sala de Espera", type="secondary", use_container_width=True):
                    limpiar_pendientes()
                    st.info("Sala de espera vaciada sin afectar históricos.")
                    st.rerun()
        else:
            st.info("No hay guías nuevas pendientes de aprobación.")
    
    elif opcion == "Ver Estadísticas":
        st.markdown("### 📊 Indicadores de Auditoría y Control")
        if df_historico.empty:
            st.info("No hay datos históricos disponibles. Ingesta algunos registros en la primera pestaña.")
        else:
            df_historico_audit = df_historico.copy()
            estados_auditoria = []
            for _, row in df_historico_audit.iterrows():
                dict_row = row.to_dict()
                try:
                    dict_row['despacho_dia'] = int(float(dict_row.get('despacho_dia', 1) or 1))
                    dict_row['despacho_mes'] = int(float(dict_row.get('despacho_mes', 1) or 1))
                    dict_row['despacho_ano'] = int(float(dict_row.get('despacho_ano', 2026) or 2026))
                    dict_row['limite_dia'] = int(float(dict_row.get('limite_dia', 1) or 1))
                    dict_row['limite_mes'] = int(float(dict_row.get('limite_mes', 1) or 1))
                    dict_row['limite_ano'] = int(float(dict_row.get('limite_ano', 2026) or 2026))
                    dict_row['costo_flete'] = float(dict_row.get('costo_flete', 0) or 0)
                except ValueError:
                    dict_row['despacho_dia'] = 1
                    dict_row['despacho_mes'] = 1
                    dict_row['despacho_ano'] = 2026
                    dict_row['limite_dia'] = 1
                    dict_row['limite_mes'] = 1
                    dict_row['limite_ano'] = 2026
                    dict_row['costo_flete'] = 0.0
    
                dict_row['estado'] = dict_row.get('estado', 'en_transito')
                estados_auditoria.append(auditar_envio(dict_row))
                
            df_historico_audit['estado_auditoria'] = estados_auditoria
            renderizar_metricas(df_historico_audit)
    
    elif opcion == "Ver Mapa":
        st.markdown("### 🗺️ Mapa Operativo y Trazabilidad")
        if df_historico.empty:
            st.info("No hay datos históricos para geolocalizar.")
        else:
            df_historico_audit = df_historico.copy()
            estados_auditoria = []
            for _, row in df_historico_audit.iterrows():
                dict_row = row.to_dict()
                try:
                    dict_row['despacho_dia'] = int(float(dict_row.get('despacho_dia', 1) or 1))
                    dict_row['despacho_mes'] = int(float(dict_row.get('despacho_mes', 1) or 1))
                    dict_row['despacho_ano'] = int(float(dict_row.get('despacho_ano', 2026) or 2026))
                    dict_row['limite_dia'] = int(float(dict_row.get('limite_dia', 1) or 1))
                    dict_row['limite_mes'] = int(float(dict_row.get('limite_mes', 1) or 1))
                    dict_row['limite_ano'] = int(float(dict_row.get('limite_ano', 2026) or 2026))
                    dict_row['costo_flete'] = float(dict_row.get('costo_flete', 0) or 0)
                except ValueError:
                    dict_row['despacho_dia'] = 1
                    dict_row['despacho_mes'] = 1
                    dict_row['despacho_ano'] = 2026
                    dict_row['limite_dia'] = 1
                    dict_row['limite_mes'] = 1
                    dict_row['limite_ano'] = 2026
                    dict_row['costo_flete'] = 0.0
    
                dict_row['estado'] = dict_row.get('estado', 'en_transito')
                estados_auditoria.append(auditar_envio(dict_row))
                
            df_historico_audit['estado_auditoria'] = estados_auditoria
            renderizar_mapa(df_historico_audit)
