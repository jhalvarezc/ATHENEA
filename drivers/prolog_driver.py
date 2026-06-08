# drivers/prolog_driver.py - Motor de inferencia Prolog para ATHENEA
import streamlit as st
from pyswip import Prolog

@st.cache_resource
def inicializar_base_conocimiento():
    """Instancia y consulta la base de conocimiento una única vez."""
    prolog = Prolog()
    try:
        prolog.consult("core/logic.pl")
    except Exception:
        pass
    return prolog

prolog_instance = inicializar_base_conocimiento()

def consultar_regla(cadena_prolog):
    """Ejecuta consultas seguras devolviendo diccionarios de Python."""
    try: 
        return list(prolog_instance.query(cadena_prolog))
    except Exception: 
        return []

def obtener_alertas_financieras():
    """Consulta guías con fletes por encima del estándar."""
    res = consultar_regla("flete_alto(Guia, Costo)")
    return [r['Guia'].decode('utf-8') if isinstance(r['Guia'], bytes) else str(r['Guia']) for r in res]

def obtener_entregas_criticas():
    """Consulta guías que tienen un margen de entrega muy corto."""
    res = consultar_regla("entrega_urgente(Guia)")
    return [r['Guia'].decode('utf-8') if isinstance(r['Guia'], bytes) else str(r['Guia']) for r in res]
