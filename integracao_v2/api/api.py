import sys
import os
import psycopg2
import requests
import uuid
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

# =============================================================================
# CONFIGURAÇÃO DE PATHS PARA IMPORTS
# =============================================================================

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

print(f"📍 Current dir: {current_dir}")
print(f"📍 Parent dir: {parent_dir}")

try:
    from database import carregar_dados_com_geolocalizacao, obter_coordenadas_parada, obter_coordenadas_multiplas_paradas, obter_trecho_linha_entre_paradas, obter_trecho_linha_detalhado
    from graph import construir_grafo_completo, aplicar_direcionalidade
    from a_star import (
        encontrar_multiplos_caminhos,
        encontrar_linha_mais_direta,
        analisar_custo_caminho,
        calcular_custo_total_caminho,
        contar_trocas_linha
    )
    from utils import carregar_grafo, salvar_grafo, calcular_distancia_haversine
    print("✅ Todos os módulos importados com sucesso!")
except ImportError as e:
    print(f"❌ Erro na importação: {e}")
    sys.exit(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    inicializar_grafo()
    yield
    # Shutdown (se necessário)

app = FastAPI(
    title="Sistema de Rotas de Ônibus com Caminhada e Visualização Geográfica",
    description="API completa para busca de rotas otimizadas com grafo direcional, conexões de caminhada e visualização geográfica (PostgreSQL)",
    version="5.1.0",
    lifespan=lifespan
)

# Caminho para o cache do grafo
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
diretorio_pai = os.path.dirname(diretorio_atual)
caminho_arquivo_grafo = os.path.join(diretorio_pai, 'grafo_direcional_com_caminhada.pkl')

print(f"📁 Caminho do grafo: {caminho_arquivo_grafo}")

# Variáveis globais
grafo = None
paradas_disponiveis = []
linhas_por_parada = {}
sequencias = {}
linhas_info = {}
coordenadas_paradas = {}

# Cache de rotas (em produção usar Redis ou similar)
cache_rotas = {}

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


@app.get("/", tags=["Status"])
def root():
    return {
        "mensagem": "API Completa de Rotas de Ônibus com Caminhada e Visualização Geográfica",
        "versao": "5.1.0",
        "status": "online",
        "funcionalidades": [
            "Rotas com ônibus (direcionais)",
            "Caminhada entre paradas (até 400m)",
            "Múltiplas rotas ordenadas por eficiência",
            "Análise detalhada de custos",
            "Visualização geográfica por rota específica",
            "Geometrias em GeoJSON para mapas"
        ],
        "fluxo_recomendado": [
            "1. GET /rotas/?origem=X&destino=Y - Busca múltiplas rotas",
            "2. GET /visualizacao/rota/{id_rota} - Visualização geográfica de uma rota específica"
        ],
        "total_paradas": len(paradas_disponiveis) if paradas_disponiveis else 0,
        "paradas_com_coordenadas": len(coordenadas_paradas) if coordenadas_paradas else 0,
        "documentacao": "/docs"
    }


@app.get("/rotas/", tags=["Rotas"])
def obter_rotas(
    origem: int = Query(..., description="ID da parada de origem"),
    destino: int = Query(..., description="ID da parada de destino"),
    max_rotas: int = Query(3, description="Número máximo de rotas a retornar (1-5)", ge=1, le=5),
    raio_caminhada: int = Query(400, description="Raio máximo de caminhada em metros", ge=100, le=1000)
):
    """
    Busca as melhores rotas entre duas paradas e retorna múltiplas opções.
    
    Cada rota recebe um ID único que pode ser usado para obter a visualização geográfica específica.
    
    O algoritmo usa A* com heurística geográfica e prioriza:
    1. Caminhadas curtas (custo muito baixo)
    2. Rotas diretas sem troca
    3. Menor número de integrações
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
    
    # Gera ID único para esta consulta
    consulta_id = str(uuid.uuid4())
    rotas_com_ids = []
    
    # Formata resposta com todas as rotas
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
        
        # Gera ID único para esta rota
        rota_id = f"{consulta_id}_{idx}"
        
        rota_info = {
            "id_rota": rota_id,
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
        
        # Armazena no cache
        cache_rotas[rota_id] = {
            "rota_info": rota_info,
            "caminho_original": caminho,
            "timestamp": os.times().elapsed
        }
        
        rotas_com_ids.append(rota_info)
    
    resposta = {
        "status": "sucesso",
        "consulta_id": consulta_id,
        "origem": origem,
        "destino": destino,
        "total_rotas_encontradas": len(rotas_com_ids),
        "rotas": rotas_com_ids
    }
    
    # Adiciona informação sobre linha direta se existir
    if linha_direta:
        resposta["linha_direta"] = {
            "existe": True,
            "linha": linha_direta,
            "numero_paradas": num_paradas_direta
        }
    
    return resposta


@app.get("/visualizacao/rota/{id_rota}", tags=["Visualização Geográfica"])
def visualizar_rota_especifica(id_rota: str = Path(..., description="ID único da rota")):
    """
    Retorna a visualização geográfica completa de UMA rota específica.
    
    Inclui:
    - Coordenadas de todas as paradas da rota
    - LineStrings de todos os trechos de ônibus
    - Informações de caminhadas (se houver)
    - Geometrias em formato GeoJSON para visualização em mapas
    """
    
    # Recupera a rota do cache
    if id_rota not in cache_rotas:
        raise HTTPException(
            status_code=404,
            detail=f"Rota {id_rota} não encontrada. IDs de rota expiram após algum tempo."
        )
    
    rota_cache = cache_rotas[id_rota]
    rota_info = rota_cache["rota_info"]
    
    try:
        print(f"🗺️  Gerando visualização para rota {id_rota}")
        
        rota_visualizacao = {
            "id_rota": id_rota,
            "numero_rota": rota_info["numero_rota"],
            "custo_total": rota_info["custo_total"],
            "origem": rota_info["origem"],
            "destino": rota_info["destino"],
            "resumo": rota_info["resumo"],
            "paradas": [],
            "trechos_linha": [],
            "caminhadas": [],
            "geometrias": {
                "paradas": {},
                "linhas": {}
            }
        }
        
        # 1. Coleta todas as paradas únicas da rota
        paradas_unicas = set()
        for trecho in rota_info["trechos"]:
            paradas_unicas.add(trecho["parada_origem"])
            paradas_unicas.add(trecho["parada_destino"])
        
        # 2. Obtém geometrias de todas as paradas
        for parada_id in paradas_unicas:
            try:
                geometria_parada = obter_geometria_parada_simples(parada_id)
                if geometria_parada:
                    rota_visualizacao["geometrias"]["paradas"][parada_id] = geometria_parada
                    
                    # Adiciona informação da parada ao array
                    tipo_parada = "origem" if parada_id == rota_info["origem"] else "destino" if parada_id == rota_info["destino"] else "intermediaria"
                    rota_visualizacao["paradas"].append({
                        "id": parada_id,
                        "tipo": tipo_parada,
                        "coordenadas": geometria_parada["coordenadas"],
                        "geometria_geojson": geometria_parada["geometria_geojson"]
                    })
            except Exception as e:
                print(f"⚠️  Erro ao obter geometria da parada {parada_id}: {e}")
        
        # 3. Obtém LineStrings de todos os trechos de ônibus
        for trecho in rota_info["trechos"]:
            if trecho["tipo"] == "onibus":
                try:
                    # Extrai código da linha e sentido
                    linha_completa = trecho["linha"]
                    partes = linha_completa.split('-')
                    cod_linha = partes[0] if partes else linha_completa
                    sentido = partes[1] if len(partes) > 1 else "IDA"
                    
                    # Obtém a LineString do trecho
                    linha_geometria = obter_trecho_linha_geometria(
                        cod_linha, sentido, 
                        trecho["parada_origem"], trecho["parada_destino"]
                    )
                    
                    if linha_geometria:
                        trecho_linha_info = {
                            "linha": linha_completa,
                            "cod_linha": cod_linha,
                            "sentido": sentido,
                            "parada_origem": trecho["parada_origem"],
                            "parada_destino": trecho["parada_destino"],
                            "geometria": linha_geometria
                        }
                        
                        rota_visualizacao["trechos_linha"].append(trecho_linha_info)
                        
                        # Armazena no objeto de geometrias
                        chave_linha = f"{cod_linha}_{sentido}_{trecho['parada_origem']}_{trecho['parada_destino']}"
                        rota_visualizacao["geometrias"]["linhas"][chave_linha] = linha_geometria
                        
                except Exception as e:
                    print(f"⚠️  Erro ao obter geometria da linha {trecho['linha']}: {e}")
            
            elif trecho["tipo"] == "caminhada":
                # Para caminhadas, usamos as coordenadas das paradas
                origem_coords = rota_visualizacao["geometrias"]["paradas"].get(trecho["parada_origem"], {})
                destino_coords = rota_visualizacao["geometrias"]["paradas"].get(trecho["parada_destino"], {})
                
                if origem_coords and destino_coords:
                    rota_visualizacao["caminhadas"].append({
                        "origem": trecho["parada_origem"],
                        "destino": trecho["parada_destino"],
                        "distancia_metros": trecho.get("distancia_metros", 0),
                        "coordenadas_origem": origem_coords["coordenadas"],
                        "coordenadas_destino": destino_coords["coordenadas"]
                    })
        
        return {
            "status": "sucesso",
            "rota": rota_visualizacao
        }
        
    except Exception as e:
        print(f"❌ Erro na visualização da rota {id_rota}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na visualização: {str(e)}")


@app.get("/visualizacao/rota/detalhada/{id_rota}", tags=["Visualização Geográfica"])
def visualizar_rota_detalhada(id_rota: str = Path(..., description="ID único da rota")):
    """
    Retorna uma visualização MAIS DETALHADA da rota específica.
    
    Inclui todas as informações da visualização básica mais:
    - Informações completas de cada parada
    - Detalhes adicionais dos trechos
    - Metadados extensos
    """
    
    # Primeiro obtém a visualização básica
    resultado_basico = visualizar_rota_especifica(id_rota)
    
    if resultado_basico["status"] != "sucesso":
        return resultado_basico
    
    rota_visualizacao = resultado_basico["rota"]
    
    # Adiciona informações detalhadas das paradas
    for parada_info in rota_visualizacao["paradas"]:
        parada_id = parada_info["id"]
        try:
            # Obtém informações detalhadas da parada
            detalhes_parada = obter_detalhes_parada_completo(parada_id)
            if detalhes_parada:
                parada_info["detalhes"] = detalhes_parada
        except Exception as e:
            print(f"⚠️  Erro ao obter detalhes da parada {parada_id}: {e}")
    
    # Adiciona informações detalhadas dos trechos de linha
    for trecho_info in rota_visualizacao["trechos_linha"]:
        try:
            detalhes_trecho = obter_trecho_linha_detalhado(
                trecho_info["cod_linha"],
                trecho_info["sentido"],
                trecho_info["parada_origem"],
                trecho_info["parada_destino"]
            )
            if detalhes_trecho:
                trecho_info["detalhes"] = detalhes_trecho
        except Exception as e:
            print(f"⚠️  Erro ao obter detalhes do trecho: {e}")
    
    return {
        "status": "sucesso",
        "rota": rota_visualizacao,
        "metadados": {
            "total_paradas": len(rota_visualizacao["paradas"]),
            "total_trechos_linha": len(rota_visualizacao["trechos_linha"]),
            "total_caminhadas": len(rota_visualizacao["caminhadas"]),
            "geometrias_disponiveis": {
                "paradas": len(rota_visualizacao["geometrias"]["paradas"]),
                "linhas": len(rota_visualizacao["geometrias"]["linhas"])
            }
        }
    }


# =============================================================================
# FUNÇÕES AUXILIARES PARA VISUALIZAÇÃO
# =============================================================================

def obter_geometria_parada_simples(id_parada: int):
    """
    Obtém geometrias de uma única parada
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', '10.233.46.51'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'bdg'),
            user=os.getenv('DB_USER', 'ana_fialho'),
            password=os.getenv('DB_PASSWORD', 'Se654c$0')
        )
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                id,
                ST_AsText(geom) as geom_wkt,
                ST_AsGeoJSON(geom)::json as geom_geojson,
                ST_X(geom) as longitude,
                ST_Y(geom) as latitude
            FROM linha_sentido_parada.paradas_v1
            WHERE id = %s
        """, (id_parada,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            id_parada, geom_wkt, geom_geojson, longitude, latitude = resultado
            return {
                "geometria_wkt": geom_wkt,
                "geometria_geojson": geom_geojson,
                "coordenadas": {
                    "latitude": float(latitude),
                    "longitude": float(longitude)
                }
            }
        return None
        
    except Exception as e:
        print(f"❌ Erro ao obter geometria da parada {id_parada}: {e}")
        return None


def obter_trecho_linha_geometria(cod_linha: str, sentido: str, id_origem: int, id_destino: int):
    """
    Obtém a geometria de um trecho de linha
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', '10.233.46.51'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'bdg'),
            user=os.getenv('DB_USER', 'ana_fialho'),
            password=os.getenv('DB_PASSWORD', 'Se654c$0')
        )
        
        cursor = conn.cursor()
        cursor.execute("""
            WITH parametros AS (
                SELECT %s::text AS cod_linha, %s::text AS sentido, 
                       %s::integer AS id_origem, %s::integer AS id_destino
            )
            SELECT 
                ST_AsGeoJSON(
                    ST_LineSubstring(
                        tl.geo_linhas_lin,
                        LEAST(
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p_origem.geom, 31983)),
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p_destino.geom, 31983))
                        ),
                        GREATEST(
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p_origem.geom, 31983)),
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p_destino.geom, 31983))
                        )
                    )
                )::json AS trecho_linha_geojson,
                
                ST_Length(
                    ST_LineSubstring(
                        tl.geo_linhas_lin,
                        LEAST(
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p_origem.geom, 31983)),
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p_destino.geom, 31983))
                        ),
                        GREATEST(
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p_origem.geom, 31983)),
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p_destino.geom, 31983))
                        )
                    )
                ) AS comprimento_metros
                
            FROM parametros p
            JOIN linha_sentido_parada.tab_linhas tl 
              ON tl.cod_linha = p.cod_linha 
             AND tl.dsc_sentido = p.sentido
            JOIN linha_sentido_parada.paradas_v1 p_origem ON p_origem.id = p.id_origem
            JOIN linha_sentido_parada.paradas_v1 p_destino ON p_destino.id = p.id_destino
        """, (cod_linha, sentido, id_origem, id_destino))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado and resultado[0]:
            return {
                "geometria_geojson": resultado[0],
                "comprimento_metros": round(float(resultado[1]), 2) if resultado[1] else 0
            }
        return None
            
    except Exception as e:
        print(f"❌ Erro ao obter geometria da linha {cod_linha}: {e}")
        return None


