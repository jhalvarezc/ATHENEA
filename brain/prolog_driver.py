# brain/prolog_driver.py - Conexión PySwip para ATHENEA
import os
import threading
from pyswip import Prolog

# Determinar la ruta absoluta de logic.pl
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_LOGIC_PL = os.path.join(BASE_DIR, "logic.pl").replace("\\", "/")

prolog_instance = Prolog()
prolog_lock = threading.Lock() # Candado para evitar colisiones multi-hilo

try:
    prolog_instance.consult(PATH_LOGIC_PL)
except Exception as e:
    print(f"⚠️ Error cargando logic.pl: {e}")

def consultar_regla(cadena_prolog):
    """Ejecuta una consulta Prolog genérica y devuelve los resultados."""
    try:
        return list(prolog_instance.query(cadena_prolog))
    except Exception as e:
        print(f"⚠️ Error ejecutando regla Prolog '{cadena_prolog}': {e}")
        return []

def auditar_envio(datos):
    """
    Registra temporalmente el envío en Prolog, evalúa su estado de alerta
    y retorna 'riesgo_financiero', 'alerta_retraso' o 'aprobado'.
    Los datos de entrada siguen el Contrato de Datos Estricto (con guia_id).
    """
    with prolog_lock: # Aseguramos thread-safety para PySwip
        g = str(datos.get('guia_id')).replace("'", "").strip()
        e = str(datos.get('estado', 'preparacion')).replace("'", "").strip()
        c = int(datos.get('costo_flete', 0))
        o = str(datos.get('origen', 'bogota')).replace("'", "").strip().lower()
        d = str(datos.get('destino', 'medellin')).replace("'", "").strip().lower()
        
        d_dia = int(datos.get('despacho_dia', 1))
        d_mes = int(datos.get('despacho_mes', 1))
        d_ano = int(datos.get('despacho_ano', 2026))
        
        l_dia = int(datos.get('limite_dia', 1))
        l_mes = int(datos.get('limite_mes', 1))
        l_ano = int(datos.get('limite_ano', 2026))

        try:
            # Inyectar hechos
            prolog_instance.assertz(f"estado_envio('{g}', {e})")
            prolog_instance.assertz(f"costo_flete('{g}', {c})")
            prolog_instance.assertz(f"origen_envio('{g}', '{o}')")
            prolog_instance.assertz(f"destino_envio('{g}', '{d}')")
            prolog_instance.assertz(f"fecha_despacho('{g}', fecha({d_dia}, {d_mes}, {d_ano}))")
            prolog_instance.assertz(f"limite_entrega('{g}', fecha({l_dia}, {l_mes}, {l_ano}))")

            # 1. Riesgo Financiero
            r_critico = consultar_regla(f"alerta_critica('{g}')")
            r_perdida = consultar_regla(f"alerta_riesgo_perdida_total('{g}')")
            r_fraude = consultar_regla(f"flete_sospechoso('{g}')")
            if r_critico or r_perdida or r_fraude:
                return "riesgo_financiero"
            
            # 2. Retraso (Fecha Simulación: 7 de Junio de 2026)
            retraso = consultar_regla(f"alerta_retraso('{g}', fecha(7, 6, 2026))")
            if retraso:
                return "alerta_retraso"

            return "aprobado"
            
        finally:
            # Retractar para limpiar
            consultar_regla(f"retractall(estado_envio('{g}', _))")
            consultar_regla(f"retractall(costo_flete('{g}', _))")
            consultar_regla(f"retractall(origen_envio('{g}', _))")
            consultar_regla(f"retractall(destino_envio('{g}', _))")
            consultar_regla(f"retractall(fecha_despacho('{g}', _))")
            consultar_regla(f"retractall(limite_entrega('{g}', _))")
