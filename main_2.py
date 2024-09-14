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
    print(f"Valor obtenido de Redis para {key}: {value}")  # Depuración
    return value

# Función para resolver dominios usando gRPC
def resolve_domain_with_grpc(domain): # Configurar el cliente gRPC
    channel = grpc.insecure_channel('localhost:50051')
    stub = dns_service_pb2_grpc.DNSResolverStub(channel)
    
    # Hacer la solicitud de resolución de dominio
    response = stub.ResolveDomain(dns_service_pb2.DomainRequest(domain=domain))
    
    # Añadir impresión para depurar
    print(f"Resolviendo dominio {domain}, IP obtenida: {response.ip_address}")
    
    # Si no se encuentra una IP válida, devolver None
    if response.ip_address:
        return response.ip_address
    return None

# Endpoint POST para almacenar texto en Redis
@app.post('/text')
def add_text(text_model: TextModel):
    add_text_to_redis(text_model.text, text_model.text)
    return {"stored_value": get_text_from_redis(text_model.text)}

# Endpoint GET para obtener texto de Redis o resolver vía gRPC
@app.get('/text/{text}')
def get_text(text: str):
    # Intentar recuperar el valor del caché
    value = get_text_from_redis(text)
    
    # Añadir impresión para depurar
    print(f"Buscando {text} en caché. Resultado: {value}")
    
    if value:  # Si se encuentra en caché
        print(f"Valor encontrado en caché para {text}")
        return {"retrieved_value": value}
    # Llamar al gRPC si no está en caché
    ip = resolve_domain_with_grpc(text)
    if ip:  # Si se resuelve correctamente
        print(f"Dominio {text} resuelto con IP: {ip}")
        add_text_to_redis(text, ip)  # Almacenar en caché
        return {"retrieved_value": ip}
    
    # Si no se pudo resolver el dominio
    print(f"No se pudo resolver el dominio {text}")
    return {"error": "No se pudo resolver el dominio"
