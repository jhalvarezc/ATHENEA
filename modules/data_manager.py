# modules/data_manager.py (Fragmento Corregido)
import pandas as pd
import os
from modules.prolog_engine import consultar_regla, prolog_instance

def cargar_guias_pdfs():
    """Lee las guías reales procesadas por tu lector de PDF guardadas en pendientes_aprobacion.csv."""
    ruta_pendientes = "pendientes_aprobacion.csv"
    
    # Si tu lector_guias.py ya generó el CSV, lo cargamos con su etiqueta correspondiente
    if os.path.exists(ruta_pendientes):
        try:
            df_p = pd.read_csv(ruta_pendientes)
            df_p['fuente'] = 'PDF_Digitalizado'
            return df_p
        except Exception:
            pass
            
    # Mock de seguridad en caso de que el archivo esté vacío o en uso
    datos_extraidos = [
        {
            "guia": "9160393764", "origen": "CARTAGENA", "destino": "CALI", 
            "estado": "en_revision_doc", "costo_flete": 38658, "fuente": "PDF_Digitalizado",
            "origen_latitude": 10.3910, "origen_longitude": -75.4794,
            "destino_latitude": 3.4516, "destino_longitude": -76.5320,
            "despacho_dia": 19, "despacho_mes": 3, "despacho_ano": 2026,
            "limite_dia": 23, "limite_mes": 3, "limite_ano": 2026
        }
    ]
    return pd.DataFrame(datos_extraidos)

# modules/data_manager.py
import pandas as pd
import os
from modules.prolog_engine import consultar_regla, prolog_instance

def cargar_guias_pdfs():
    """Lee las guías reales procesadas por tu lector de PDF guardadas en pendientes_aprobacion.csv."""
    ruta_pendientes = "pendientes_aprobacion.csv"
    
    if os.path.exists(ruta_pendientes):
        try:
            df_p = pd.read_csv(ruta_pendientes)
            df_p['fuente'] = 'PDF_Digitalizado'
            return df_p
        except Exception:
            pass
            
    # Fallback/Mock si el archivo de pendientes está vacío o bloqueado
    return pd.DataFrame()

def sincronizar_datos():
    """Limpia Prolog y unifica de forma segura fuentes CSV e histórico de PDFs."""
    consultar_regla("retractall(estado_envio(_,_))")
    consultar_regla("retractall(costo_flete(_,_))")
    consultar_regla("retractall(destino_envio(_,_))")
    consultar_regla("retractall(origen_envio(_,_))")
    consultar_regla("retractall(fecha_despacho(_,_))")
    consultar_regla("retractall(limite_entrega(_,_))")
    
    # 1. Cargar Histórico e inicializar la columna 'fuente' para evitar el KeyError
    try:
        df_csv = pd.read_csv("envios.csv")
        df_csv['fuente'] = 'Data_Lake_CSV'
    except Exception:
        df_csv = pd.DataFrame()
        
    # 2. Cargar datos extraídos de tus documentos PDF
    df_pdfs = cargar_guias_pdfs()
    
    # Unificación limpia de fuentes de datos
    if not df_csv.empty and not df_pdfs.empty:
        df_unificado = pd.concat([df_csv, df_pdfs], ignore_index=True)
    elif not df_csv.empty:
        df_unificado = df_csv
    else:
        df_unificado = df_pdfs

    if df_unificado.empty:
        return df_unificado

    # 3. Mapeo en el Motor de Inferencia Prolog
    for _, row in df_unificado.iterrows():
        g = str(row['guia']).strip()
        e = str(row['estado']).strip()
        c = int(row['costo_flete'])
        o = str(row['origen']).strip()
        d = str(row['destino']).strip()
        
        d_dia, d_mes, d_ano = int(row['despacho_dia']), int(row['despacho_mes']), int(row['despacho_ano'])
        l_dia, l_mes, l_ano = int(row['limite_dia']), int(row['limite_mes']), int(row['limite_ano'])
        
        prolog_instance.assertz(f"estado_envio('{g}', {e})")
        prolog_instance.assertz(f"costo_flete('{g}', {c})")
        prolog_instance.assertz(f"origen_envio('{g}', '{o}')")
        prolog_instance.assertz(f"destino_envio('{g}', '{d}')")
        prolog_instance.assertz(f"fecha_despacho('{g}', fecha({d_dia}, {d_mes}, {d_ano}))")
        prolog_instance.assertz(f"limite_entrega('{g}', fecha({l_dia}, {l_mes}, {l_ano}))")
        
    return df_unificado
    # 1. Cargar Histórico e inicializar la columna 'fuente' para evitar el KeyError
    try:
        df_csv = pd.read_csv("envios.csv")
        df_csv['fuente'] = 'Data_Lake_CSV'  # <-- ESTA LÍNEA ASEGURA QUE EXISTA LA COLUMNA
    except Exception:
        df_csv = pd.DataFrame()
        
    # 2. Cargar datos extraídos de tus documentos PDF
    df_pdfs = cargar_guias_pdfs()
    if 'fuente' not in df_pdfs.columns:
        df_pdfs['fuente'] = 'PDF_Digitalizado'
    
    # Unificación limpia de matrices
    if not df_csv.empty and not df_pdfs.empty:
        df_unificado = pd.concat([df_csv, df_pdfs], ignore_index=True)
    elif not df_csv.empty:
        df_unificado = df_csv
    else:
        df_unificado = df_pdfs

    if df_unificado.empty:
        return df_unificado

    # 3. Mapeo en el Motor de Inferencia Prolog
    for _, row in df_unificado.iterrows():
        g = str(row['guia']).strip()
        e = str(row['estado']).strip()
        c = int(row['costo_flete'])
        o = str(row['origen']).strip()
        d = str(row['destino']).strip()
        
        d_dia, d_mes, d_ano = int(row['despacho_dia']), int(row['despacho_mes']), int(row['despacho_ano'])
        l_dia, l_mes, l_ano = int(row['limite_dia']), int(row['limite_mes']), int(row['limite_ano'])
        
        prolog_instance.assertz(f"estado_envio('{g}', {e})")
        prolog_instance.assertz(f"costo_flete('{g}', {c})")
        prolog_instance.assertz(f"origen_envio('{g}', '{o}')")
        prolog_instance.assertz(f"destino_envio('{g}', '{d}')")
        prolog_instance.assertz(f"fecha_despacho('{g}', fecha({d_dia}, {d_mes}, {d_ano}))")
        prolog_instance.assertz(f"limite_entrega('{g}', fecha({l_dia}, {l_mes}, {l_ano}))")
        
    return df_unificado