# app.py - Dashboard Ejecutivo ATHENEA con Analítica Financiera y Gráficos Visuales
import streamlit as st
import pandas as pd
from pyswip import Prolog

# 1. Configuración de la interfaz visual
st.set_page_config(page_title="ATHENEA Dashboard", page_icon="🧠", layout="wide")

st.title("🧠 ATHENEA - Centro de Inteligencia Logística")
st.markdown("Panel de control ejecutivo en tiempo real para auditoría de paquetería.")

# 2. Control seguro del ciclo de vida del motor de Prolog
@st.cache_resource
def inicializar_base_conocimiento():
    prolog = Prolog()
    prolog.consult("logic.pl")
    return prolog

prolog = inicializar_base_conocimiento()

def consultar_regla(cadena_prolog):
    try:
        return list(prolog.query(cadena_prolog))
    except Exception:
        return []

# 3. Ingestión y Sincronización de Datos Dinámicos
def sincronizar_datos():
    consultar_regla("retractall(estado_envio(_,_))")
    consultar_regla("retractall(limite_entrega(_,_))")
    consultar_regla("retractall(costo_flete(_,_))")
    
    df = pd.read_csv("envios.csv")
    for _, row in df.iterrows():
        g = str(row['guia']).strip()
        e = str(row['estado']).strip()
        l = int(row['limite_entrega'])
        c = int(row['costo_flete'])
        
        prolog.assertz(f"estado_envio({g}, {e})")
        prolog.assertz(f"limite_entrega({g}, {l})")
        prolog.assertz(f"costo_flete({g}, {c})")
    return df

