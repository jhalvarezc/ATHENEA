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

st.markdown("<h1 class='titulo-athenea'>🧠 ATHENEA - Centro de Inteligencia Logística</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #8b949e; margin-top:-10px;'>Plataforma modular de auditoría con motores Prolog y visualización geográfica.</p>", unsafe_allow_html=True)
st.markdown("---")

# Menú lateral de navegación
st.sidebar.markdown("<h2 style='font-size:1.2rem; color:#58a6ff;'>🧭 Navegación</h2>", unsafe_allow_html=True)
opcion = st.sidebar.radio(
    "Selecciona una vista:",
    ["Cargar Datos (Excel)", "Ver Estadísticas", "Ver Mapa"]
)

# Cargar los datos históricos
df_historico = leer_historico()

if opcion == "Cargar Datos (Excel)":
    st.markdown("### 📥 Cargar y Procesar Datos de Transporte")
    
    st.markdown("#### 📊 Importación desde Excel")
    st.write("Sube un archivo `.xlsx` o `.xls` para normalizar y auditar su contenido.")
    uploaded_file = st.file_uploader("Selecciona un archivo Excel", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        if st.button("🚀 Ingestar y Auditar Excel", use_container_width=True):
            try:
                # 1. Ingestión
                registros = parsear_excel(uploaded_file)
                exitos = 0
                for reg in registros:
                    # 2. Auditoría
                    reg['estado_auditoria'] = auditar_envio(reg)
                    # 3. Guardar en pendientes
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
        
        # Formatear fechas para mostrar en formato legible
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
        
        # Filtrado de columnas según el rol de seguridad (RBAC)
        columnas_ocultar = []
        if rol_usuario == 'basico':
            columnas_ocultar = ['costo_flete', 'recomendaciones']
            
        cols_visual = [
            'guia_id', 'origen', 'destino', 'estado_auditoria', 'alertas_detalladas', 'salud', 'categoria', 'recomendaciones', 'costo_flete',
            'fecha_despacho_legible', 'fecha_limite_legible'
        ]
        
        # Filtrar columnas
        cols_visual = [c for c in cols_visual if c not in columnas_ocultar]
        cols_mostrar = [c for c in cols_visual if c in df_visual.columns]
        
        # Tabla interactiva
        df_editado_visual = st.data_editor(
            df_visual[cols_mostrar],
            num_rows="dynamic",
            use_container_width=True,
            key="editor_OCR_Excel"
        )
        
        col_app, col_dec = st.columns(2)
        
        with col_app:
            if st.button("✅ Aprobar e Inyectar al Dashboard", type="primary", use_container_width=True):
                # Volver a mapear las celdas editadas al DataFrame de pendientes
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
                
                # Guardar aprobados
                df_aprobados_list = df_pendientes.to_dict(orient='records')
                # Añadir columna de procedencia / fuente para estadísticas
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
        
        # Analizar en tiempo real para las estadísticas con Prolog
        estados_auditoria = []
        for _, row in df_historico_audit.iterrows():
            dict_row = row.to_dict()
            try:
                # Usar get() para evitar KeyErrors, y float() primero por si hay valores como '1.0' o NaN
                dict_row['despacho_dia'] = int(float(dict_row.get('despacho_dia', 1) or 1))
                dict_row['despacho_mes'] = int(float(dict_row.get('despacho_mes', 1) or 1))
                dict_row['despacho_ano'] = int(float(dict_row.get('despacho_ano', 2026) or 2026))
                dict_row['limite_dia'] = int(float(dict_row.get('limite_dia', 1) or 1))
                dict_row['limite_mes'] = int(float(dict_row.get('limite_mes', 1) or 1))
                dict_row['limite_ano'] = int(float(dict_row.get('limite_ano', 2026) or 2026))
                dict_row['costo_flete'] = float(dict_row.get('costo_flete', 0) or 0)
            except ValueError:
                # Valores por defecto en caso de datos no numéricos o vacíos
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
                # Valores por defecto en caso de datos no numéricos o vacíos
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
