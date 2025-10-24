import math
import pickle

def calcular_distancia_haversine(coord1, coord2):
    """
    Calcula distância em metros entre duas coordenadas usando fórmula de Haversine
    DISTÂNCIA EM LINHA RETA - não considera vias/estradas
    """
    if not coord1 or not coord2:
        return float('inf')
    
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # Raio da Terra em metros
    R = 6371000
    
    # Converte para radianos
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    # Fórmula de Haversine (distância em linha reta)
    a = (math.sin(delta_phi / 2) ** 2 + 
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distancia_metros = R * c
    return distancia_metros

def salvar_grafo(grafo, caminho_arquivo='grafo.pkl'):
    """Salva o grafo em um arquivo usando pickle."""
    try:
        with open(caminho_arquivo, 'wb') as f:
            pickle.dump(grafo, f)
        print(f"💾 Grafo salvo em: {caminho_arquivo}")
    except Exception as e:
        print(f"❌ Erro ao salvar grafo: {e}")

def carregar_grafo(caminho_arquivo='grafo.pkl'):
    """Carrega o grafo de um arquivo usando pickle."""
    try:
        with open(caminho_arquivo, 'rb') as f:
            grafo = pickle.load(f)
        return grafo
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"❌ Erro ao carregar grafo: {e}")
        return None