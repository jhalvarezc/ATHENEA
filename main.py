# main.py - Orquestador ATHENEA con Ingestión CSV
import csv
import sys
from pyswip import Prolog

# Forzar codificación UTF-8 para consola
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def cargar_datos_y_auditar():
    prolog = Prolog()
    try:
        # 1. Consultar el cerebro (que ahora está vacío de datos, solo tiene reglas)
        prolog.consult("core/logic.pl")
        print("=======================================")
        print("🧠 [ATHENEA] Arquitectura Desacoplada")
        print("=======================================\n")

        # 2. Leer el archivo CSV e inyectar los datos en Prolog
        print("[*] Ingestando datos desde archivo CSV...")
        
        with open("storage/data/envios.csv", mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                g = row['guia'].strip()
                e = row['estado'].strip()
                c = int(row['costo_flete'])
                l_dia, l_mes, l_ano = int(row['limite_dia']), int(row['limite_mes']), int(row['limite_ano'])
                
                # Inyección dinámica de conocimientos a Prolog
                prolog.assertz(f"estado_envio('{g}', {e})")
                prolog.assertz(f"limite_entrega('{g}', fecha({l_dia}, {l_mes}, {l_ano}))")
                prolog.assertz(f"costo_flete('{g}', {c})")

        print("[✅] Datos de operación ingestados en el motor lógico.\n")
        
        # 3. Ejecutar Razonamiento Múltiple
        fecha_hoy = "fecha(7, 6, 2026)"
        
        # Auditoría 1: Los Retrasos
        print("[*] Analizando tiempos de entrega...")
        resultados_retrasos = list(prolog.query(f"alerta_retraso(Guia, {fecha_hoy})"))
        if resultados_retrasos:
            for res in resultados_retrasos:
                guia = res['Guia'].decode('utf-8') if isinstance(res['Guia'], bytes) else res['Guia']
                print(f" 🚨 [RETRASO] Envío {guia} superó el límite.")
        
        print("")
        
        # Auditoría 2: Alertas Críticas de Dinero
        print("[*] Analizando riesgos financieros...")
        resultados_criticos = list(prolog.query("alerta_critica(Guia)"))
        if resultados_criticos:
            for res in resultados_criticos:
                guia = res['Guia'].decode('utf-8') if isinstance(res['Guia'], bytes) else res['Guia']
                print(f" 💥 [RIESGO CRÍTICO] Envío {guia} en estado de NOVEDAD con flete de alto impacto.")

    except FileNotFoundError:
        print("[ERROR] No se encontró el archivo 'storage/data/envios.csv'.")
    except Exception as e:
        print(f"[ERROR CRÍTICO] {e}")
        sys.exit(1)

if __name__ == "__main__":
    cargar_datos_y_auditar()