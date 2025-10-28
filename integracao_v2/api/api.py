import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from database import carregar_dados_com_geolocalizacao
from graph import construir_grafo_completo, aplicar_direcionalidade
from a_star import (
    encontrar_multiplos_caminhos,
    encontrar_linha_mais_direta,
    analisar_custo_caminho,
    calcular_custo_total_caminho,
    contar_trocas_linha
)
from utils import carregar_grafo, salvar_grafo
from typing import Optional

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    inicializar_grafo()
    yield
    # Shutdown (se necessário)

app = FastAPI(
    title="Sistema de Rotas de Ônibus com Caminhada",
    description="API para busca de rotas otimizadas com grafo direcional e conexões de caminhada (PostgreSQL)",
    version="4.0.0",
    lifespan=lifespan
)

diretorio_atual = os.path.dirname(os.path.abspath(__file__))
diretorio_pai = os.path.dirname(diretorio_atual)
caminho_arquivo_grafo = os.path.join(diretorio_pai, 'grafo_direcional_com_caminhada.pkl')

# Variáveis globais
grafo = None
paradas_disponiveis = []
linhas_por_parada = {}
sequencias = {}
linhas_info = {}
coordenadas_paradas = {}


def inicializar_grafo():
    """Inicializa ou carrega o grafo com conexões de caminhada"""
    global grafo, paradas_disponiveis, linhas_por_parada, sequencias, linhas_info, coordenadas_paradas
    
    print("🚀 Inicializando sistema de rotas com caminhada...")
    
    # SEMPRE carrega dados geográficos
    print("📊 Carregando dados do PostgreSQL...")
    paradas, linhas_por_parada, sequencias, linhas_info, coordenadas_paradas = carregar_dados_com_geolocalizacao()
    paradas_disponiveis = paradas
    
    if not paradas:
        print("❌ Erro: Não foi possível carregar dados do banco.")
        return
    
    print(f"    ✓ {len(paradas)} paradas carregadas")
    print(f"    ✓ {len(sequencias)} linhas com sequências")
    print(f"    ✓ {len(coordenadas_paradas)} paradas com coordenadas")
    
    # Tenta carregar cache
    grafo = carregar_grafo(caminho_arquivo_grafo)
    
    if grafo is None:
        print("🔄 Construindo novo grafo direcional...")
        
        # [1] Construir grafo completo
        print("  [1/2] Construindo grafo completo...")
        grafo_completo = construir_grafo_completo(paradas, linhas_por_parada)
        print(f"    ✓ {sum(len(v) for v in grafo_completo.values())} conexões totais")
        
        # [2] Aplicar direcionalidade
        print("  [2/2] Aplicando direcionalidade...")
        grafo = aplicar_direcionalidade(grafo_completo, sequencias)
        print(f"    ✓ {sum(len(v) for v in grafo.values())} conexões direcionais")
        
        # Salvar
        salvar_grafo(grafo, caminho_arquivo_grafo)
        print("✅ Grafo direcional construído com sucesso!")
    else:
        print("✅ Grafo carregado do cache")


diretorio_atual = os.path.dirname(os.path.abspath(__file__))
diretorio_pai = os.path.dirname(diretorio_atual)
caminho_arquivo_grafo = os.path.join(diretorio_pai, 'grafo_direcional_com_caminhada.pkl')

# Variáveis globais
grafo = None
paradas_disponiveis = []
linhas_por_parada = {}
sequencias = {}
linhas_info = {}
coordenadas_paradas = {}

@app.get("/", tags=["Status"])
def root():
    return {
        "mensagem": "API de Rotas de Ônibus com Caminhada",
        "versao": "4.0.0",
        "status": "online",
        "funcionalidades": [
            "Rotas com ônibus (direcionais)",
            "Caminhada entre paradas (até 400m)",
            "Múltiplas rotas ordenadas por eficiência",
            "Análise detalhada de custos",
            "Otimização A* com heurística geográfica"
        ],
        "total_paradas": len(paradas_disponiveis) if paradas_disponiveis else 0,
        "paradas_com_coordenadas": len(coordenadas_paradas) if coordenadas_paradas else 0,
        "documentacao": "/docs"
    }


