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
        # Se não temos informação da sequência, não valida
        return False
    
    sequencia = sequencias[linha]
    
    try:
        idx_origem = sequencia.index(parada_origem)
        idx_destino = sequencia.index(parada_destino)
        
        # Válido apenas se destino vem DEPOIS da origem
        return idx_destino > idx_origem
        
    except ValueError:
        # Uma das paradas não está na sequência desta linha
        return False


def aplicar_direcionalidade(grafo, sequencias):
    """Filtra o grafo mantendo apenas arestas válidas direcionalmente"""
    grafo_direcional = defaultdict(list)
    
    arestas_removidas = 0
    arestas_mantidas = 0
    
    for parada_origem, conexoes in grafo.items():
        for parada_destino, linha in conexoes:
            if validar_conexao_direcional(parada_origem, parada_destino, linha, sequencias):
                grafo_direcional[parada_origem].append((parada_destino, linha))
                arestas_mantidas += 1
            else:
                arestas_removidas += 1
    
    print(f"  Arestas mantidas: {arestas_mantidas}")
    print(f"  Arestas removidas: {arestas_removidas}")
    
    return grafo_direcional