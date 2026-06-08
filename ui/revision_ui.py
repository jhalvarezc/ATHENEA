# ui/revision_ui.py - Panel de control y auditoría OCR para la interfaz de ATHENEA
import streamlit as st
import pandas as pd
import os
import subprocess
import shutil

def renderizar_bandeja_revision():
    """Módulo interactivo para escanear, auditar, editar y aprobar PDFs."""
    st.divider()
    st.markdown("### 📥 Panel de Control y Auditoría OCR")
    
    # Fila de botones de control superior
    col_scan, col_clear = st.columns([1, 1])
    
    with col_scan:
        if st.button("🔍 Escanear Carpeta de PDFs", use_container_width=True):
            with st.spinner("Ejecutando extractor automático 'core/extractor.py'..."):
                try:
                    # Llama a tu lector de guías reestructurado
                    subprocess.run(["python", "core/extractor.py"], check=True)
                    st.success("¡Escaneo completo!")
                except Exception as e:
                    st.error(f"Error al ejecutar el lector: {e}")
            st.rerun()

    ruta_pendientes = os.path.join("storage", "data", "pendientes_aprobacion.csv")
    
    # Si la sala de espera contiene datos generados por extractor.py
    if os.path.exists(ruta_pendientes):
        try:
            df_pendientes = pd.read_csv(ruta_pendientes)
        except Exception:
            df_pendientes = pd.DataFrame()
        
        if not df_pendientes.empty:
            st.warning("⚠️ Guías detectadas en sala de espera. Realiza doble clic sobre cualquier celda para corregirla antes de aprobar.")
            
            # st.data_editor convierte el lote en una tabla interactiva modificable
            df_editado = st.data_editor(
                df_pendientes, 
                num_rows="dynamic", 
                use_container_width=True,
                key="editor_guias_ocr"
            )
            
            col_save, col_reject = st.columns([1, 1])
            
            with col_save:
                if st.button("✅ Aprobar e Inyectar al Dashboard", type="primary", use_container_width=True):
                    ruta_oficial = os.path.join("storage", "data", "envios.csv")
                    df_historico = pd.read_csv(ruta_oficial) if os.path.exists(ruta_oficial) else pd.DataFrame()
                    
                    # Forzar limpiezas rápidas sobre el lote editado por el humano
                    if 'origen' in df_editado.columns:
                        df_editado['origen'] = df_editado['origen'].astype(str).str.strip().str.upper()
                    if 'destino' in df_editado.columns:
                        df_editado['destino'] = df_editado['destino'].astype(str).str.strip().str.upper()
                    if 'fuente' not in df_editado.columns:
                        df_editado['fuente'] = 'PDF_Digitalizado'
                    else:
                        df_editado['fuente'] = df_editado['fuente'].fillna('PDF_Digitalizado')
                    
                    # Unificación limpia del nuevo lote aprobado con tu histórico oficial
                    df_final = pd.concat([df_historico, df_editado], ignore_index=True)
                    df_final.to_csv(ruta_oficial, index=False)
                    
                    # Limpiar el archivo temporal de pendientes
                    os.remove(ruta_pendientes)
                    
                    # Archivar los archivos PDFs reales para dejar limpia la carpeta de entrada
                    carpeta_procesados = os.path.join("storage", "archive_pdfs")
                    if not os.path.exists(carpeta_procesados):
                        os.makedirs(carpeta_procesados)
                        
                    input_path = os.path.join("storage", "pdfs_pendientes")
                    if os.path.exists(input_path):
                        for archivo in os.listdir(input_path):
                            if archivo.lower().endswith(".pdf"):
                                try:
                                    shutil.move(
                                        os.path.join(input_path, archivo),
                                        os.path.join(carpeta_procesados, archivo)
                                    )
                                except Exception:
                                    pass # Evita caídas si el archivo está bloqueado
                                
                    st.success("¡Base de datos unificada con éxito! El Dashboard se actualizará automáticamente.")
                    st.rerun()
                    
            with col_reject:
                if st.button("🗑️ Descartar y Limpiar Lote Actual", type="secondary", use_container_width=True):
                    if os.path.exists(ruta_pendientes):
                        os.remove(ruta_pendientes)
                    st.info("Bandeja temporal vaciada sin alterar los reportes históricos.")
                    st.rerun()
        else:
            st.info("No hay guías nuevas en la bandeja de revisión.")
    else:
        st.info("No hay guías nuevas en la bandeja de revisión. Agrega PDFs en 'storage/pdfs_pendientes' y presiona Escanear.")
        
    st.divider()