@app.get("/rotas/", tags=["Rotas"])
def obter_rota(
    origem: int = Query(..., description="ID da parada de origem"),
    destino: int = Query(..., description="ID da parada de destino"),
    max_rotas: int = Query(3, description="Número máximo de rotas a retornar (1-5)", ge=1, le=5),
    raio_caminhada: int = Query(400, description="Raio máximo de caminhada em metros", ge=100, le=1000)
):
    """
    Busca as melhores rotas entre duas paradas.
    
    O algoritmo usa A* com heurística geográfica e prioriza:
    1. Caminhadas curtas (custo muito baixo)
    2. Rotas diretas sem troca
    3. Menor número de integrações
    
    Retorna múltiplas rotas ordenadas por eficiência (custo total).
    """
    
    # Validações
    if origem not in paradas_disponiveis and origem not in coordenadas_paradas:
        raise HTTPException(status_code=404, detail=f"Parada {origem} não encontrada")
    
    if destino not in paradas_disponiveis and destino not in coordenadas_paradas:
        raise HTTPException(status_code=404, detail=f"Parada {destino} não encontrada")
    
    if origem == destino:
        raise HTTPException(status_code=400, detail="Origem e destino devem ser diferentes")
    
    # Verifica linha direta
    linha_direta = None
    num_paradas_direta = None
    if origem in grafo:
        linha_direta, num_paradas_direta = encontrar_linha_mais_direta(grafo, sequencias, origem, destino)
    
    # Busca múltiplos caminhos
    caminhos = encontrar_multiplos_caminhos(
        grafo, 
        coordenadas_paradas, 
        origem, 
        destino, 
        raio_caminhada=raio_caminhada,
        max_caminhos=max_rotas
    )
    
    if not caminhos:
        raise HTTPException(status_code=404, detail="Nenhuma rota encontrada")
    
    # Formata resposta com todas as rotas
    rotas_formatadas = []
    
    for idx, caminho in enumerate(caminhos, 1):
        rota_detalhada = []
        integracoes = []
        trechos_caminhada = []
        linhas_usadas = []
        
        # Processa o caminho
        i = 0
        linha_anterior = None
        
        while i < len(caminho):
            if i == len(caminho) - 1:
                break
            
            parada_atual = caminho[i]
            
            if i + 1 < len(caminho) and isinstance(caminho[i + 1], str):
                meio = caminho[i + 1]
                
                if i + 2 < len(caminho):
                    parada_proxima = caminho[i + 2]
                    
                    trecho = {
                        "parada_origem": parada_atual,
                        "parada_destino": parada_proxima
                    }
                    
                    if meio.startswith("🚶‍♂️"):
                        # Trecho de caminhada
                        distancia = int(meio.replace("🚶‍♂️", "").replace("m", ""))
                        trecho["tipo"] = "caminhada"
                        trecho["distancia_metros"] = distancia
                        trechos_caminhada.append(trecho)
                        i += 3
                    else:
                        # Trecho de ônibus
                        linha_atual = meio
                        trecho["tipo"] = "onibus"
                        trecho["linha"] = linha_atual
                        
                        if linha_atual not in linhas_usadas:
                            linhas_usadas.append(linha_atual)
                        
                        # Detecta integração
                        if linha_anterior is not None and linha_atual != linha_anterior:
                            integracoes.append({
                                "parada": parada_atual,
                                "linha_anterior": linha_anterior,
                                "linha_nova": linha_atual
                            })
                        
                        linha_anterior = linha_atual
                        i += 2
                    
                    rota_detalhada.append(trecho)
                else:
                    i += 1
            else:
                i += 1
        
        # Análise de custo
        analise = analisar_custo_caminho(caminho)
        
        rota_info = {
            "numero_rota": idx,
            "custo_total": round(analise['custo_total'], 2),
            "origem": origem,
            "destino": destino,
            "trechos": rota_detalhada,
            "resumo": {
                "total_paradas": len([x for x in caminho if isinstance(x, int)]),
                "total_linhas_onibus": len(linhas_usadas),
                "total_integracoes": len(integracoes),
                "total_trechos_caminhada": len(trechos_caminhada),
                "distancia_total_caminhada_metros": analise['distancia_total_caminhada'],
                "linhas_utilizadas": linhas_usadas
            },
            "integracoes": integracoes,
            "analise_custo": {
                "trechos_onibus": analise['trechos_onibus'],
                "trechos_caminhada": analise['trechos_caminhada'],
                "trocas_linha": analise['trocas_linha']
            }
        }
        
        rotas_formatadas.append(rota_info)
    
    resposta = {
        "status": "sucesso",
        "origem": origem,
        "destino": destino,
        "total_rotas_encontradas": len(rotas_formatadas),
        "rotas": rotas_formatadas
    }
    
    # Adiciona informação sobre linha direta se existir
    if linha_direta:
        resposta["linha_direta"] = {
            "existe": True,
            "linha": linha_direta,
            "numero_paradas": num_paradas_direta
        }
    
    return resposta


