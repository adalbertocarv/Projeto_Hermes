import heapq

def heuristica(parada_atual, destino):
    """Heurística: diferença entre IDs (simplificada)"""
    return abs(parada_atual - destino) * 0.01


def encontrar_caminho_com_integracao_astar(grafo, origem, destino):
    """
    Algoritmo A* otimizado para priorizar caminhada quando vantajoso.
    
    Sistema de custos:
    - Caminhada: 1 ponto por 100m (muito barato)
    - Ônibus: 10 pontos por trecho
    - Troca de linha: +15 pontos (penalidade alta)
    
    Isso faz com que:
    1. Caminhadas curtas (até 200m) sejam preferidas
    2. Trocar de linha seja evitado quando possível
    3. Rotas diretas sejam priorizadas
    """
    
    # Fila: (custo_estimado, custo_real, parada_atual, tipo_transporte_atual, linha_atual, caminho)
    fila = [(0, 0, origem, None, None, [])]
    
    # Melhores custos: (parada, tipo_transporte, linha) -> custo
    melhores_custos = {}
    
    PENALIDADE_TROCA_LINHA = 15  # Custo alto para desincentivar trocas
    
    while fila:
        _, custo_real, parada_atual, tipo_atual, linha_atual, caminho = heapq.heappop(fila)
        
        # Chegou ao destino
        if parada_atual == destino:
            return caminho + [(parada_atual, tipo_atual, linha_atual)]
        
        # Chave de estado
        estado = (parada_atual, tipo_atual, linha_atual)
        
        # Poda: se já visitamos este estado com custo menor
        if estado in melhores_custos and melhores_custos[estado] <= custo_real:
            continue
        
        melhores_custos[estado] = custo_real
        
        # Explora vizinhos
        if parada_atual in grafo:
            for proxima_parada, tipo_transporte, identificador, custo_base in grafo[parada_atual]:
                
                # Calcula custo da transição
                custo_transicao = custo_base
                
                # Penalidade por trocar de linha de ônibus
                if tipo_atual == 'onibus' and tipo_transporte == 'onibus':
                    if linha_atual is not None and identificador != linha_atual:
                        custo_transicao += PENALIDADE_TROCA_LINHA
                
                # Bônus por continuar caminhando (incentiva completar caminhada)
                elif tipo_atual == 'caminhada' and tipo_transporte == 'caminhada':
                    custo_transicao *= 0.9  # 10% de desconto
                
                # Bônus por iniciar com caminhada (incentiva começar caminhando)
                elif tipo_atual is None and tipo_transporte == 'caminhada':
                    custo_transicao *= 0.8  # 20% de desconto
                
                novo_custo_real = custo_real + custo_transicao
                custo_estimado = novo_custo_real + heuristica(proxima_parada, destino)
                
                # Adiciona à fila
                novo_caminho = caminho + [(parada_atual, tipo_transporte, identificador)]
                heapq.heappush(fila, (
                    custo_estimado, 
                    novo_custo_real, 
                    proxima_parada, 
                    tipo_transporte,
                    identificador if tipo_transporte == 'onibus' else None,
                    novo_caminho
                ))
    
    return None

