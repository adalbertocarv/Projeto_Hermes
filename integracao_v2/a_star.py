import heapq
from utils import calcular_distancia_haversine

def heuristica(parada_atual, destino, coordenadas_paradas):
    """
    Função heurística baseada em distância geográfica
    """
    if (parada_atual in coordenadas_paradas and 
        destino in coordenadas_paradas):
        distancia = calcular_distancia_haversine(
            coordenadas_paradas[parada_atual], 
            coordenadas_paradas[destino]
        )
        return distancia / 1000
    else:
        return abs(parada_atual - destino) * 0.1

def encontrar_caminho_com_caminhadas(grafo, coordenadas_paradas, origem, destino, raio_caminhada=400):
    """
    Função A* que PRIORIZA caminhadas quando possível
    """
    # PRIMEIRO: Verifica se pode ir A PÉ DIRETAMENTE da origem ao destino
    if (origem in coordenadas_paradas and 
        destino in coordenadas_paradas):
        
        distancia_direta = calcular_distancia_haversine(
            coordenadas_paradas[origem], 
            coordenadas_paradas[destino]
        )
        
        # Se está dentro do raio de caminhada, VAI A PÉ DIRETAMENTE
        if distancia_direta <= raio_caminhada:
            return [origem, f"🚶‍♂️{int(distancia_direta)}m", destino]

    # SEGUNDO: Se não pode ir a pé diretamente, usa A* normal
    fila = [(0, origem, [], None)]  # (custo, parada, caminho, linha_anterior)
    visitados = set()
    melhores_custos = {origem: 0}

    while fila:
        custo, parada_atual, caminho, linha_anterior = heapq.heappop(fila)

        if parada_atual == destino:
            return caminho + [parada_atual]

        if parada_atual in visitados:
            continue
            
        visitados.add(parada_atual)

        # 1. Expansão por ônibus
        if parada_atual in grafo:
            for vizinho, linha in grafo[parada_atual]:
                if vizinho in visitados:
                    continue
                
                custo_movimento = calcular_custo_onibus(linha_anterior, linha)
                novo_custo = custo + custo_movimento
                custo_estimado = novo_custo + heuristica(vizinho, destino, coordenadas_paradas)
                
                if vizinho not in melhores_custos or novo_custo < melhores_custos[vizinho]:
                    melhores_custos[vizinho] = novo_custo
                    
                    if linha_anterior is None or linha != linha_anterior:
                        novo_caminho = caminho + [parada_atual, linha]
                    else:
                        novo_caminho = caminho
                    
                    heapq.heappush(fila, (custo_estimado, vizinho, novo_caminho, linha))

        # 2. Caminhada para paradas próximas (apenas se vantajoso)
        if parada_atual in coordenadas_paradas:
            for outra_parada in coordenadas_paradas:
                if (outra_parada == parada_atual or 
                    outra_parada in visitados or 
                    outra_parada not in grafo):
                    continue
                
                distancia = calcular_distancia_haversine(
                    coordenadas_paradas[parada_atual], 
                    coordenadas_paradas[outra_parada]
                )
                
                # Caminhada para paradas próximas
                if distancia <= raio_caminhada:
                    custo_caminhada = calcular_custo_caminhada(distancia)
                    novo_custo = custo + custo_caminhada
                    custo_estimado = novo_custo + heuristica(outra_parada, destino, coordenadas_paradas)
                    
                    if outra_parada not in melhores_custos or novo_custo < melhores_custos[outra_parada]:
                        melhores_custos[outra_parada] = novo_custo
                        novo_caminho = caminho + [parada_atual, f"🚶‍♂️{int(distancia)}m", outra_parada]
                        heapq.heappush(fila, (custo_estimado, outra_parada, novo_caminho, None))

    return None

def calcular_custo_onibus(linha_anterior, linha_atual):
    """
    Calcula custo do movimento de ônibus
    """
    custo = 2  # Custo base do ônibus
    
    if linha_anterior is not None and linha_atual != linha_anterior:
        custo += 3
    
    if linha_anterior == linha_atual:
        custo -= 0.5
        
    return max(1, custo)