@app.get("/rotas/analise/{numero_rota}", tags=["Rotas"])
def analisar_rota_detalhada(
    numero_rota: int = Path(..., description="Número da rota a analisar (1-5)", ge=1, le=5),
    origem: int = Query(..., description="ID da parada de origem"),
    destino: int = Query(..., description="ID da parada de destino"),
    raio_caminhada: int = Query(400, description="Raio máximo de caminhada em metros")
):
    """
    Retorna análise detalhada do custo de uma rota específica.
    
    Inclui decomposição completa dos custos e fatores que influenciaram o resultado.
    """
    
    # Validações
    if origem not in paradas_disponiveis and origem not in coordenadas_paradas:
        raise HTTPException(status_code=404, detail=f"Parada {origem} não encontrada")
    
    if destino not in paradas_disponiveis and destino not in coordenadas_paradas:
        raise HTTPException(status_code=404, detail=f"Parada {destino} não encontrada")
    
    # Busca caminhos
    caminhos = encontrar_multiplos_caminhos(
        grafo, 
        coordenadas_paradas, 
        origem, 
        destino, 
        raio_caminhada=raio_caminhada,
        max_caminhos=5
    )
    
    if not caminhos or numero_rota > len(caminhos):
        raise HTTPException(
            status_code=404, 
            detail=f"Rota {numero_rota} não encontrada. Total de rotas disponíveis: {len(caminhos)}"
        )
    
    # Analisa a rota escolhida
    caminho = caminhos[numero_rota - 1]
    analise = analisar_custo_caminho(caminho)
    
    return {
        "numero_rota": numero_rota,
        "origem": origem,
        "destino": destino,
        "custo_total": round(analise['custo_total'], 2),
        "resumo": {
            "trechos_onibus": analise['trechos_onibus'],
            "trechos_caminhada": analise['trechos_caminhada'],
            "trocas_linha": analise['trocas_linha'],
            "distancia_total_caminhada_metros": analise['distancia_total_caminhada']
        },
        "componentes": analise['componentes'],
        "detalhes_trechos": analise['detalhes_trechos']
    }


