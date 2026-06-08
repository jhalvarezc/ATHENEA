# ingestion/excel_parser.py - Importador y normalizador para archivos Excel
import pandas as pd
import datetime

def normalizar_ciudad(texto):
    if pd.isna(texto):
        return ""
    txt = str(texto).strip().lower()
    # Estandarizar texto
    remplazos = str.maketrans("áéíóúüñ", "aeiouun")
    return txt.translate(remplazos)

def parsear_excel(ruta_excel):
    """
    Lee un archivo Excel y normaliza sus filas al Contrato de Datos Estricto.
    """
    try:
        df = pd.read_excel(ruta_excel)
    except Exception as e:
        print(f"❌ Error leyendo Excel {ruta_excel}: {e}")
        return []
    
    # Estandarizar columnas a minúsculas
    df.columns = [str(col).strip().lower() for col in df.columns]
    
    registros_normalizados = []
    
    # Mapear nombres de columnas probables
    col_guia = next((c for c in df.columns if c in ['guia', 'guia_id', 'id', 'guía', 'guiaid', 'codigo']), None)
    col_origen = next((c for c in df.columns if c in ['origen', 'ciudad_origen', 'ciudad_orig', 'orig']), None)
    col_destino = next((c for c in df.columns if c in ['destino', 'ciudad_destino', 'ciudad_dest', 'dest']), None)
    col_costo = next((c for c in df.columns if c in ['costo_flete', 'flete', 'costo', 'valor', 'precio']), None)
    
    col_despacho = next((c for c in df.columns if c in ['fecha_despacho', 'despacho', 'fecha', 'fecha_envio']), None)
    col_limite = next((c for c in df.columns if c in ['fecha_limite', 'limite', 'limite_entrega', 'limite_fecha']), None)

    for idx, row in df.iterrows():
        d_dia, d_mes, d_ano = 1, 6, 2026
        l_dia, l_mes, l_ano = 1, 6, 2026
        
        # Procesar fecha despacho
        if col_despacho:
            val_despacho = row[col_despacho]
            try:
                dt_despacho = pd.to_datetime(val_despacho)
                if not pd.isna(dt_despacho):
                    d_dia, d_mes, d_ano = dt_despacho.day, dt_despacho.month, dt_despacho.year
            except Exception:
                pass
                
        # Procesar fecha límite
        if col_limite:
            val_limite = row[col_limite]
            try:
                dt_limite = pd.to_datetime(val_limite)
                if not pd.isna(dt_limite):
                    l_dia, l_mes, l_ano = dt_limite.day, dt_limite.month, dt_limite.year
            except Exception:
                pass

        # Generar código de guía normalizado
        g_id = ""
        if col_guia:
            val_guia = row[col_guia]
            if not pd.isna(val_guia):
                g_str = str(val_guia).strip()
                if g_str:
                    g_id = g_str if g_str.startswith("guia_") else f"guia_{g_str}"
        
        if not g_id:
            g_id = f"guia_excel_{idx}"
            
        costo_val = 0.0
        if col_costo:
            val_costo = row[col_costo]
            try:
                if not pd.isna(val_costo):
                    costo_val = float(val_costo)
            except Exception:
                pass

        registro = {
            'guia_id': g_id,
            'origen': normalizar_ciudad(row[col_origen]) if col_origen else "bogota",
            'destino': normalizar_ciudad(row[col_destino]) if col_destino else "medellin",
            'costo_flete': costo_val,
            'despacho_dia': d_dia, 'despacho_mes': d_mes, 'despacho_ano': d_ano,
            'limite_dia': l_dia, 'limite_mes': l_mes, 'limite_ano': l_ano,
            'estado_auditoria': 'pendiente'
        }
        registros_normalizados.append(registro)
        
    return registros_normalizados