try:
    datos_crudos = sincronizar_datos()
    fecha_hoy = 20260607
    
    # --- Extracción de Deducciones desde Prolog ---
    res_retrasos = consultar_regla(f"alerta_retraso(Guia, {fecha_hoy})")
    retrasos = [r['Guia'].decode('utf-8') if isinstance(r['Guia'], bytes) else r['Guia'] for r in res_retrasos]
    
    res_criticos = consultar_regla("alerta_critica(Guia)")
    criticos = [r['Guia'].decode('utf-8') if isinstance(r['Guia'], bytes) else r['Guia'] for r in res_criticos]

    res_rutas = consultar_regla("alerta_ruta_critica(Guia)")
    rutas_criticas = [r['Guia'].decode('utf-8') if isinstance(r['Guia'], bytes) else r['Guia'] for r in res_rutas]

    res_tarifas = consultar_regla("alerta_tarifa_excesiva(Guia)")
    tarifas_excesivas = [r['Guia'].decode('utf-8') if isinstance(r['Guia'], bytes) else r['Guia'] for r in res_tarifas]

    # ==========================================================
    # PANEL DE FILTROS (SIDEBAR)
    # ==========================================================
    st.sidebar.header("🔍 Panel de Filtros")
    busqueda_guia = st.sidebar.text_input("Buscar código de guía:", "").strip()
    
    estados_disponibles = datos_crudos['estado'].unique().tolist()
    estados_seleccionados = st.sidebar.multiselect("Filtrar por Estado:", estados_disponibles, default=estados_disponibles)
    
    flete_maximo = int(datos_crudos['costo_flete'].max())
    flete_minimo_filtro = st.sidebar.slider("Filtrar fletes mayores a ($):", 0, flete_maximo, 0)

    # Filtrado dinámico principal
    datos_filtrados = datos_crudos[
        (datos_crudos['estado'].isin(estados_seleccionados)) &
        (datos_crudos['costo_flete'] >= flete_minimo_filtro)
    ]
    if busqueda_guia:
        datos_filtrados = datos_filtrados[datos_filtrados['guia'].str.contains(busqueda_guia, case=False)]

    # ==========================================================
    # OPCIÓN A: CÁLCULO DE FUGAS ECONÓMICAS Y RIESGOS TOTALES
    # ==========================================================
    # Calculamos el costo sumado de los fletes que están bajo alertas financieras (datos filtrados actuales)
    total_fuga_criticos = datos_filtrados[datos_filtrados['guia'].isin(criticos)]['costo_flete'].sum()
    total_fuga_tarifas = datos_filtrados[datos_filtrados['guia'].isin(tarifas_excesivas)]['costo_flete'].sum()
    riesgo_financiero_total = total_fuga_criticos + total_fuga_tarifas

    # ==========================================================
    # 4. Despliegue de KPIs Globales Expandidos
    # ==========================================================
    st.header("📊 Resumen de la Red de Distribución")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Auditado (Registros)", f"{len(datos_filtrados):,}")
    kpi2.metric("🚨 Alertas de Retraso", len(datos_filtrados[datos_filtrados['guia'].isin(retrasos)]))
    kpi3.metric("🎯 Rutas Críticas Activas", len(datos_filtrados[datos_filtrados['guia'].isin(rutas_criticas)]))
    kpi4.metric("💰 Capital en Riesgo Crítico", f"${riesgo_financiero_total:,} USD")

    st.markdown("---")

    # ==========================================================
    # OPCIÓN C: CAPA VISUAL - GRÁFICOS DE TRAZABILIDAD
    # ==========================================================
    st.subheader("📈 Analítica Visual de Trazabilidad")
    graf_col1, graf_col2 = st.columns(2)

    with graf_col1:
        st.markdown("**Distribución Operativa por Estado Actual**")
        # Conteo de guías por estado
        conteo_estados = datos_filtrados['estado'].value_counts()
        if not conteo_estados.empty:
            st.bar_chart(conteo_estados)
        else:
            st.info("Sin datos para mostrar gráfico de estados.")

    with graf_col2:
        st.markdown("**Volumen de Costos de Flete Agrupados por Estado**")
        # Suma de costos financieros acumulados por estado
        costos_por_estado = datos_filtrados.groupby('estado')['costo_flete'].sum()
        if not costos_por_estado.empty:
            st.line_chart(costos_por_estado)
        else:
            st.info("Sin datos para mostrar gráfico de costos.")

    st.markdown("---")

    # ==========================================================
    # 5. Matrices de Alerta Operativas (2x2)
    # ==========================================================
    fila1_colA, fila1_colB = st.columns(2)
    
    with fila1_colA:
        st.subheader("⏱️ Análisis de Latencia (Retrasos)")
        retrasos_vista = datos_filtrados[datos_filtrados['guia'].isin(retrasos)]
        if not retrasos_vista.empty:
            st.error(f"Intervención táctica requerida en {len(retrasos_vista)} guías.")
            st.dataframe(retrasos_vista, use_container_width=True)
        else:
            st.success("Tiempos logísticos estables.")

    with fila1_colB:
        st.subheader("💸 Riesgos de Flete Crítico")
        criticos_vista = datos_filtrados[datos_filtrados['guia'].isin(criticos)]
        if not criticos_vista.empty:
            st.error(f"Fuga detectada en {len(criticos_vista)} guías (Total: ${criticos_vista['costo_flete'].sum():,} USD).")
            st.dataframe(criticos_vista, use_container_width=True)
        else:
            st.success("Sin anomalías de alto valor financiero.")

    st.markdown("---")
    
    fila2_colA, fila2_colB = st.columns(2)
    
    with fila2_colA:
        st.subheader("🎯 Monitoreo de Rutas Críticas (Regla C)")
        rutas_vista = datos_filtrados[datos_filtrados['guia'].isin(rutas_criticas)]
        if not rutas_vista.empty:
            st.warning(f"Prioridad Máxima asignada a {len(rutas_vista)} despachos.")
            st.dataframe(rutas_vista, use_container_width=True)
        else:
            st.success("No hay rutas críticas activas.")

    with fila2_colB:
        st.subheader("📈 Auditoría de Tarifas Excesivas (Regla D)")
        tarifas_vista = datos_filtrados[datos_filtrados['guia'].isin(tarifas_excesivas)]
        if not tarifas_vista.empty:
            st.warning(f"Sobreprecio en tránsito detectado en {len(tarifas_vista)} guías.")
            st.dataframe(tarifas_vista, use_container_width=True)
        else:
            st.success("Tarifas de distribución bajo presupuesto.")

    # Tabla General abajo
    st.markdown("---")
    st.subheader("📋 Base de Datos Completa de Trazabilidad")
    st.dataframe(datos_filtrados, use_container_width=True)

except Exception as e:
    st.error(f"Error en la carga dinámica del Dashboard: {e}")

st.sidebar.markdown("---")
st.sidebar.success("✅ ATHENEA Engine: Activo")