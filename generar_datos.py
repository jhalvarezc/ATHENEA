# generar_datos.py - Simulador de Carga Masiva para ATHENEA
import pandas as pd
import random

def generar_dataset_corporativo(num_envios=2000):
    print(f"⚡ Iniciando la construcción de {num_envios} registros logísticos...")
    
    estados = ['en_transito', 'entregado', 'en_novedad']
    lista_guias = []
    
    # Inyectamos los 5 originales para mantener consistencia histórica
    lista_guias.extend([
        {"guia": "guia_1001", "estado": "en_transito", "limite_entrega": 20260608, "costo_flete": 25000},
        {"guia": "guia_1002", "estado": "entregado", "limite_entrega": 20260605, "costo_flete": 18000},
        {"guia": "guia_1003", "estado": "en_novedad", "limite_entrega": 20260601, "costo_flete": 32000},
        {"guia": "guia_1004", "estado": "en_transito", "limite_entrega": 20260605, "costo_flete": 21000},
        {"guia": "guia_1005", "estado": "en_novedad", "limite_entrega": 20260615, "costo_flete": 45000}
    ])
    
    # Bucle automatizado para poblar el Big Data restante
    for i in range(1006, 1006 + num_envios - 5):
        guia = f"guia_{i}"
        estado = random.choice(estados)
        
        dia = random.randint(1, 28)
        mes = random.choice([5, 6])
        limite = int(f"20260{mes}{dia:02d}")
        
        flete = random.randint(500, 5000)
        
        lista_guias.append({
            "guia": guia,
            "estado": estado,
            "limite_entrega": limite,
            "costo_flete": flete
        })
        
    df_gigante = pd.DataFrame(lista_guias)
    df_gigante.to_csv("envios.csv", index=False)
    print(f"✅ ¡Éxito! Archivo 'envios.csv' actualizado masivamente con {len(df_gigante)} registros.")

if __name__ == "__main__":
    generar_dataset_corporativo(num_envios=2000)