# storage/csv_manager.py - Gestor de persistencia CSV para ATHENEA
import pandas as pd
import os
from brain.prolog_driver import consultar_regla, prolog_instance, obtener_alertas_financieras, obtener_entregas_criticas

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
    """Limpia Prolog, carga SOLO el histórico oficial y enriquece con IA."""
    consultar_regla("retractall(estado_envio(_,_))")
    consultar_regla("retractall(costo_flete(_,_))")
    consultar_regla("retractall(destino_envio(_,_))")
    consultar_regla("retractall(origen_envio(_,_))")
    consultar_regla("retractall(fecha_despacho(_,_))")
    consultar_regla("retractall(limite_entrega(_,_))")
    
    # Cargar SOLO Histórico CSV (Lo aprobado)
    try:
        df_unificado = pd.read_csv("storage/data/envios.csv")
        df_unificado['fuente'] = 'Data_Lake_CSV'
    except Exception:
        return pd.DataFrame() # Si no hay data, devolvemos vacío inmediatamente

    if df_unificado.empty:
        return df_unificado

    # 3. Mapeo e inyección en el Motor de Inferencia Prolog
    for _, row in df_unificado.iterrows():
        g = str(row['guia']).strip()
        e = str(row['estado']).strip()
        c = int(row['costo_flete'])
        o = str(row['origen']).strip().lower()
        d = str(row['destino']).strip().lower()
        
        d_dia, d_mes, d_ano = int(row['despacho_dia']), int(row['despacho_mes']), int(row['despacho_ano'])
        l_dia, l_mes, l_ano = int(row['limite_dia']), int(row['limite_mes']), int(row['limite_ano'])
        
        prolog_instance.assertz(f"estado_envio('{g}', {e})")
        prolog_instance.assertz(f"costo_flete('{g}', {c})")
        prolog_instance.assertz(f"origen_envio('{g}', '{o}')")
        prolog_instance.assertz(f"destino_envio('{g}', '{d}')")
        prolog_instance.assertz(f"fecha_despacho('{g}', fecha({d_dia}, {d_mes}, {d_ano}))")
        prolog_instance.assertz(f"limite_entrega('{g}', fecha({l_dia}, {l_mes}, {l_ano}))")
        
    # 4. Enriquecer la data con las reglas antes de retornarla a app.py
    df_listo = enriquecer_con_ia(df_unificado)
    return df_listo

def obtener_datos_consolidados():
    """
    Sincroniza el histórico oficial, lee la cola de pendientes de aprobación si existe,
    y fusiona ambos en un solo DataFrame consolidado.
    """
    # 1. Obtener histórico enriquecido con IA
    df_historico = sincronizar_datos()
    
    # 2. Leer pendientes de aprobación
    ruta_pendientes = os.path.join("storage", "data", "pendientes_aprobacion.csv")
    df_pendientes = pd.DataFrame()
    if os.path.exists(ruta_pendientes):
        try:
            df_pendientes = pd.read_csv(ruta_pendientes)
            if not df_pendientes.empty:
                df_pendientes['fuente'] = 'Cargue_Operador_Excel'
        except Exception:
            pass
            
    # 3. Fusionar datos
    dfs_to_concat = []
    if df_historico is not None and not df_historico.empty:
        dfs_to_concat.append(df_historico)
    if not df_pendientes.empty:
        dfs_to_concat.append(df_pendientes)
        
    if dfs_to_concat:
        df_consolidado = pd.concat(dfs_to_concat, ignore_index=True)
    else:
        df_consolidado = pd.DataFrame()
        
    return df_consolidado
