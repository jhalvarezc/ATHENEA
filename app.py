# app.py - Dashboard Interactivo de ATHENEA
import streamlit as st
import pandas as pd
from pyswip import Prolog

# 1. Configuración de la página web
st.set_page_config(page_title="ATHENEA Dashboard", page_icon="🧠", layout="wide")

st.title("🧠 ATHENEA - Centro de Inteligencia Logística")
st.markdown("Panel de control ejecutivo en tiempo real para auditoría de paquetería.")

# 2. Función para conectar Python y Prolog en la web
@st.cache_resource
def iniciar_motor():
    prolog = Prolog()
    prolog.consult("logic.pl")
    return prolog

prolog = iniciar_motor()

# 3. Ingestar datos desde CSV
def cargar_datos():
    # Limpiamos la memoria para evitar datos duplicados si se recarga la página
    list(prolog.query("retractall(estado_envio(_,_))"))
    list(prolog.query("retractall(limite_entrega(_,_))"))
    list(prolog.query("retractall(costo_flete(_,_))"))
    
    # Leemos el archivo con Pandas (ideal para web)
    df = pd.read_csv("envios.csv")
    for index, row in df.iterrows():
        g = row['guia']
        e = row['estado']
        l = int(row['limite_entrega'])
        c = int(row['costo_flete'])
        prolog.assertz(f"estado_envio({g}, {e})")
        prolog.assertz(f"limite_entrega({g}, {l})")
        prolog.assertz(f"costo_flete({g}, {c})")
    return df

datos_crudos = cargar_datos()

# 4. Deducciones Lógicas (El cerebro trabajando)
fecha_hoy = 20260607

# Extraemos los resultados y limpiamos el formato
retrasos = [res['Guia'].decode('utf-8') if isinstance(res['Guia'], bytes) else res['Guia'] for res in prolog.query(f"alerta_retraso(Guia, {fecha_hoy})")]
criticos = [res['Guia'].decode('utf-8') if isinstance(res['Guia'], bytes) else res['Guia'] for res in prolog.query("alerta_critica(Guia)")]

# 5. Diseño Visual del Dashboard
st.header("📊 Resumen Operativo")
col1, col2, col3 = st.columns(3)
col1.metric("Total Envíos Auditados", len(datos_crudos))
col2.metric("🚨 Alertas de Retraso", len(retrasos))
col3.metric("💥 Riesgos Financieros", len(criticos))

st.markdown("---")

# Dividimos la pantalla en dos columnas
colA, colB = st.columns(2)

with colA:
    st.subheader("⏱️ Envíos con Retraso")
    if retrasos:
        st.error(f"Se requiere intervención táctica en: {', '.join(retrasos)}")
        # Filtramos la tabla para mostrar solo los problemáticos
        st.dataframe(datos_crudos[datos_crudos['guia'].isin(retrasos)], use_container_width=True)
    else:
        st.success("Tiempos logísticos dentro de la norma.")

with colB:
    st.subheader("💸 Riesgos de Flete Crítico")
    if criticos:
        st.error(f"Fuga de capital detectada en: {', '.join(criticos)}")
        st.dataframe(datos_crudos[datos_crudos['guia'].isin(criticos)], use_container_width=True)
    else:
        st.success("No hay riesgos críticos financieros.")

st.sidebar.success("✅ ATHENEA Engine: Activo y sincronizado.")
st.sidebar.info("Arquitectura: Python + Prolog + Streamlit")