@app.post("/grafo/reconstruir", tags=["Administração"])
def reconstruir_grafo():
    """Reconstrói o grafo do zero"""
    
    if os.path.exists(caminho_arquivo_grafo):
        os.remove(caminho_arquivo_grafo)
    
    try:
        inicializar_grafo()
        return {
            "status": "sucesso",
            "total_paradas": len(paradas_disponiveis),
            "total_conexoes": sum(len(v) for v in grafo.values()) if grafo else 0,
            "paradas_com_coordenadas": len(coordenadas_paradas)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


@app.get("/status", tags=["Status"])
def status():
    """Verifica o status do sistema"""
    return {
        "grafo_carregado": grafo is not None,
        "total_paradas": len(paradas_disponiveis),
        "paradas_com_coordenadas": len(coordenadas_paradas),
        "total_linhas": len(sequencias),
        "total_conexoes": sum(len(v) for v in grafo.values()) if grafo else 0,
        "cache_ativo": True,
        "fonte_dados": "PostgreSQL",
        "funcionalidade_caminhada": "ativa",
        "algoritmo": "A* com heurística geográfica"
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
        paradas_filtradas = [
            parada for parada, linhas in linhas_por_parada.items() 
            if linha in linhas
        ]
        
        if not paradas_filtradas:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhuma parada encontrada para a linha {linha}"
            )
        
        resultado = paradas_filtradas
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
    conexoes_onibus = []
    
    if grafo and id_parada in grafo:
        vizinhos_onibus = {}
        
        for vizinho, linha in grafo[id_parada]:
            if vizinho not in vizinhos_onibus:
                vizinhos_onibus[vizinho] = []
            vizinhos_onibus[vizinho].append(linha)
        
        for vizinho, linhas_conexao in vizinhos_onibus.items():
            conexoes_onibus.append({
                "parada_destino": vizinho,
                "linhas": linhas_conexao
            })
    
    # Informações geográficas
    coordenadas = coordenadas_paradas.get(id_parada)
    
    resposta = {
        "id_parada": id_parada,
        "linhas": linhas,
        "total_linhas": len(linhas),
        "conexoes_onibus": len(conexoes_onibus),
        "destinos_onibus": conexoes_onibus[:10]  # Limita a 10
    }
    
    if coordenadas:
        resposta["coordenadas"] = {
            "latitude": coordenadas[0],
            "longitude": coordenadas[1]
        }
    
    return resposta


@app.get("/linhas/", tags=["Linhas"])
def listar_linhas():
    """
    Lista todas as linhas disponíveis no sistema.
    """
    
    # Extrai todas as linhas únicas
    linhas_unicas = sorted(list(sequencias.keys()))
    
    return {
        "total": len(linhas_unicas),
        "linhas": linhas_unicas
    }


@app.get("/linhas/{cod_linha}", tags=["Linhas"])
def detalhes_linha(cod_linha: str):
    """
    Retorna detalhes de uma linha específica.
    
    - **cod_linha**: Código da linha (ex: "504.1-IDA")
    """
    
    if cod_linha not in sequencias:
        raise HTTPException(
            status_code=404,
            detail=f"Linha {cod_linha} não encontrada"
        )
    
    paradas_da_linha = sequencias[cod_linha]
    sentido = linhas_info.get(cod_linha, "Desconhecido")
    
    return {
        "linha": cod_linha,
        "sentido": sentido,
        "total_paradas": len(paradas_da_linha),
        "paradas": paradas_da_linha
    }


@app.get("/paradas/{id_parada}/proximas", tags=["Paradas"])
def paradas_proximas_caminhada(
    id_parada: int, 
    raio: Optional[int] = Query(400, description="Raio em metros", ge=100, le=1000)
):
    """
    Retorna paradas próximas acessíveis por caminhada.
    
    - **id_parada**: ID da parada de origem
    - **raio**: Raio máximo em metros (padrão: 400m)
    """
    
    if id_parada not in coordenadas_paradas:
        raise HTTPException(
            status_code=404,
            detail=f"Parada {id_parada} não encontrada ou sem coordenadas"
        )
    
    from utils import calcular_distancia_haversine
    
    coord_origem = coordenadas_paradas[id_parada]
    proximas = []
    
    for outra_parada, coord_destino in coordenadas_paradas.items():
        if outra_parada == id_parada:
            continue
        
        distancia = calcular_distancia_haversine(coord_origem, coord_destino)
        
        if distancia <= raio:
            proximas.append({
                "parada_id": outra_parada,
                "distancia_metros": round(distancia, 2),
                "linhas": linhas_por_parada.get(outra_parada, []),
                "coordenadas": {
                    "latitude": coord_destino[0],
                    "longitude": coord_destino[1]
                }
            })
    
    # Ordena por distância
    proximas.sort(key=lambda x: x['distancia_metros'])
    
    return {
        "parada_origem": id_parada,
        "raio_busca": raio,
        "total_encontradas": len(proximas),
        "paradas_proximas": proximas
    }


@app.get("/health", tags=["Status"])
def health_check():
    """Endpoint de health check para monitoramento"""
    return {
        "status": "healthy",
        "grafo_disponivel": grafo is not None,
        "paradas_carregadas": len(paradas_disponiveis) > 0,
        "coordenadas_carregadas": len(coordenadas_paradas) > 0,
        "sequencias_carregadas": len(sequencias) > 0,
        "funcionalidade_caminhada": "ativa",
        "fonte_dados": "PostgreSQL",
        "algoritmo": "A* com heurística Haversine"
    }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  🚌 API DE ROTAS - VERSÃO COM CAMINHADA E A*")
    print("  🚶 Raio de caminhada: até 400 metros")
    print("  🎯 Múltiplas rotas ordenadas por eficiência")
    print("="*60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=3001, log_level="info")