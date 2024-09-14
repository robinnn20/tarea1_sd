from fastapi import FastAPI
from pydantic import BaseModel
import redis
import grpc
import dns_service_pb2
import dns_service_pb2_grpc

app = FastAPI()

class TextModel(BaseModel):
    text: str

# Configuración de los nodos Redis
redis_clients = [
    redis.Redis(host='redis-node-1', port=6379, password='yourpassword', decode_responses=True),
    redis.Redis(host='redis-node-2', port=6379, password='yourpassword', decode_responses=True),
]

# Variables globales para contar hits y misses
hit_count = 0
miss_count = 0

def get_redis_client(key: str):
    index = hash(key) % len(redis_clients)
    return redis_clients[index]

# Función para agregar un valor a Redis
def add_text_to_redis(key: str, value: str):
    client = get_redis_client(key)
    client.set(key, value)

# Función para recuperar un valor de Redis
def get_text_from_redis(key: str):
    client = get_redis_client(key)
    value = client.get(key)
    return value
# Función para resolver dominios usando gRPC
def resolve_domain_with_grpc(domain):
    # Usa el nombre del servicio gRPC en la red Docker en lugar de localhost
    channel = grpc.insecure_channel('grpc-server:50051')  # Cambiar localhost a grpc-server
    stub = dns_service_pb2_grpc.DNSResolverStub(channel)
    
    # Realiza la solicitud gRPC
    response = stub.ResolveDomain(dns_service_pb2.DomainRequest(domain=domain))
    
    return response.ip_address

# Endpoint POST para almacenar texto en Redis
@app.post('/text')
def add_text(text_model: TextModel):
    add_text_to_redis(text_model.text, text_model.text)
    return {"stored_value": get_text_from_redis(text_model.text)}

# Endpoint GET para obtener texto de Redis o resolver vía gRPC
@app.get('/text/{text}')
def get_text(text: str):
    global hit_count, miss_count
    value = get_text_from_redis(text)
    
    if value:
        hit_count += 1  # Aumentar el contador de hits
        print(f"HIT: Valor encontrado en caché para {text}")
        return {"retrieved_value": value, "hit": True}
# Si no está en caché, intentar resolver vía gRPC (MISS)
    ip = resolve_domain_with_grpc(text)
    if ip:
        miss_count += 1  # Aumentar el contador de misses
        print(f"MISS: Dominio {text} resuelto con IP {ip}. Almacenando en caché.")
        add_text_to_redis(text, ip)
        return {"retrieved_value": ip, "hit": False}
    
    return {"error": "No se pudo resolver el dominio"}

# Endpoint para obtener las estadísticas de hits y misses
@app.get('/stats')
def get_stats():
    return {"hit_count": hit_count, "miss_count": miss_count}
