import sys
import os

# Pega o caminho absoluto do diretório onde este arquivo (api.py) está
current_dir = os.path.dirname(os.path.abspath(__file__))
# Pega o diretório pai (no seu caso, 'integracao_v2')
parent_dir = os.path.dirname(current_dir)
# Adiciona o diretório pai ao caminho de busca do Python
sys.path.append(parent_dir)

# AGORA as importações de módulos na pasta pai vão funcionar
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from database import carregar_dados_postgis, carregar_sequencias_linhas_postgis
from graph import construir_grafo, aplicar_direcionalidade
from a_star import encontrar_caminho_com_integracao_astar
from utils import carregar_grafo, salvar_grafo
from typing import Optional

app = FastAPI(
    title="Sistema de Rotas de Ônibus",
    description="API para busca de rotas otimizadas com grafo direcional (PostgreSQL)",
    version="2.0.0"
)

# Pega o caminho absoluto do diretório onde este script (api.py) está
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
# Sobe um nível para o diretório pai (a raiz do projeto, 'integracao_v2')
diretorio_pai = os.path.dirname(diretorio_atual)
# Caminho do arquivo de cache do grafo
caminho_arquivo_grafo = os.path.join(diretorio_pai, 'grafo_direcional.pkl')

# Variáveis globais para cache
grafo = None
paradas_disponiveis = []
linhas_por_parada = {}


def inicializar_grafo():
    """Inicializa ou carrega o grafo direcional"""
    global grafo, paradas_disponiveis, linhas_por_parada
    
    print("🚀 Inicializando sistema de rotas...")
    
    # Tenta carregar grafo existente
    grafo = carregar_grafo(caminho_arquivo_grafo)
    
    if grafo is None:
        print("📊 Construindo novo grafo direcional...")
        
        # Etapa 1: Carregar dados das paradas (PostgreSQL)
        print("  [1/4] Carregando paradas e linhas (PostgreSQL)...")
        paradas, linhas_de_onibus = carregar_dados_postgis()
        paradas_disponiveis = paradas
        linhas_por_parada = dict(linhas_de_onibus)
        print(f"    ✓ {len(paradas)} paradas carregadas")
        
        # Etapa 2: Construir grafo inicial
        print("  [2/4] Construindo grafo inicial...")
        grafo_inicial = construir_grafo(paradas, linhas_de_onibus)
        total_conexoes = sum(len(v) for v in grafo_inicial.values())
        print(f"    ✓ {total_conexoes} conexões criadas")
        
        # Etapa 3: Carregar sequências (PostgreSQL)
        print("  [3/4] Carregando sequências das linhas (PostgreSQL)...")
        sequencias = carregar_sequencias_linhas_postgis()
        print(f"    ✓ {len(sequencias)} linhas com sequências")
        
        # Etapa 4: Aplicar direcionalidade
        print("  [4/4] Aplicando direcionalidade...")
        grafo = aplicar_direcionalidade(grafo_inicial, sequencias)
        
        # Salvar grafo
        salvar_grafo(grafo, caminho_arquivo_grafo)
        print("✅ Grafo direcional construído com sucesso!")
    else:
        print("✅ Grafo direcional carregado do cache")
        
        # Carregar dados das paradas para consultas (mesmo com cache do grafo)
        paradas, linhas_de_onibus = carregar_dados_postgis()
        paradas_disponiveis = paradas
        linhas_por_parada = dict(linhas_de_onibus)


# Inicializa o grafo ao startar a aplicação
@app.on_event("startup")
async def startup_event():
    inicializar_grafo()


# ==================== ROTAS DA API ====================

@app.get("/", tags=["Status"])
def root():
    """Endpoint raiz com informações da API"""
    return {
        "mensagem": "API de Rotas de Ônibus - Sistema Direcional (PostgreSQL)",
        "versao": "2.0.0",
        "status": "online",
        "total_paradas": len(paradas_disponiveis) if paradas_disponiveis else 0,
        "documentacao": "/docs"
    }


