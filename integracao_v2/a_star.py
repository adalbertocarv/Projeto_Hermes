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

def encontrar_multiplos_caminhos(grafo, coordenadas_paradas, origem, destino, raio_caminhada=400, max_caminhos=5):
    """
    Função A* que encontra múltiplos caminhos ordenados por eficiência
    """
    # PRIMEIRO: Verifica se pode ir A PÉ DIRETAMENTE da origem ao destino
    caminhos_diretos = []
    if (origem in coordenadas_paradas and 
        destino in coordenadas_paradas):
        
        distancia_direta = calcular_distancia_haversine(
            coordenadas_paradas[origem], 
            coordenadas_paradas[destino]
        )
        
        # Se está dentro do raio de caminhada, VAI A PÉ DIRETAMENTE
        if distancia_direta <= raio_caminhada:
            caminho_direto = [origem, f"🚶‍♂️{int(distancia_direta)}m", destino]
            caminhos_diretos.append((calcular_custo_total_caminho(caminho_direto), caminho_direto))

    # SEGUNDO: Busca múltiplos caminhos com A*
    caminhos_encontrados = []
    
    # Fila priorizada por custo estimado
    fila = [(0, 0, origem, [], None)]  # (custo_estimado, custo_real, parada, caminho, linha_anterior)
    visitados = {}  # Agora armazena múltiplos caminhos para o mesmo nó
    melhores_custos = {origem: [0]}  # Lista de custos para o mesmo nó
    
    contador_ordem = 1  # Para desempate na heap

    while fila and len(caminhos_encontrados) < max_caminhos:
        custo_estimado, custo_real, parada_atual, caminho, linha_anterior = heapq.heappop(fila)

        if parada_atual == destino:
            caminho_completo = caminho + [parada_atual]
            custo_total = calcular_custo_total_caminho(caminho_completo)
            caminhos_encontrados.append((custo_total, caminho_completo))
            continue

        # Limita o número de visitas ao mesmo nó para evitar loops infinitos
        if parada_atual in visitados:
            if len(visitados[parada_atual]) > 10:  # Máximo 10 caminhos diferentes para o mesmo nó
                continue
            visitados[parada_atual].append(custo_real)
        else:
            visitados[parada_atual] = [custo_real]

        # 1. Expansão por ônibus
        if parada_atual in grafo:
            for vizinho, linha in grafo[parada_atual]:
                # Verifica se vale a pena explorar este vizinho
                custo_movimento = calcular_custo_onibus(linha_anterior, linha)
                novo_custo_real = custo_real + custo_movimento
                
                # Aceita caminhos alternativos mesmo se não forem ótimos
                if vizinho in melhores_custos:
                    # Aceita se for até 50% pior que o melhor custo
                    custo_limite = min(melhores_custos[vizinho]) * 1.5
                    if novo_custo_real > custo_limite and len(caminhos_encontrados) >= 1:
                        continue
                    melhores_custos[vizinho].append(novo_custo_real)
                else:
                    melhores_custos[vizinho] = [novo_custo_real]
                
                custo_estimado = novo_custo_real + heuristica(vizinho, destino, coordenadas_paradas)
                
                if linha_anterior is None or linha != linha_anterior:
                    novo_caminho = caminho + [parada_atual, linha]
                else:
                    novo_caminho = caminho
                
                contador_ordem += 1
                heapq.heappush(fila, (custo_estimado, novo_custo_real, vizinho, novo_caminho, linha))

        # 2. Caminhada para paradas próximas
        if parada_atual in coordenadas_paradas:
            for outra_parada in coordenadas_paradas:
                if (outra_parada == parada_atual or 
                    outra_parada not in grafo):
                    continue
                
                distancia = calcular_distancia_haversine(
                    coordenadas_paradas[parada_atual], 
                    coordenadas_paradas[outra_parada]
                )
                
                # Caminhada para paradas próximas
                if distancia <= raio_caminhada:
                    custo_caminhada = calcular_custo_caminhada(distancia)
                    novo_custo_real = custo_real + custo_caminhada
                    
                    # Verifica se vale a pena explorar
                    if outra_parada in melhores_custos:
                        custo_limite = min(melhores_custos[outra_parada]) * 1.5
                        if novo_custo_real > custo_limite and len(caminhos_encontrados) >= 1:
                            continue
                    
                    custo_estimado = novo_custo_real + heuristica(outra_parada, destino, coordenadas_paradas)
                    
                    novo_caminho = caminho + [parada_atual, f"🚶‍♂️{int(distancia)}m", outra_parada]
                    contador_ordem += 1
                    heapq.heappush(fila, (custo_estimado, novo_custo_real, outra_parada, novo_caminho, None))

    # Combina caminhos diretos e encontrados, ordena por custo
    todos_caminhos = caminhos_diretos + caminhos_encontrados
    todos_caminhos.sort(key=lambda x: x[0])  # Ordena por custo
    
    # Remove duplicatas mantendo a ordem
    caminhos_unicos = []
    caminhos_vistos = set()
    
    for custo, caminho in todos_caminhos:
        caminho_str = str(caminho)
        if caminho_str not in caminhos_vistos and len(caminhos_unicos) < max_caminhos:
            caminhos_vistos.add(caminho_str)
            caminhos_unicos.append((custo, caminho))
    
    return [caminho for custo, caminho in caminhos_unicos]

