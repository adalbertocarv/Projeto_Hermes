import heapq

def heuristica(parada_atual, destino):
    """Função heurística simples (diferença entre IDs)"""
    return abs(parada_atual - destino)


def encontrar_caminho_com_integracao_astar(grafo, origem, destino):
    """Algoritmo A* para encontrar o caminho mais eficiente entre duas paradas"""
    fila = [(0, origem, [])]  # (custo_total, parada_atual, caminho)
    visitados = set()

    while fila:
        custo, parada_atual, caminho = heapq.heappop(fila)

        if parada_atual == destino:
            return caminho + [parada_atual]

        if parada_atual not in visitados:
            visitados.add(parada_atual)

            for vizinho, linha in grafo[parada_atual]:
                if vizinho not in visitados:
                    custo_estimado = custo + 1 + heuristica(vizinho, destino)
                    heapq.heappush(fila, (custo_estimado, vizinho, caminho + [parada_atual, linha]))

    return None