@app.get("/status", tags=["Status"])
def status():
    """Verifica o status do sistema"""
    return {
        "grafo_carregado": grafo is not None,
        "total_paradas": len(paradas_disponiveis),
        "total_conexoes": sum(len(v) for v in grafo.values()) if grafo else 0,
        "cache_ativo": True,
        "fonte_dados": "PostgreSQL"
    }


@app.get("/rotas/", tags=["Rotas"])
def obter_rota(
    origem: int = Query(..., description="ID da parada de origem"),
    destino: int = Query(..., description="ID da parada de destino")
):
    """
    Busca a melhor rota entre duas paradas respeitando a direção das linhas.
    
    - **origem**: ID da parada inicial
    - **destino**: ID da parada final
    
    Retorna o caminho com linhas e pontos de integração.
    """
    
    # Validação das paradas
    if origem not in paradas_disponiveis:
        raise HTTPException(
            status_code=404,
            detail=f"Parada de origem {origem} não encontrada"
        )
    
    if destino not in paradas_disponiveis:
        raise HTTPException(
            status_code=404,
            detail=f"Parada de destino {destino} não encontrada"
        )
    
    if origem == destino:
        raise HTTPException(
            status_code=400,
            detail="Origem e destino devem ser diferentes"
        )
    
    # Busca a rota
    caminho = encontrar_caminho_com_integracao_astar(grafo, origem, destino)
    
    if not caminho:
        raise HTTPException(
            status_code=404,
            detail="Nenhuma rota encontrada entre as paradas informadas"
        )
    
    # Monta resposta detalhada
    rota_detalhada = []
    for i in range(0, len(caminho) - 1, 2):
        if i + 2 < len(caminho):
            rota_detalhada.append({
                "parada_origem": caminho[i],
                "linha": caminho[i + 1],
                "parada_destino": caminho[i + 2]
            })
    
    # Identifica integrações
    integracoes = []
    linhas_usadas = []
    
    for i in range(1, len(caminho), 2):
        linha_atual = caminho[i]
        if linha_atual not in linhas_usadas:
            linhas_usadas.append(linha_atual)
        
        if i > 1 and i + 1 < len(caminho):
            linha_anterior = caminho[i - 2]
            if linha_atual != linha_anterior:
                integracoes.append({
                    "parada": caminho[i - 1],
                    "linha_anterior": linha_anterior,
                    "linha_nova": linha_atual
                })
    
    # Calcula estatísticas
    total_paradas = len([p for i, p in enumerate(caminho) if i % 2 == 0])
    
    return {
        "status": "sucesso",
        "origem": origem,
        "destino": destino,
        "rota": rota_detalhada,
        "integracoes": integracoes,
        "resumo": {
            "total_paradas": total_paradas,
            "total_linhas": len(linhas_usadas),
            "total_integracoes": len(integracoes),
            "linhas_utilizadas": linhas_usadas
        }
    }


@app.get("/paradas/", tags=["Paradas"])
def listar_paradas(
    limite: Optional[int] = Query(None, description="Limitar número de resultados"),
    linha: Optional[str] = Query(None, description="Filtrar por linha específica")
):
    """
    Lista todas as paradas disponíveis no sistema.
    
    - **limite**: Número máximo de paradas a retornar (opcional)
    - **linha**: Filtrar paradas por linha específica (opcional)
    """
    
    if linha:
        # Filtra paradas que têm a linha especificada
        paradas_filtradas = {
            parada: linhas 
            for parada, linhas in linhas_por_parada.items() 
            if linha in linhas
        }
        
        if not paradas_filtradas:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhuma parada encontrada para a linha {linha}"
            )
        
        resultado = list(paradas_filtradas.keys())
    else:
        resultado = paradas_disponiveis
    
    # Aplica limite se fornecido
    if limite and limite > 0:
        resultado = resultado[:limite]
    
    return {
        "total": len(resultado),
        "paradas": resultado
    }


