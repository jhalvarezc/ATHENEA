# storage/csv_manager.py - Gestor de persistencia CSV para ATHENEA
import pandas as pd
import os
from brain.prolog_driver import consultar_regla, prolog_instance, obtener_alertas_financieras, obtener_entregas_criticas
from ui.styles import normalizar_ciudad

def safe_to_int(val, default=0):
    """Convierte de forma segura cualquier valor a entero, manejando NaNs, Nones y formatos de punto flotante en texto."""
    try:
        num = pd.to_numeric(val, errors='coerce')
        if pd.isna(num):
            return default
        return int(num)
    except Exception:
        return default

def enriquecer_con_ia(df):
    """
    Toma el DataFrame de guías y le añade etiquetas inteligentes 
    basadas en las inferencias de las nuevas funciones del motor Prolog.
    """
    if df is None or df.empty:
        return df

    # Obtener listas de guías con alertas desde Prolog
    guias_sobrecosto = obtener_alertas_financieras()   # Devuelve ej: ['guia_1486', ...]
    guias_criticas = obtener_entregas_criticas()       # Devuelve ej: ['guia_1486', ...]

    # Limpiar y asegurar que sean strings sin espacios para un cruce perfecto
    guias_sobrecosto = [str(g).strip().lower() for g in guias_sobrecosto]
    guias_criticas = [str(g).strip().lower() for g in guias_criticas]

    # Crear las columnas inteligentes mapeando fila por fila de forma segura
    df['alerta_costo'] = df['guia'].astype(str).str.strip().str.lower().isin(guias_sobrecosto)
    df['prioridad_alta'] = df['guia'].astype(str).str.strip().str.lower().isin(guias_criticas)

    return df

def sincronizar_datos():
    """Limpia Prolog, carga el histórico y pendientes, los inyecta en Prolog y enriquece con IA."""
    consultar_regla("retractall(estado_envio(_,_))")
    consultar_regla("retractall(costo_flete(_,_))")
    consultar_regla("retractall(destino_envio(_,_))")
    consultar_regla("retractall(origen_envio(_,_))")
    consultar_regla("retractall(fecha_despacho(_,_))")
    consultar_regla("retractall(limite_entrega(_,_))")
    
    # 1. Cargar Histórico CSV
    try:
        df_historico = pd.read_csv("storage/data/envios.csv")
        df_historico['fuente'] = 'Data_Lake_CSV'
    except Exception:
        df_historico = pd.DataFrame()

    # 2. Cargar Pendientes de Aprobación
    ruta_pendientes = os.path.join("storage", "data", "pendientes_aprobacion.csv")
    df_pendientes = pd.DataFrame()
    if os.path.exists(ruta_pendientes):
        try:
            df_pendientes = pd.read_csv(ruta_pendientes)
            if not df_pendientes.empty:
                df_pendientes['fuente'] = 'Cargue_Operador_Excel'
        except Exception:
            pass

    # 3. Fusionar datos para inyección
    dfs = []
    if not df_historico.empty:
        dfs.append(df_historico)
    if not df_pendientes.empty:
        dfs.append(df_pendientes)

    if not dfs:
        return pd.DataFrame()

    df_unificado = pd.concat(dfs, ignore_index=True)

    # Función local para normalizar nombres de ciudades quitando tildes y espacios
    def limpiar_ciudad_texto(x):
        if pd.isna(x) or str(x).lower() == 'nan':
            return ""
        # Usar la función compartida, pero retornar en minúsculas para mantener consistencia aquí
        return normalizar_ciudad(x).lower()

    if 'origen' in df_unificado.columns:
        df_unificado['origen'] = df_unificado['origen'].apply(limpiar_ciudad_texto)
    if 'destino' in df_unificado.columns:
        df_unificado['destino'] = df_unificado['destino'].apply(limpiar_ciudad_texto)

    # 4. Mapeo e inyección en el Motor de Inferencia Prolog
    for _, row in df_unificado.iterrows():
        g = str(row['guia']).strip()
        e = str(row['estado']).strip()
        c = safe_to_int(row.get('costo_flete'), 0)
        o = str(row['origen']).strip()
        d = str(row['destino']).strip()
        
        d_dia = safe_to_int(row.get('despacho_dia'), 1)
        d_mes = safe_to_int(row.get('despacho_mes'), 1)
        d_ano = safe_to_int(row.get('despacho_ano'), 2026)
        
        l_dia = safe_to_int(row.get('limite_dia'), 1)
        l_mes = safe_to_int(row.get('limite_mes'), 1)
        l_ano = safe_to_int(row.get('limite_ano'), 2026)
        
        prolog_instance.assertz(f"estado_envio('{g}', {e})")
        prolog_instance.assertz(f"costo_flete('{g}', {c})")
        prolog_instance.assertz(f"origen_envio('{g}', '{o}')")
        prolog_instance.assertz(f"destino_envio('{g}', '{d}')")
        prolog_instance.assertz(f"fecha_despacho('{g}', fecha({d_dia}, {d_mes}, {d_ano}))")
        prolog_instance.assertz(f"limite_entrega('{g}', fecha({l_dia}, {l_mes}, {l_ano}))")
        
    # Enriquecer la data con las reglas antes de retornarla a app.py
    df_listo = enriquecer_con_ia(df_unificado)
    return df_listo

def obtener_datos_consolidados():
    """
    Sincroniza y enriquece todos los datos (históricos y pendientes) en el motor Prolog
    y los retorna en un solo DataFrame consolidado.
    """
    return sincronizar_datos()