def calcular_custo_caminhada(distancia_metros):
    """
    Calcula custo da caminhada - MUITO BAIXO para incentivar caminhadas
    """
    return distancia_metros / 50  # 50m ≈ custo 1 (MUITO vantajoso)

def encontrar_linha_mais_direta(grafo, sequencias, origem, destino):
    """
    Encontra a linha que faz o caminho mais direto entre origem e destino
    """
    if origem not in grafo:
        return None, float('inf')
    
    melhor_linha = None
    menor_distancia = float('inf')
    
    for vizinho, linha in grafo[origem]:
        if linha not in sequencias:
            continue
            
        sequencia = sequencias[linha]
        
        if origem in sequencia and destino in sequencia:
            idx_origem = sequencia.index(origem)
            idx_destino = sequencia.index(destino)
            
            if idx_destino > idx_origem:
                distancia = idx_destino - idx_origem
                if distancia < menor_distancia:
                    menor_distancia = distancia
                    melhor_linha = linha
    
    return melhor_linha, menor_distancia

def formatar_caminho(caminho):
    """
    Formata o caminho encontrado de maneira legível
    """
    if not caminho:
        return "Nenhum caminho encontrado"
    
    resultado = []
    total_caminhada = 0
    total_trechos_onibus = 0
    total_trechos_pe = 0

    i = 0
    while i < len(caminho):
        # Último elemento (chegada)
        if i == len(caminho) - 1:
            if isinstance(caminho[i], int):
                resultado.append(f"🎯 Chegada: Parada {caminho[i]}")
            break
        
        parada_atual = caminho[i]
        
        # Próximo elemento é meio de transporte
        if i + 1 < len(caminho) and isinstance(caminho[i + 1], str):
            meio = caminho[i + 1]
            
            # Próxima parada existe
            if i + 2 < len(caminho) and isinstance(caminho[i + 2], int):
                prox_parada = caminho[i + 2]
                
                if meio.startswith("🚶‍♂️"):
                    # Trecho a pé
                    distancia = meio.replace("🚶‍♂️", "").replace("m", "")
                    resultado.append(f"📍 Parada {parada_atual} → 🚶‍♂️ Caminhar {distancia}m → 📍 Parada {prox_parada}")
                    total_caminhada += int(distancia)
                    total_trechos_pe += 1
                    i += 3
                else:
                    # Trecho de ônibus
                    linha = meio
                    resultado.append(f"📍 Parada {parada_atual} → 🚌 {linha} → 📍 Parada {prox_parada}")
                    total_trechos_onibus += 1
                    i += 2
            else:
                i += 1
        else:
            i += 1
    
    # Estatísticas
    resultado.append("\n📊 RESUMO DA ROTA:")
    
    if total_caminhada > 0:
        resultado.append(f"   🚶‍♂️ Caminhada total: {total_caminhada}m")
    
    if total_trechos_onibus > 0:
        resultado.append(f"   🚌 Trechos de ônibus: {total_trechos_onibus}")
    
    if total_trechos_pe > 0:
        resultado.append(f"   👣 Trechos a pé: {total_trechos_pe}")
    
    # Conta trocas de linha
    trocas = contar_trocas_linha(caminho)
    if trocas > 0:
        resultado.append(f"   🔄 Trocas de linha: {trocas}")
    
    return "\n".join(resultado)

def contar_trocas_linha(caminho):
    """
    Conta quantas vezes o usuário precisa trocar de linha de ônibus
    """
    trocas = 0
    linha_anterior = None
    
    for elemento in caminho:
        if isinstance(elemento, str) and not elemento.startswith("🚶‍♂️"):
            if linha_anterior is not None and elemento != linha_anterior:
                trocas += 1
            linha_anterior = elemento
    
    return trocas

# Função de compatibilidade
def encontrar_caminho_com_integracao_astar(grafo, origem, destino):
    """
    Função original mantida para compatibilidade
    """
    return encontrar_caminho_com_caminhadas(grafo, {}, origem, destino)