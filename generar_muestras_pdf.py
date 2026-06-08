# generar_muestras_pdf.py - Fábrica de Facturas PDF de Prueba para ATHENEA
import os
import random
from datetime import datetime, timedelta
from fpdf import FPDF

# 1. Configuración de la carpeta destino
CARPETA_PDFS = "pdfs_pendientes"
if not os.path.exists(CARPETA_PDFS):
    os.makedirs(CARPETA_PDFS)

# 2. Ciudades admitidas por los HUBs geográficos de tu ATHENEA
ciudades = ["bogota", "medellin", "cali", "barranquilla", "bucaramanga", "cartagena", "pereira"]

def generar_factura_falsa():
    pdf = FPDF()
    pdf.add_page()
    # Usamos Helvetica que viene integrada por defecto y no requiere archivos externos
    pdf.set_font("Helvetica", size=10) 
    
    # --- GENERACIÓN DE DATOS ALEATORIOS COHERENTES ---
    guia_num = random.randint(9100000000, 9199999999)
    origen = random.choice(ciudades).upper()
    # Evitar que el destino sea el mismo origen
    destino = random.choice([c for c in ciudades if c.upper() != origen]).upper()
    
    flete_valor = random.randint(25000, 95000)
    flete_formateado = f"{flete_valor:,}".replace(",", ".")
    
    # Fechas simuladas para el entorno temporal de simulación del sistema
    fecha_despacho = datetime(2026, random.randint(1, 5), random.randint(1, 28))
    fecha_limite = fecha_despacho + timedelta(days=random.randint(2, 6))
    
    str_fecha_despacho = fecha_despacho.strftime("%Y/%m/%d")
    str_fecha_limite = fecha_limite.strftime("%d-%m-%Y")
    
    # --- EMULACIÓN DEL TEXTO EXACTO DE LA FACTURA ORIGINAL ---
    pdf.cell(200, 5, "SERVIENTREGA S.A. NIT. 860.512.330-3", ln=1)
    pdf.cell(200, 5, "Principal: Bogotá D.C., Colombia", ln=1)
    pdf.cell(200, 5, "Av Calle 6 No 34 A 11.", ln=1)
    pdf.cell(200, 5, "Somos Grandes Contribuyentes.", ln=1)
    pdf.cell(200, 5, "--------------------------------------------------------------------------------", ln=1)
    
    pdf.cell(200, 5, f"FACTURA ELECTRÓNICA DE VENTA No.: E743{random.randint(100000, 999999)}", ln=1)
    pdf.cell(200, 5, f"FECHA: {str_fecha_despacho}", ln=1)
    pdf.cell(200, 5, f"HORA: {random.randint(10,18)}:{random.randint(10,59)}:{random.randint(10,59)}", ln=1)
    pdf.cell(200, 5, "--------------------------------------------------------------------------------", ln=1)
    
    pdf.cell(200, 5, "INFORMACIÓN DEL SERVICIO", ln=1)
    pdf.cell(200, 5, "CLIENTE: SIMULACIÓN LOGÍSTICA ENTERPRISE", ln=1)
    pdf.cell(200, 5, f"ORIGEN: {origen}/GENERIC_DEPT", ln=1)
    pdf.cell(200, 5, f"SERVICIO (1): GUÍA: {guia_num}", ln=1)
    pdf.cell(200, 5, "RÉGIMEN:", ln=1)
    pdf.cell(200, 5, f"{str_fecha_limite}", ln=1) # Estructura exacta de salto de línea para la fecha límite
    pdf.cell(200, 5, "TRANSPORTE DE CARGA", ln=1)
    
    pdf.cell(200, 5, "DESTINATARIO: PUNTOS DE ENTREGA ATHENEA SAS", ln=1)
    pdf.cell(200, 5, "DESTINO:", ln=1)
    pdf.cell(200, 5, f"{destino}/GENERIC_DEPT", ln=1) # Estructura exacta de salto de línea para el destino
    pdf.cell(200, 5, "--------------------------------------------------------------------------------", ln=1)
    
    pdf.cell(200, 5, f"VALOR TOTAL SERVICIO: $ {flete_formateado}", ln=1)
    pdf.cell(200, 5, "VALOR A RECAUDAR EN DESTINO: $0", ln=1)
    
    # Guardar en la carpeta de pendientes con el número de guía como nombre
    nombre_archivo = os.path.join(CARPETA_PDFS, f"FACT_{guia_num}_MOCK.pdf")
    pdf.output(nombre_archivo)
    print(f"📄 PDF Autogenerado: {nombre_archivo}")

if __name__ == "__main__":
    # Cambia este número si deseas generar más o menos muestras a la vez
    CANTIDAD_MUESTRAS = 10 
    
    print(f"⚙️ Iniciando la fábrica de muestras... Creando {CANTIDAD_MUESTRAS} PDFs.")
    for _ in range(CANTIDAD_MUESTRAS):
        generar_factura_falsa()
    print("✨ ¡Proceso terminado! Revisa tu carpeta 'pdfs_pendientes'.")