def obter_detalhes_parada_completo(id_parada: int):
    """
    Obtém informações completas de uma parada
    """
    try:
        if id_parada not in linhas_por_parada:
            return None
        
        linhas = linhas_por_parada[id_parada]
        coordenadas = coordenadas_paradas.get(id_parada)
        
        detalhes = {
            "id_parada": id_parada,
            "linhas": linhas,
            "total_linhas": len(linhas)
        }
        
        if coordenadas:
            detalhes["coordenadas"] = {
                "latitude": coordenadas[0],
                "longitude": coordenadas[1]
            }
        
        return detalhes
        
    except Exception as e:
        print(f"❌ Erro ao obter detalhes da parada {id_parada}: {e}")
        return None


# =============================================================================
# ENDPOINTS ORIGINAIS DA API (MANTIDOS)
# =============================================================================

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
        "rotas_em_cache": len(cache_rotas),
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
    """
    
    if linha:
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
    """
    
    if id_parada not in linhas_por_parada:
        raise HTTPException(
            status_code=404,
            detail=f"Parada {id_parada} não encontrada"
        )
    
    linhas = linhas_por_parada[id_parada]
    coordenadas = coordenadas_paradas.get(id_parada)
    
    resposta = {
        "id_parada": id_parada,
        "linhas": linhas,
        "total_linhas": len(linhas)
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
    
    linhas_unicas = sorted(list(sequencias.keys()))
    
    return {
        "total": len(linhas_unicas),
        "linhas": linhas_unicas
    }


@app.get("/linhas/{cod_linha}", tags=["Linhas"])
def detalhes_linha(cod_linha: str):
    """
    Retorna detalhes de uma linha específica.
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


@app.get("/health", tags=["Status"])
def health_check():
    """Endpoint de health check para monitoramento"""
    return {
        "status": "healthy",
        "grafo_disponivel": grafo is not None,
        "paradas_carregadas": len(paradas_disponiveis) > 0,
        "coordenadas_carregadas": len(coordenadas_paradas) > 0,
        "sequencias_carregadas": len(sequencias) > 0,
        "rotas_em_cache": len(cache_rotas),
        "funcionalidade_caminhada": "ativa",
        "fonte_dados": "PostgreSQL",
        "algoritmo": "A* com heurística Haversine",
        "versao": "5.1.0"
    }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  🚌 API COMPLETA DE ROTAS - VERSÃO 5.1")
    print("  🗺️  Visualização geográfica por rota específica")
    print("  🎯 Fluxo otimizado: Busca → Visualização individual")
    print("="*60)
    print("  🌐 Endpoints principais:")
    print("     GET /rotas/?origem=X&destino=Y - Busca múltiplas rotas")
    print("     GET /visualizacao/rota/{id_rota} - Visualização de UMA rota")
    print("     GET /visualizacao/rota/detalhada/{id_rota} - Visualização detalhada")
    print("="*60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=3001, log_level="info")