# generar_datos.py - Generador de Data Lake Inteligente para ATHENEA
import pandas as pd
import random

# 1. Configuración Geográfica de Nodos Logísticos (Colombia)
ciudades_hub = {
    'bogota': {'lat': 4.7110, 'lon': -74.0721},
    'medellin': {'lat': 6.2442, 'lon': -75.5812},
    'cali': {'lat': 3.4516, 'lon': -76.5320},
    'barranquilla': {'lat': 10.9685, 'lon': -74.7813},
    'bucaramanga': {'lat': 7.1254, 'lon': -73.1198},
    'cartagena': {'lat': 10.3910, 'lon': -75.4794},
    'pereira': {'lat': 4.8133, 'lon': -75.6961}
}

estados_validos = ['en_bodega', 'preparacion', 'en_transito', 'en_novedad', 'entregado']

# Nota: Nuestra simulación se sitúa en la fecha actual de auditoría: 7 de Junio de 2026
# Es decir: fecha(7, 6, 2026) en Prolog.

registros = []

# ==========================================================
# 2. INYECCIÓN DE CASOS CRÍTICOS CONTROLADOS (Para Auditoría)
# ==========================================================

# Caso A: Retraso por Despacho (Atrapado en origen)
# Debería haber salido el 4 de Junio, sigue en bodega al 7 de Junio.
registros.append({
    'guia': 'guia_101_despacho', 'origen': 'bogota', 'destino': 'medellin',
    'estado': 'en_bodega', 'costo_flete': 1200,
    'despacho_dia': 4, 'despacho_mes': 6, 'despacho_ano': 2026,
    'limite_dia': 10, 'limite_mes': 6, 'limite_ano': 2026
})

# Caso B: Retraso por Transporte / Carretera
# Sigue en tránsito pero su fecha límite de entrega era el 5 de Junio (Ya expiró)
registros.append({
    'guia': 'guia_102_transporte', 'origen': 'cali', 'destino': 'barranquilla',
    'estado': 'en_transito', 'costo_flete': 2100,
    'despacho_dia': 1, 'despacho_mes': 6, 'despacho_ano': 2026,
    'limite_dia': 5, 'limite_mes': 6, 'limite_ano': 2026
})

# Caso C: Alerta Crítica Nivel 1 (Riesgo Financiero Extremo)
# Tiene novedad y un costo astronómico (> $30,000 USD)
registros.append({
    'guia': 'guia_103_critica', 'origen': 'bogota', 'destino': 'cartagena',
    'estado': 'en_novedad', 'costo_flete': 32000,
    'despacho_dia': 2, 'despacho_mes': 6, 'despacho_ano': 2026,
    'limite_dia': 9, 'limite_mes': 6, 'limite_ano': 2026
})

# Caso D: Flete Sospechoso / Posible Fraude Interno
# Está en novedad y costó más de $4,500 USD sin justificación aparente
registros.append({
    'guia': 'guia_104_fraude', 'origen': 'medellin', 'destino': 'bucaramanga',
    'estado': 'en_novedad', 'costo_flete': 5500,
    'despacho_dia': 3, 'despacho_mes': 6, 'despacho_ano': 2026,
    'limite_dia': 8, 'limite_mes': 6, 'limite_ano': 2026
})

# Caso E: Envío Estrella (Operación Eficiente y Económica)
# Ya fue entregado a tiempo y costó menos de $1,500 USD
registros.append({
    'guia': 'guia_105_estrella', 'origen': 'pereira', 'destino': 'bogota',
    'estado': 'entregado', 'costo_flete': 950,
    'despacho_dia': 4, 'despacho_mes': 6, 'despacho_ano': 2026,
    'limite_dia': 8, 'limite_mes': 6, 'limite_ano': 2026
})

# ==========================================================
# 3. GENERACIÓN DE VOLUMEN MASIVO (995 Envíos Aleatorios)
# ==========================================================
for i in range(106, 600):
    # Selección de nodos asegurando que Origen != Destino
    orig = random.choice(list(ciudades_hub.keys()))
    dest = random.choice([c for c in ciudades_hub.keys() if c != orig])
    
    est = random.choice(estados_validos)
    flete = random.randint(500, 4800) # Rango estándar corporativo
    
    # Generar fechas coherentes en torno a Junio de 2026
    d_dia = random.randint(1, 6)
    l_dia = random.randint(8, 15)
    
    registros.append({
        'guia': f'guia_{i}',
        'origen': orig,
        'destino': dest,
        'estado': est,
        'costo_flete': flete,
        'despacho_dia': d_dia,
        'despacho_mes': 6,
        'despacho_ano': 2026,
        'limite_dia': l_dia,
        'limite_mes': 6,
        'limite_ano': 2026
    })

# ==========================================================
# 4. MAPEADO AUTOMÁTICO DE COORDENADAS Y EXPORTACIÓN
# ==========================================================
df = pd.DataFrame(registros)

# Inyectamos las coordenadas reales correspondientes a los nombres de las ciudades
df['origen_latitude'] = df['origen'].map(lambda x: ciudades_hub[x]['lat'])
df['origen_longitude'] = df['origen'].map(lambda x: ciudades_hub[x]['lon'])
df['destino_latitude'] = df['destino'].map(lambda x: ciudades_hub[x]['lat'])
df['destino_longitude'] = df['destino'].map(lambda x: ciudades_hub[x]['lon'])

# Guardar la base de datos master
df.to_csv('envios.csv', index=False)
print(f"📦 ¡Data Lake generado con éxito! Se han creado {len(df)} registros en 'envios.csv'.")