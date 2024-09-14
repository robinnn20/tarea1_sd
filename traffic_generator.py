import pandas as pd
import requests
import random
import time

# Leer el dataset
df = pd.read_csv("3rd_lev_domains.csv")

# Limitar el dataset a 50,000 consultas
limited_df = df.sample(n=50000, random_state=42)

# Lista para almacenar las consultas repetidas
repeat_domains = limited_df.sample(n=10000, random_state=42)['ascension.gov.ac'].tolist()

# Función para generar tráfico
def generate_traffic():
    for index, row in limited_df.iterrows():
        # Alternar entre una consulta única y una consulta repetida
        if random.random() > 0.5:
            domain = row['ascension.gov.ac']
        else:
            domain = random.choice(repeat_domains)

        # Hacer una solicitud a la API
        response = requests.post("http://localhost:8000/text", json={"text": domain})
        
        if response.status_code == 200:
            print(f"Consulta {index + 1}: {domain} almacenado en caché.")
        else:
            print(f"Error en consulta {index + 1}: {response.status_code}")
        
        # Introducir un pequeño delay para simular tráfico real
        time.sleep(0.1)

if _name_ == "_main_":
    generate_traffic()