@app.get("/paradas/{id_parada}", tags=["Paradas"])
def detalhes_parada(id_parada: int):
    """
    Retorna detalhes de uma parada específica.
    
    - **id_parada**: ID da parada
    """
    
    if id_parada not in linhas_por_parada:
        raise HTTPException(
            status_code=404,
            detail=f"Parada {id_parada} não encontrada"
        )
    
    linhas = linhas_por_parada[id_parada]
    
    # Busca conexões diretas (vizinhos)
    conexoes = []
    if grafo and id_parada in grafo:
        vizinhos_unicos = {}
        for vizinho, linha in grafo[id_parada]:
            if vizinho not in vizinhos_unicos:
                vizinhos_unicos[vizinho] = []
            vizinhos_unicos[vizinho].append(linha)
        
        for vizinho, linhas_conexao in vizinhos_unicos.items():
            conexoes.append({
                "parada_destino": vizinho,
                "linhas": linhas_conexao
            })
    
    return {
        "id_parada": id_parada,
        "linhas": linhas,
        "total_linhas": len(linhas),
        "conexoes_diretas": len(conexoes),
        "destinos_disponiveis": conexoes[:10]  # Limita a 10 para não sobrecarregar
    }


@app.get("/linhas/", tags=["Linhas"])
def listar_linhas():
    """
    Lista todas as linhas disponíveis no sistema.
    """
    
    # Extrai todas as linhas únicas
    linhas_unicas = set()
    for linhas in linhas_por_parada.values():
        linhas_unicas.update(linhas)
    
    linhas_lista = sorted(list(linhas_unicas))
    
    return {
        "total": len(linhas_lista),
        "linhas": linhas_lista
    }


@app.get("/linhas/{cod_linha}", tags=["Linhas"])
def detalhes_linha(cod_linha: str):
    """
    Retorna detalhes de uma linha específica.
    
    - **cod_linha**: Código da linha (ex: "504.1")
    """
    
    # Busca paradas que têm essa linha
    paradas_da_linha = [
        parada for parada, linhas in linhas_por_parada.items()
        if cod_linha in linhas
    ]
    
    if not paradas_da_linha:
        raise HTTPException(
            status_code=404,
            detail=f"Linha {cod_linha} não encontrada"
        )
    
    return {
        "linha": cod_linha,
        "total_paradas": len(paradas_da_linha),
        "paradas": paradas_da_linha
    }


@app.post("/grafo/reconstruir", tags=["Administração"])
def reconstruir_grafo():
    """
    Força a reconstrução do grafo direcional.
    
    ⚠️ Esta operação pode levar alguns minutos.
    """
    
    # Remove cache existente
    if os.path.exists(caminho_arquivo_grafo):
        os.remove(caminho_arquivo_grafo)
        print(f"✓ Cache removido: {caminho_arquivo_grafo}")
    
    # Reconstrói
    try:
        inicializar_grafo()
        return {
            "status": "sucesso",
            "mensagem": "Grafo reconstruído com sucesso",
            "total_paradas": len(paradas_disponiveis),
            "total_conexoes": sum(len(v) for v in grafo.values())
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao reconstruir grafo: {str(e)}"
        )


@app.get("/health", tags=["Status"])
def health_check():
    """Endpoint de health check para monitoramento"""
    return {
        "status": "healthy",
        "grafo_disponivel": grafo is not None,
        "paradas_carregadas": len(paradas_disponiveis) > 0,
        "fonte_dados": "PostgreSQL"
    }


# ==================== EXECUÇÃO ====================

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  🚌 API DE ROTAS DE ÔNIBUS - SISTEMA DIRECIONAL")
    print("  📡 Fonte de dados: PostgreSQL")
    print("="*60 + "\n")
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=3000,
        log_level="info"
    )