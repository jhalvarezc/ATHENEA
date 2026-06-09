# brain/forecasting.py - Motor de Predicciones y Proyecciones Analíticas (Prolog + Python)
import pandas as pd
import numpy as np
import streamlit as st
from brain.prolog_driver import prolog_instance, prolog_lock, consultar_regla
from ui.styles import normalizar_ciudad

def predecir_operacion(df):
    """
    Toma el DataFrame de envíos actual, calcula agregados, inyecta hechos en Prolog
    y ejecuta reglas lógicas de predicción para costos, hubs y SLAs.
    """
    # 1. Validación de entrada
    if df is None or df.empty:
        return {
            'costos': {'proyectado': 0.0, 'categoria': 'Sin Datos', 'recomendacion': 'No hay datos cargados para realizar proyecciones.'},
            'hubs': [],
            'sla': {'tasa_fallo': 0.0, 'categoria': 'Sin Datos', 'recomendacion': 'Sin envíos críticos activos.'}
        }

    # Asegurar tipos de columnas correctos
    df_clean = df.copy()
    if 'costo_flete' in df_clean.columns:
        df_clean['costo_flete'] = pd.to_numeric(df_clean['costo_flete'], errors='coerce').fillna(0)
    else:
        df_clean['costo_flete'] = 0

    if 'estado' not in df_clean.columns:
        df_clean['estado'] = 'preparacion'

    if 'destino' not in df_clean.columns:
        df_clean['destino'] = 'desconocido'

    # 2. Inicialización de resultados (Estructura de Fallback por defecto)
    mes_actual = 6  # Simulación ATHENEA fija en Junio 2026 (mes 6)
    acumulado_flete = float(df_clean['costo_flete'].sum())
    total_envios = len(df_clean)
    
    # Fallback matemático en Python
    costo_proyectado_py = (acumulado_flete / mes_actual) * 12
    if costo_proyectado_py > 1500000:
        categoria_costos_py = 'Peligro (Sobrepresupuesto)'
        recom_costos_py = 'Alerta (Heurística): El costo anual proyectado supera los márgenes ideales. Renegociar tarifas.'
    elif costo_proyectado_py > 1000000:
        categoria_costos_py = 'Precaucion (Moderado)'
        recom_costos_py = 'Advertencia (Heurística): Monitorear costos de fletes.'
    else:
        categoria_costos_py = 'Seguro (Bajo Riesgo)'
        recom_costos_py = 'Normal (Heurística): Gasto anual proyectado dentro del presupuesto fiscal.'

    predicciones = {
        'costos': {
            'proyectado': costo_proyectado_py,
            'categoria': categoria_costos_py,
            'recomendacion': recom_costos_py
        },
        'hubs': [],
        'sla': {
            'tasa_fallo': 0.0,
            'categoria': 'SLA Cumplido',
            'recomendacion': 'Excelente: Las entregas críticas se encuentran estables.'
        },
        'max_hub': None
    }

    # 3. Inyección e Inferencia en Prolog (Dentro del candado multi-hilo)
    try:
        with prolog_lock:
            # A. Limpiar predicados anteriores
            list(prolog_instance.query("retractall(datos_fiscales(_, _, _))"))
            list(prolog_instance.query("retractall(estadisticas_hub(_, _, _))"))
            list(prolog_instance.query("retractall(estadisticas_sla(_, _))"))
            
            # B. Inyectar hechos fiscales
            prolog_instance.assertz(f"datos_fiscales({mes_actual}, {int(acumulado_flete)}, {total_envios})")
            
            # C. Inyectar estadísticas de Hubs
            destinos = df_clean['destino'].unique()
            for dest in destinos:
                ciudad_norm = normalizar_ciudad(dest).lower()
                df_dest = df_clean[df_clean['destino'] == dest]
                total_dest = len(df_dest)
                nov_dest = len(df_dest[df_dest['estado'] == 'en_novedad'])
                prolog_instance.assertz(f"estadisticas_hub('{ciudad_norm}', {nov_dest}, {total_dest})")
                
            # D. Inyectar estadísticas de SLA
            # Se consideran críticos los envíos marcados con prioridad_alta
            urgentes_col = 'prioridad_alta' if 'prioridad_alta' in df_clean.columns else None
            if urgentes_col:
                df_urgentes = df_clean[df_clean[urgentes_col] == True]
                total_urgentes = len(df_urgentes)
                retrasados_urgentes = len(df_urgentes[df_urgentes['estado'] != 'entregado'])
            else:
                total_urgentes = 0
                retrasados_urgentes = 0
                
            prolog_instance.assertz(f"estadisticas_sla({retrasados_urgentes}, {total_urgentes})")

            # E. Consultar Proyección Fiscal en Prolog
            res_fiscal = list(prolog_instance.query("prediccion_costo_anual(CostoProj, Cat, Rec)"))
            if res_fiscal:
                sol = res_fiscal[0]
                # Decodificar bytes si PySwip los retorna
                cat_val = sol['Cat'].decode('utf-8') if isinstance(sol['Cat'], bytes) else str(sol['Cat'])
                rec_val = sol['Rec'].decode('utf-8') if isinstance(sol['Rec'], bytes) else str(sol['Rec'])
                predicciones['costos'] = {
                    'proyectado': float(sol['CostoProj']),
                    'categoria': cat_val,
                    'recomendacion': rec_val
                }

            # F. Consultar Predicción de SLA en Prolog
            res_sla = list(prolog_instance.query("prediccion_sla(Tasa, Cat, Rec)"))
            if res_sla:
                sol = res_sla[0]
                cat_val = sol['Cat'].decode('utf-8') if isinstance(sol['Cat'], bytes) else str(sol['Cat'])
                rec_val = sol['Rec'].decode('utf-8') if isinstance(sol['Rec'], bytes) else str(sol['Rec'])
                predicciones['sla'] = {
                    'tasa_fallo': float(sol['Tasa']),
                    'categoria': cat_val,
                    'recomendacion': rec_val
                }

            # G. Consultar Predicción de Hubs en Prolog
            res_hubs = list(prolog_instance.query("prediccion_embotellamiento(Ciudad, TasaNov, NivelRiesgo, Rec)"))
            hubs_predicciones = []
            for r in res_hubs:
                ciudad_val = r['Ciudad'].decode('utf-8') if isinstance(r['Ciudad'], bytes) else str(r['Ciudad'])
                nivel_val = r['NivelRiesgo'].decode('utf-8') if isinstance(r['NivelRiesgo'], bytes) else str(r['NivelRiesgo'])
                rec_val = r['Rec'].decode('utf-8') if isinstance(r['Rec'], bytes) else str(r['Rec'])
                hubs_predicciones.append({
                    'ciudad': ciudad_val.upper(),
                    'tasa_novedades': float(r['TasaNov']),
                    'nivel_riesgo': nivel_val,
                    'recomendacion': rec_val
                })
            # Ordenar por nivel de riesgo / tasa novedades descendente
            predicciones['hubs'] = sorted(hubs_predicciones, key=lambda x: x['tasa_novedades'], reverse=True)

            # H. Consultar Punto de Mayor Cuello de Botella en Prolog
            res_max_hub = list(prolog_instance.query("mayor_cuello_botella(Ciudad, TasaMax, Rec)"))
            if res_max_hub:
                sol_max = res_max_hub[0]
                ciudad_val = sol_max['Ciudad'].decode('utf-8') if isinstance(sol_max['Ciudad'], bytes) else str(sol_max['Ciudad'])
                rec_val = sol_max['Rec'].decode('utf-8') if isinstance(sol_max['Rec'], bytes) else str(sol_max['Rec'])
                predicciones['max_hub'] = {
                    'ciudad': ciudad_val.upper(),
                    'tasa_novedades': float(sol_max['TasaMax']),
                    'recomendacion': rec_val
                }

            # I. Limpiar hechos temporales tras la inferencia
            list(prolog_instance.query("retractall(datos_fiscales(_, _, _))"))
            list(prolog_instance.query("retractall(estadisticas_hub(_, _, _))"))
            list(prolog_instance.query("retractall(estadisticas_sla(_, _))"))

    except Exception as e:
        # Si Prolog falla, completamos los Hubs con un cálculo heurístico básico en Python
        # para asegurar la total resiliencia del Dashboard
        hubs_py = []
        destinos = df_clean['destino'].unique()
        for dest in destinos:
            ciudad_norm = normalizar_ciudad(dest)
            df_dest = df_clean[df_clean['destino'] == dest]
            total_dest = len(df_dest)
            nov_dest = len(df_dest[df_dest['estado'] == 'en_novedad'])
            tasa = (nov_dest / total_dest) * 100 if total_dest > 0 else 0.0
            
            if tasa > 30:
                riesgo = 'Alto Riesgo'
                rec = 'Heurística: Desviar despachos y auditar Hub debido a novedades críticas.'
            elif tasa > 15:
                riesgo = 'Riesgo Moderado'
                rec = 'Heurística: Revisar tiempos operativos del Hub.'
            else:
                riesgo = 'Operación Estable'
                rec = 'Heurística: Hub operando con normalidad.'
                
            hubs_py.append({
                'ciudad': ciudad_norm,
                'tasa_novedades': tasa,
                'nivel_riesgo': riesgo,
                'recomendacion': rec
            })
        predicciones['hubs'] = sorted(hubs_py, key=lambda x: x['tasa_novedades'], reverse=True)
        
        # Fallback en Python para max_hub
        if hubs_py:
            max_item = max(hubs_py, key=lambda x: x['tasa_novedades'])
            if max_item['tasa_novedades'] > 0:
                predicciones['max_hub'] = {
                    'ciudad': max_item['ciudad'].upper(),
                    'tasa_novedades': max_item['tasa_novedades'],
                    'recomendacion': f"PUNTO CRITICO DE CUELLO DE BOTELLA (Heurística): El Hub {max_item['ciudad'].upper()} tiene la mayor tasa de novedades de la red ({max_item['tasa_novedades']:.1f}%)."
                }

    return predicciones