def analisar_custo_caminho(caminho):
    """
    Analisa detalhadamente os componentes do custo de um caminho
    Retorna um dicionário com a decomposição do custo
    """
    analise = {
        'custo_total': 0,
        'componentes': [],
        'trechos_onibus': 0,
        'trechos_caminhada': 0,
        'trocas_linha': 0,
        'distancia_total_caminhada': 0,
        'detalhes_trechos': []
    }
    
    i = 0
    linha_anterior = None
    
    while i < len(caminho):
        if i == len(caminho) - 1:
            break
        
        if isinstance(caminho[i], int) and i + 1 < len(caminho):
            if isinstance(caminho[i + 1], str):
                meio = caminho[i + 1]
                
                if meio.startswith("🚶‍♂️"):
                    # Custo de caminhada
                    distancia = int(meio.replace("🚶‍♂️", "").replace("m", ""))
                    custo_trecho = calcular_custo_caminhada(distancia)
                    analise['custo_total'] += custo_trecho
                    analise['trechos_caminhada'] += 1
                    analise['distancia_total_caminhada'] += distancia
                    
                    componente = {
                        'tipo': 'caminhada',
                        'origem': caminho[i],
                        'destino': caminho[i + 2] if i + 2 < len(caminho) else 'FIM',
                        'distancia': distancia,
                        'custo': custo_trecho,
                        'descricao': f"Caminhada {distancia}m: custo = {distancia}m / 50 = {custo_trecho:.2f}"
                    }
                    analise['componentes'].append(componente)
                    analise['detalhes_trechos'].append(f"🚶‍♂️ {distancia}m (custo: {custo_trecho:.2f})")
                    
                    i += 3
                else:
                    # Custo de ônibus
                    linha_atual = meio
                    custo_trecho = calcular_custo_onibus(linha_anterior, linha_atual)
                    analise['custo_total'] += custo_trecho
                    analise['trechos_onibus'] += 1
                    
                    # Verifica se houve troca de linha
                    if linha_anterior is not None and linha_atual != linha_anterior:
                        analise['trocas_linha'] += 1
                    
                    componente = {
                        'tipo': 'onibus',
                        'origem': caminho[i],
                        'destino': caminho[i + 2] if i + 2 < len(caminho) else 'FIM',
                        'linha': linha_atual,
                        'linha_anterior': linha_anterior,
                        'custo': custo_trecho,
                        'descricao': f"Ônibus {linha_atual}: custo_base(2.0) + {'troca(3.0)' if linha_anterior and linha_atual != linha_anterior else 'mesma_linha(-0.5)' if linha_anterior == linha_atual else 'inicio(0.0)'} = {custo_trecho:.2f}"
                    }
                    analise['componentes'].append(componente)
                    analise['detalhes_trechos'].append(f"🚌 {linha_atual} (custo: {custo_trecho:.2f})")
                    
                    linha_anterior = linha_atual
                    i += 2
            else:
                i += 1
        else:
            i += 1
    
    return analise

def calcular_custo_total_caminho(caminho):
    """
    Calcula o custo total de um caminho completo
    """
    analise = analisar_custo_caminho(caminho)
    return analise['custo_total']

def calcular_custo_onibus(linha_anterior, linha_atual):
    """
    Calcula custo do movimento de ônibus
    """
    custo = 2.0  # Custo base do ônibus
    
    if linha_anterior is not None and linha_atual != linha_anterior:
        custo += 3.0  # Penalidade por troca de linha
    
    if linha_anterior == linha_atual:
        custo -= 0.5  # Bonus por permanecer na mesma linha
        
    return max(1.0, custo)

def calcular_custo_caminhada(distancia_metros):
    """
    Calcula custo da caminhada
    """
    return distancia_metros / 50.0

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

