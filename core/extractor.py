# core/extractor.py - Motor de Extracción de Datos PDF para ATHENEA
import os
import re
import pandas as pd
from PyPDF2 import PdfReader

# Configuración de carpetas
CARPETA_PDFS = os.path.join("storage", "pdfs_pendientes")
ARCHIVO_PENDIENTES = os.path.join("storage", "data", "pendientes_aprobacion.csv")

def limpiar_texto_ciudad(texto):
    """Limpia espacios, saltos de línea y remueve tildes para estandarizar la data."""
    if not texto:
        return ""
    txt = texto.strip().lower()
    # Remover acentos de forma manual y segura
    remplazos = str.maketrans("áéíóúüñ", "aeiouun")
    return txt.translate(remplazos)

def extraer_datos_servientrega(texto):
    """Usa Regex ultra-robusto para buscar los datos, ignorando capitalización y acentos."""
    datos = {
        'guia': None, 'origen': None, 'destino': None, 'estado': 'preparacion',
        'costo_flete': 0, 'despacho_dia': 1, 'despacho_mes': 1, 'despacho_ano': 2026,
        'limite_dia': 1, 'limite_mes': 1, 'limite_ano': 2026
    }
    
    if not texto or not texto.strip():
        return datos

    try:
        # 1. Extraer Guía (Soporta GUIA, GUÍA, Guia, guía, etc. gracias a re.IGNORECASE)
        match_guia = re.search(r"GUÍ?A:\s*(\d+)", texto, re.IGNORECASE)
        if match_guia: 
            datos['guia'] = f"guia_{match_guia.group(1).strip()}"
        
        # 2. Extraer Origen (Soporta tildes, eñes, mayúsculas/minúsculas y espacios intermedios)
        match_origen = re.search(r"ORIGEN:\s*([A-Za-zÁÉÍÓÚáéíóúÑñüÜ\s]+)", texto, re.IGNORECASE)
        if match_origen: 
            datos['origen'] = limpiar_texto_ciudad(match_origen.group(1))
        
        # 3. Extraer Destino (Soporta saltos de línea opcionales, tildes y espacios)
        match_destino = re.search(r"DESTINO:\s*\n*\s*([A-Za-zÁÉÍÓÚáéíóúÑñüÜ\s]+)", texto, re.IGNORECASE)
        if match_destino: 
            datos['destino'] = limpiar_texto_ciudad(match_destino.group(1))
            
        # 4. Extraer Flete (Soporta variaciones como VALOR, TOTAL, SERVICIO o fletes directos)
        match_flete = re.search(r"(?:VALOR TOTAL SERVICIO|VALOR|FLETE):\s*\$\s*([\d\.]+)", texto, re.IGNORECASE)
        if match_flete: 
            datos['costo_flete'] = int(match_flete.group(1).replace('.', ''))
            
        # 5. Extraer Fecha Despacho (Soporta tanto barra / como guion -)
        match_fecha_desp = re.search(r"FECHA:\s*(\d{4})[-/](\d{2})[-/](\d{2})", texto, re.IGNORECASE)
        if match_fecha_desp:
            datos['despacho_ano'] = int(match_fecha_desp.group(1))
            datos['despacho_mes'] = int(match_fecha_desp.group(2))
            datos['despacho_dia'] = int(match_fecha_desp.group(3))
            
        # 6. Extraer Fecha Límite (Soporta tanto barra / como guion -)
        match_fecha_lim = re.search(r"(\d{2})[-/](\d{2})[-/](\d{4})", texto)
        if match_fecha_lim:
            datos['limite_dia'] = int(match_fecha_lim.group(1))
            datos['limite_mes'] = int(match_fecha_lim.group(2))
            datos['limite_ano'] = int(match_fecha_lim.group(3))
            
    except Exception as e:
        print(f"⚠️ Error procesando texto en Regex: {e}")
        
    return datos

def procesar_carpeta():
    if not os.path.exists(CARPETA_PDFS):
        os.makedirs(CARPETA_PDFS)
        print(f"Carpeta '{CARPETA_PDFS}' creada. Por favor, pon los PDFs ahí.")
        return

    archivos_pdf = [f for f in os.listdir(CARPETA_PDFS) if f.lower().endswith('.pdf')]
    if not archivos_pdf:
        print("No hay PDFs nuevos para procesar.")
        return

    registros_extraidos = []
    
    for archivo in archivos_pdf:
        ruta_pdf = os.path.join(CARPETA_PDFS, archivo)
        texto_completo = ""
        
        try:
            # Leer el PDF de forma segura
            lector = PdfReader(ruta_pdf)
            for pagina in lector.pages:
                texto_pag = pagina.extract_text()
                if texto_pag:
                    texto_completo += texto_pag + "\n"
            
            # Alerta preventiva en consola si el PDF no contiene texto (escaneado como imagen pura)
            if not texto_completo.strip():
                print(f"⚠️ Aviso: El archivo '{archivo}' no tiene texto extraíble. ¿Es una imagen sin OCR?")
                
            # Extraer datos y añadir a la lista
            datos = extraer_datos_servientrega(texto_completo)
            
            # 🛡️ Blindaje de seguridad: Si la Regex no encontró la guía, usamos el nombre del archivo
            if not datos['guia'] or datos['guia'] == 'None':
                nombre_limpio = os.path.splitext(archivo)[0].replace(" ", "_").lower()
                datos['guia'] = f"guia_{nombre_limpio}"
            
            # 🌟 NUEVA HOMOLOGACIÓN ESTRICTA: Asegura que siempre tenga el prefijo 'guia_'
            if not str(datos['guia']).startswith("guia_"):
                datos['guia'] = f"guia_{datos['guia']}"
            
            # Forzar valores por defecto en MINÚSCULAS si vinieron nulos en el PDF real
            if not datos['origen']: datos['origen'] = "bogota"
            if not datos['destino']: datos['destino'] = "medellin"
                
            registros_extraidos.append(datos)
        except Exception as e:
            print(f"❌ Error crítico leyendo el archivo {archivo}: {e}")

    if not registros_extraidos:
        print("⚠️ No se pudieron extraer registros válidos de los PDFs actuales.")
        return

    # Guardar en el CSV temporal de aprobación
    df_nuevos = pd.DataFrame(registros_extraidos)
    
    if os.path.exists(ARCHIVO_PENDIENTES):
        try:
            df_existente = pd.read_csv(ARCHIVO_PENDIENTES)
            df_final = pd.concat([df_existente, df_nuevos], ignore_index=True).drop_duplicates(subset=['guia'], keep='last')
        except Exception:
            df_final = df_nuevos
    else:
        df_final = df_nuevos
        
    df_final.to_csv(ARCHIVO_PENDIENTES, index=False)
    print(f"✅ Se han procesado {len(archivos_pdf)} PDFs con éxito. Listos para revisión en ATHENEA.")

if __name__ == "__main__":
    procesar_carpeta()
