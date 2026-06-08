# modules/prolog_engine.py
import streamlit as st
from pyswip import Prolog

@st.cache_resource
def inicializar_base_conocimiento():
    """Instancia y consulta la base de conocimiento una única vez."""
    prolog = Prolog()
    try:
        prolog.consult("logic.pl")
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