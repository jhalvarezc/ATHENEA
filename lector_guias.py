# lector_guias.py - Motor de Extracción de Datos PDF para ATHENEA
import os
import re
import pandas as pd
from PyPDF2 import PdfReader

# Configuración de carpetas
CARPETA_PDFS = "pdfs_pendientes"
ARCHIVO_PENDIENTES = "pendientes_aprobacion.csv"

def extraer_datos_servientrega(texto):
    """Usa Regex para buscar los datos exactos en el texto del PDF"""
    datos = {
        'guia': None, 'origen': None, 'destino': None, 'estado': 'preparacion',
        'costo_flete': None, 'despacho_dia': None, 'despacho_mes': None, 'despacho_ano': None,
        'limite_dia': None, 'limite_mes': None, 'limite_ano': None
    }
    
    try:
        # Extraer Guía
        match_guia = re.search(r"GUÍA:\s*(\d+)", texto)
        if match_guia: datos['guia'] = f"guia_{match_guia.group(1)}"
        
        # Extraer Origen (Ej: ORIGEN: MEDELLIN/ANTIOQUIA)
        match_origen = re.search(r"ORIGEN:\s*([A-Z]+)", texto)
        if match_origen: datos['origen'] = match_origen.group(1).lower()
        
        # Extraer Destino (Ej: DESTINO: \n BARRANQUILLA)
        match_destino = re.search(r"DESTINO:\s*\n*\s*([A-Z]+)", texto)
        if match_destino: datos['destino'] = match_destino.group(1).lower()
        
        # Extraer Flete (Ej: VALOR TOTAL SERVICIO: $ 43.000)
        match_flete = re.search(r"VALOR TOTAL SERVICIO:\s*\$\s*([\d\.]+)", texto)
        if match_flete: 
            datos['costo_flete'] = int(match_flete.group(1).replace('.', ''))
            
        # Extraer Fecha Despacho (Ej: FECHA: 2026/04/30)
        match_fecha_desp = re.search(r"FECHA:\s*(\d{4})/(\d{2})/(\d{2})", texto)
        if match_fecha_desp:
            datos['despacho_ano'] = int(match_fecha_desp.group(1))
            datos['despacho_mes'] = int(match_fecha_desp.group(2))
            datos['despacho_dia'] = int(match_fecha_desp.group(3))
            
        # Extraer Fecha Límite (Ej: 04-05-2026 debajo de RÉGIMEN o PROG.ENTREGA)
        match_fecha_lim = re.search(r"(\d{2})-(\d{2})-(\d{4})", texto)
        if match_fecha_lim:
            datos['limite_dia'] = int(match_fecha_lim.group(1))
            datos['limite_mes'] = int(match_fecha_lim.group(2))
            datos['limite_ano'] = int(match_fecha_lim.group(3))
            
    except Exception as e:
        print(f"Error procesando texto: {e}")
        
    return datos

def procesar_carpeta():
    if not os.path.exists(CARPETA_PDFS):
        os.makedirs(CARPETA_PDFS)
        print(f"Carpeta '{CARPETA_PDFS}' creada. Por favor, pon los PDFs ahí.")
        return

    archivos_pdf = [f for f in os.listdir(CARPETA_PDFS) if f.endswith('.pdf')]
    if not archivos_pdf:
        print("No hay PDFs nuevos para procesar.")
        return

    registros_extraidos = []
    
    for archivo in archivos_pdf:
        ruta_pdf = os.path.join(CARPETA_PDFS, archivo)
        texto_completo = ""
        
        # Leer el PDF
        lector = PdfReader(ruta_pdf)
        for pagina in lector.pages:
            texto_completo += pagina.extract_text() + "\n"
            
        # Extraer datos y añadir a la lista
        datos = extraer_datos_servientrega(texto_completo)
        registros_extraidos.append(datos)
        
        # Mover o eliminar el PDF procesado (Opcional, aquí solo lo dejamos)
        # os.remove(ruta_pdf) 

    # Guardar en el CSV temporal de aprobación
    df_nuevos = pd.DataFrame(registros_extraidos)
    
    if os.path.exists(ARCHIVO_PENDIENTES):
        df_existente = pd.read_csv(ARCHIVO_PENDIENTES)
        df_final = pd.concat([df_existente, df_nuevos], ignore_index=True).drop_duplicates(subset=['guia'])
    else:
        df_final = df_nuevos
        
    df_final.to_csv(ARCHIVO_PENDIENTES, index=False)
    print(f"✅ Se han procesado {len(archivos_pdf)} PDFs. Listos para revisión en ATHENEA.")

if __name__ == "__main__":
    procesar_carpeta()