def formatar_multiplos_caminhos(lista_caminhos):
    """
    Formata múltiplos caminhos de maneira legível
    """
    if not lista_caminhos:
        return "Nenhum caminho encontrado"
    
    resultado = []
    
    for idx, caminho in enumerate(lista_caminhos, 1):
        resultado.append(f"\n{'='*60}")
        resultado.append(f"🚀 ROTA {idx} (Ordem de Eficiência)")
        resultado.append(f"{'='*60}")
        
        resultado.append(formatar_caminho(caminho))
    
    return "\n".join(resultado)

def formatar_analise_detalhada(caminho, numero_rota):
    """
    Formata uma análise detalhada do custo de uma rota específica
    """
    analise = analisar_custo_caminho(caminho)
    
    resultado = []
    resultado.append(f"\n{'='*70}")
    resultado.append(f"📊 ANÁLISE DETALHADA - ROTA {numero_rota}")
    resultado.append(f"{'='*70}")
    
    # Resumo geral
    resultado.append("\n📈 RESUMO GERAL:")
    resultado.append(f"   💰 Custo total: {analise['custo_total']:.2f}")
    resultado.append(f"   🚌 Trechos de ônibus: {analise['trechos_onibus']}")
    resultado.append(f"   🚶‍♂️ Trechos a pé: {analise['trechos_caminhada']}")
    resultado.append(f"   👣 Distância total caminhada: {analise['distancia_total_caminhada']}m")
    resultado.append(f"   🔄 Trocas de linha: {analise['trocas_linha']}")
    
    # Detalhamento dos componentes do custo
    resultado.append("\n🔍 DECOMPOSIÇÃO DO CUSTO:")
    
    for i, componente in enumerate(analise['componentes'], 1):
        if componente['tipo'] == 'onibus':
            resultado.append(f"\n   {i}. ÔNIBUS {componente['linha']}:")
            resultado.append(f"      📍 {componente['origem']} → {componente['destino']}")
            resultado.append(f"      💰 {componente['descricao']}")
        else:
            resultado.append(f"\n   {i}. CAMINHADA:")
            resultado.append(f"      📍 {componente['origem']} → {componente['destino']}")
            resultado.append(f"      💰 {componente['descricao']}")
    
    # Fatores que influenciaram o custo
    resultado.append("\n🎯 FATORES QUE INFLUENCIARAM O CUSTO:")
    
    if analise['trocas_linha'] > 0:
        resultado.append(f"   ⚠️  Penalidades por troca de linha: +{analise['trocas_linha'] * 3.0}")
    
    if analise['distancia_total_caminhada'] > 0:
        resultado.append(f"   ✅ Caminhadas: custo muito baixo ({analise['distancia_total_caminhada']}m / 50 = {analise['distancia_total_caminhada']/50:.2f})")
    
    if analise['trechos_onibus'] > 0 and analise['trocas_linha'] == 0:
        resultado.append(f"   ✅ Viagem direta: sem trocas de linha")
    
    # Comparação com outras opções
    resultado.append(f"\n💡 DICAS:")
    if analise['trocas_linha'] > 0:
        resultado.append(f"   • Esta rota requer {analise['trocas_linha']} troca(s) de linha")
        resultado.append(f"   • Cada troca adiciona +3.0 ao custo total")
    else:
        resultado.append(f"   • ✅ Rota direta sem trocas de linha!")
    
    if analise['distancia_total_caminhada'] > 0:
        resultado.append(f"   • 🚶‍♂️ Inclui {analise['distancia_total_caminhada']}m de caminhada (custo muito baixo)")
    
    return "\n".join(resultado)

def formatar_caminho(caminho):
    """
    Formata um único caminho de maneira legível
    """
    if not caminho:
        return "Caminho vazio"
    
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
    
    # Custo total (para comparação)
    custo_total = calcular_custo_total_caminho(caminho)
    resultado.append(f"   💰 Custo estimado: {custo_total:.2f}")
    
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

# Funções de compatibilidade
def encontrar_caminho_com_caminhadas(grafo, coordenadas_paradas, origem, destino, raio_caminhada=400):
    """
    Função original mantida para compatibilidade - retorna apenas o melhor caminho
    """
    caminhos = encontrar_multiplos_caminhos(grafo, coordenadas_paradas, origem, destino, raio_caminhada, max_caminhos=1)
    return caminhos[0] if caminhos else None

def encontrar_caminho_com_integracao_astar(grafo, origem, destino):
    """
    Função original mantida para compatibilidade
    """
    return encontrar_caminho_com_caminhadas(grafo, {}, origem, destino)