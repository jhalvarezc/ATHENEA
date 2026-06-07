# generar_datos.py - Simulador de Carga con Coordenadas Reales
import pandas as pd
import random

def generar_dataset_corporativo(num_envios=2000):
    print(f"⚡ Generando {num_envios} registros con coordenadas geográficas...")
    
    estados = ['en_transito', 'entregado', 'en_novedad']
    
    # Diccionario con coordenadas reales de las ciudades
    geo_ciudades = {
        'bogota': {'lat': 4.7110, 'lon': -74.0721},
        'medellin': {'lat': 6.2442, 'lon': -75.5812},
        'cali': {'lat': 3.4516, 'lon': -76.5320},
        'barranquilla': {'lat': 10.9685, 'lon': -74.7813},
        'bucaramanga': {'lat': 7.1254, 'lon': -73.1198},
        'cartagena': {'lat': 10.3910, 'lon': -75.4794}
    }
    
    lista_guias = []
    
    for i in range(1001, 1001 + num_envios):
        guia = f"guia_{i}"
        estado = random.choice(estados)
        destino = random.choice(list(geo_ciudades.keys()))
        
        dia = random.randint(1, 28)
        mes = random.choice([5, 6])
        limite = int(f"20260{mes}{dia:02d}")
        flete = random.randint(500, 5000)
        
        lista_guias.append({
            "guia": guia,
            "estado": estado,
            "limite_entrega": limite,
            "costo_flete": flete,
            "destino": destino,
            "latitude": geo_ciudades[destino]['lat'],  # Requerido por Streamlit
            "longitude": geo_ciudades[destino]['lon']  # Requerido por Streamlit
        })
        
    df_gigante = pd.DataFrame(lista_guias)
    df_gigante.to_csv("envios.csv", index=False)
    print(f"✅ Archivo 'envios.csv' actualizado con éxito.")

if __name__ == "__main__":
    generar_dataset_corporativo(num_envios=2000)