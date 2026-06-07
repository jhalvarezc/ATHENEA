# main.py - Orquestador ATHENEA con Ingestión CSV
import csv
import sys
from pyswip import Prolog

def cargar_datos_y_auditar():
    prolog = Prolog()
    try:
        # 1. Consultar el cerebro (que ahora está vacío de datos, solo tiene reglas)
        prolog.consult("logic.pl")
        print("=======================================")
        print("🧠 [ATHENEA] Arquitectura Desacoplada")
        print("=======================================\n")

        # 2. Leer el archivo CSV e inyectar los datos en Prolog
        print("[*] Ingestando datos desde archivo CSV...")
        
        with open("envios.csv", mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                guia = row['guia']
                estado = row['estado']
                limite = int(row['limite_entrega'])
                costo = int(row['costo_flete'])
                
                # Inyección dinámica de conocimientos a Prolog
                prolog.assertz(f"estado_envio({guia}, {estado})")
                prolog.assertz(f"limite_entrega({guia}, {limite})")
                prolog.assertz(f"costo_flete({guia}, {costo})")

        print("[✅] Datos de operación ingestados en el motor lógico.\n")
        
        # 3. Ejecutar Razonamiento Múltiple
        fecha_hoy = 20260607
        
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
        print("[ERROR] No se encontró el archivo 'envios.csv'.")
    except Exception as e:
        print(f"[ERROR CRÍTICO] {e}")
        sys.exit(1)

if __name__ == "__main__":
    cargar_datos_y_auditar()