from collections import defaultdict

def construir_grafo_completo_rapido(paradas, linhas_de_onibus):
    """Constrói grafo completo de forma ULTRA rápida"""
    grafo = defaultdict(list)
    
    print("Construindo grafo completo (versão turbo)...")
    
    # ETAPA 1: Inverter o mapeamento
    linha_para_paradas = defaultdict(list)
    for parada, linhas in linhas_de_onibus.items():
        for linha in linhas:
            linha_para_paradas[linha].append(parada)
    
    print(f"  {len(linha_para_paradas)} linhas únicas")
    
    # ETAPA 2: Conectar paradas de forma otimizada
    total_conexoes = 0
    for linha, paradas_da_linha in linha_para_paradas.items():
        n = len(paradas_da_linha)
        # Conectar cada parada com todas as outras da mesma linha
        for i in range(n):
            origem = paradas_da_linha[i]
            for j in range(n):
                if i != j:
                    destino = paradas_da_linha[j]
                    grafo[origem].append((destino, linha))
                    total_conexoes += 1
    
    print(f"✅ Grafo completo: {len(grafo)} paradas, {total_conexoes} conexões")
    return grafo

def aplicar_direcionalidade_rapida(grafo_completo, sequencias):
    """Versão otimizada da direcionalidade"""
    print("Aplicando direcionalidade (versão rápida)...")
    
    grafo_direcional = defaultdict(list)
    total_processadas = 0
    
    # Pré-computar índices para validação mais rápida
    cache_indices = {}
    
    for parada_origem, conexoes in grafo_completo.items():
        for parada_destino, linha in conexoes:
            total_processadas += 1
            
            # Usar cache para validação mais rápida
            if linha not in cache_indices:
                if linha in sequencias:
                    # Criar dicionário de índices para acesso O(1)
                    seq = sequencias[linha]
                    cache_indices[linha] = {parada: idx for idx, parada in enumerate(seq)}
                else:
                    cache_indices[linha] = None
            
            indices = cache_indices[linha]
            if indices and parada_origem in indices and parada_destino in indices:
                if indices[parada_destino] > indices[parada_origem]:
                    grafo_direcional[parada_origem].append((parada_destino, linha))
    
    print(f"✅ Grafo direcional: {len(grafo_direcional)} paradas")
    return grafo_direcional

# Para manter compatibilidade
construir_grafo_completo = construir_grafo_completo_rapido
aplicar_direcionalidade = aplicar_direcionalidade_rapida