import grpc
from concurrent import futures
import subprocess
import dns_service_pb2
import dns_service_pb2_grpc

class DNSResolverServicer(dns_service_pb2_grpc.DNSResolverServicer):
    def ResolveDomain(self, request, context):
        domain = request.domain
        print(f"Resolviendo dominio: {domain}")
        try:
            result = subprocess.run(['dig', '+trace', '+nodnssec', '+noall', '+answer', domain], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if result.returncode != 0:
                print(f"Error ejecutando DIG: {result.stderr.decode('utf-8')}")
                return dns_service_pb2.DomainResponse(ip_address="")
            
            output = result.stdout.decode('utf-8')
            print(f"Salida de DIG para {domain}: {output}")
            
            ip = self.extract_ip(output)
            
            if ip:
                print(f"IP extraída para {domain}: {ip}")
            else:
                print(f"No se pudo extraer una IP válida para {domain}")
            
            return dns_service_pb2.DomainResponse(ip_address=ip)
        
        except Exception as e:
            print(f"Excepción al ejecutar DIG para {domain}: {str(e)}")
            return dns_service_pb2.DomainResponse(ip_address="")
    def extract_ip(self, dig_output):
        for line in dig_output.splitlines():
            if line and not line.startswith(';'):
                parts = line.split()
                if len(parts) >= 5 and parts[3] == 'A':
                    return parts[4]
        return ""

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    dns_service_pb2_grpc.add_DNSResolverServicer_to_server(DNSResolverServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Servidor gRPC iniciado en el puerto 50051")
    server.wait_for_termination()

if _name_ == "_main_":
    serve()
