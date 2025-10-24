from collections import defaultdict

def construir_grafo(paradas, linhas_de_onibus):
    """Constrói grafo inicial com todas as conexões possíveis via linhas em comum"""
    grafo = defaultdict(list)
    
    for parada in paradas:
        for linha in linhas_de_onibus[parada]:
            for vizinha in paradas:
                if linha in linhas_de_onibus[vizinha] and vizinha != parada:
                    grafo[parada].append((vizinha, linha))
    
    return grafo


def validar_conexao_direcional(parada_origem, parada_destino, linha, sequencias):
    """Verifica se a conexão é válida respeitando a direção da linha"""
    if linha not in sequencias:
        return False
    
    sequencia = sequencias[linha]
    
    try:
        idx_origem = sequencia.index(parada_origem)
        idx_destino = sequencia.index(parada_destino)
        return idx_destino > idx_origem
    except ValueError:
        return False


def aplicar_direcionalidade(grafo, sequencias):
    """Filtra o grafo mantendo apenas arestas válidas direcionalmente"""
    grafo_direcional = defaultdict(list)
    
    arestas_removidas = 0
    arestas_mantidas = 0
    
    for parada_origem, conexoes in grafo.items():
        for parada_destino, linha in conexoes:
            if validar_conexao_direcional(parada_origem, parada_destino, linha, sequencias):
                # Formato: (destino, tipo_conexao, identificador, custo)
                # Para ônibus: custo baseado em número de paradas (estimativa)
                grafo_direcional[parada_origem].append((parada_destino, 'onibus', linha, 10))
                arestas_mantidas += 1
            else:
                arestas_removidas += 1
    
    print(f"  Arestas de ônibus mantidas: {arestas_mantidas}")
    print(f"  Arestas de ônibus removidas: {arestas_removidas}")
    
    return grafo_direcional


def adicionar_conexoes_caminhada(grafo, paradas_proximas):
    """
    Adiciona conexões de caminhada ao grafo.
    
    Formato da aresta de caminhada:
    (parada_destino, 'caminhada', distancia_metros, custo)
    
    Custo de caminhada = distancia / 100 (cada 100m = 1 ponto de custo)
    Isso torna caminhada mais atrativa que pegar múltiplas linhas.
    """
    conexoes_adicionadas = 0
    
    for parada_origem, vizinhos in paradas_proximas.items():
        for parada_destino, distancia in vizinhos:
            # Custo proporcional à distância
            # Cada 100m de caminhada = 1 ponto
            # Isso é mais barato que pegar ônibus (custo 10) para distâncias curtas
            custo_caminhada = max(1, distancia / 100)
            
            # Adiciona conexão bidirecional de caminhada
            grafo[parada_origem].append((parada_destino, 'caminhada', f'{distancia}m', custo_caminhada))
            grafo[parada_destino].append((parada_origem, 'caminhada', f'{distancia}m', custo_caminhada))
            conexoes_adicionadas += 2
    
    print(f"  Conexões de caminhada adicionadas: {conexoes_adicionadas}")
    
    return grafo