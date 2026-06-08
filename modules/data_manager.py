# modules/data_manager.py
import pandas as pd
from modules.prolog_engine import consultar_regla, prolog_instance

def sincronizar_datos():
    """Limpia Prolog e inyecta los datos vigentes del Data Lake csv."""
    consultar_regla("retractall(estado_envio(_,_))")
    consultar_regla("retractall(costo_flete(_,_))")
    consultar_regla("retractall(destino_envio(_,_))")
    consultar_regla("retractall(origen_envio(_,_))")
    consultar_regla("retractall(fecha_despacho(_,_))")
    consultar_regla("retractall(limite_entrega(_,_))")
    
    try:
        df = pd.read_csv("envios.csv")
    except Exception:
        return pd.DataFrame()

    for _, row in df.iterrows():
        g = str(row['guia']).strip()
        e = str(row['estado']).strip()
        c = int(row['costo_flete']) # Cambiado de 'flete' a 'costo_flete'
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
        
    return df