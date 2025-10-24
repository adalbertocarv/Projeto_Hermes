import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from database import (
    carregar_dados_postgis, 
    carregar_sequencias_linhas_postgis,
    buscar_paradas_proximas,
    carregar_paradas_com_geometria
)
from graph import (
    construir_grafo, 
    aplicar_direcionalidade,
    adicionar_conexoes_caminhada
)
from a_star import encontrar_caminho_com_integracao_astar
from utils import carregar_grafo, salvar_grafo
from typing import Optional

app = FastAPI(
    title="Sistema de Rotas de Ônibus com Caminhada",
    description="API para busca de rotas otimizadas com grafo direcional e conexões de caminhada (PostgreSQL)",
    version="3.0.0"
)

diretorio_atual = os.path.dirname(os.path.abspath(__file__))
diretorio_pai = os.path.dirname(diretorio_atual)
caminho_arquivo_grafo = os.path.join(diretorio_pai, 'grafo_com_caminhada.pkl')

# Variáveis globais
grafo = None
paradas_disponiveis = []
linhas_por_parada = {}
paradas_geo = {}


def inicializar_grafo(raio_caminhada=200):
    """Inicializa ou carrega o grafo com conexões de caminhada"""
    global grafo, paradas_disponiveis, linhas_por_parada, paradas_geo
    
    print("🚀 Inicializando sistema de rotas com caminhada...")
    
    # Tenta carregar cache
    grafo = carregar_grafo(caminho_arquivo_grafo)
    
    if grafo is None:
        print("📊 Construindo novo grafo com caminhada...")
        
        # [1] Carregar paradas e linhas
        print("  [1/6] Carregando paradas e linhas...")
        paradas, linhas_de_onibus = carregar_dados_postgis()
        paradas_disponiveis = paradas
        linhas_por_parada = dict(linhas_de_onibus)
        print(f"    ✓ {len(paradas)} paradas carregadas")
        
        # [2] Construir grafo inicial (só ônibus)
        print("  [2/6] Construindo grafo inicial...")
        grafo_inicial = construir_grafo(paradas, linhas_de_onibus)
        print(f"    ✓ {sum(len(v) for v in grafo_inicial.values())} conexões de ônibus")
        
        # [3] Carregar sequências
        print("  [3/6] Carregando sequências das linhas...")
        sequencias = carregar_sequencias_linhas_postgis()
        print(f"    ✓ {len(sequencias)} linhas com sequências")
        
        # [4] Aplicar direcionalidade
        print("  [4/6] Aplicando direcionalidade...")
        grafo = aplicar_direcionalidade(grafo_inicial, sequencias)
        
        # [5] Carregar geometrias
        print("  [5/6] Carregando geometrias das paradas...")
        paradas_geo = carregar_paradas_com_geometria()
        
        # [6] Adicionar conexões de caminhada
        print(f"  [6/6] Buscando paradas próximas (raio: {raio_caminhada}m)...")
        paradas_proximas = buscar_paradas_proximas(raio_metros=raio_caminhada)
        grafo = adicionar_conexoes_caminhada(grafo, paradas_proximas)
        
        # Salvar
        salvar_grafo(grafo, caminho_arquivo_grafo)
        print("✅ Grafo com caminhada construído com sucesso!")
    else:
        print("✅ Grafo carregado do cache")
        paradas, linhas_de_onibus = carregar_dados_postgis()
        paradas_disponiveis = paradas
        linhas_por_parada = dict(linhas_de_onibus)
        paradas_geo = carregar_paradas_com_geometria()


@app.on_event("startup")
async def startup_event():
    inicializar_grafo(raio_caminhada=200)


# ==================== ROTAS DA API ====================

@app.get("/", tags=["Status"])
def root():
    return {
        "mensagem": "API de Rotas de Ônibus com Caminhada",
        "versao": "3.0.0",
        "status": "online",
        "funcionalidades": [
            "Rotas com ônibus (direcionais)",
            "Caminhada entre paradas (até 200m)",
            "Otimização para priorizar caminhada"
        ],
        "total_paradas": len(paradas_disponiveis) if paradas_disponiveis else 0,
        "documentacao": "/docs"
    }


@app.get("/rotas/", tags=["Rotas"])
def obter_rota(
    origem: int = Query(..., description="ID da parada de origem"),
    destino: int = Query(..., description="ID da parada de destino")
):
    """
    Busca a melhor rota entre duas paradas.
    
    O algoritmo prioriza:
    1. Caminhadas curtas (até 200m)
    2. Rotas diretas sem troca
    3. Menor número de integrações
    """
    
    if origem not in paradas_disponiveis:
        raise HTTPException(status_code=404, detail=f"Parada {origem} não encontrada")
    
    if destino not in paradas_disponiveis:
        raise HTTPException(status_code=404, detail=f"Parada {destino} não encontrada")
    
    if origem == destino:
        raise HTTPException(status_code=400, detail="Origem e destino devem ser diferentes")
    
    # Busca rota
    caminho = encontrar_caminho_com_integracao_astar(grafo, origem, destino)
    
    if not caminho:
        raise HTTPException(status_code=404, detail="Nenhuma rota encontrada")
    
    # Formata resposta
    rota_detalhada = []
    integracoes = []
    trechos_caminhada = []
    linhas_usadas = []
    
    for i in range(len(caminho) - 1):
        parada_atual, tipo_transporte, identificador = caminho[i]
        parada_proxima = caminho[i + 1][0]
        
        trecho = {
            "parada_origem": parada_atual,
            "parada_destino": parada_proxima,
            "tipo": tipo_transporte,
        }
        
        if tipo_transporte == 'onibus':
            trecho["linha"] = identificador
            if identificador not in linhas_usadas:
                linhas_usadas.append(identificador)
        elif tipo_transporte == 'caminhada':
            trecho["distancia"] = identificador
            trechos_caminhada.append(trecho)
        
        rota_detalhada.append(trecho)
        
        # Detecta integrações
        if i > 0:
            tipo_anterior = caminho[i - 1][1]
            if tipo_anterior == 'onibus' and tipo_transporte == 'onibus':
                linha_anterior = caminho[i - 1][2]
                if identificador != linha_anterior:
                    integracoes.append({
                        "parada": parada_atual,
                        "linha_anterior": linha_anterior,
                        "linha_nova": identificador
                    })
    
    return {
        "status": "sucesso",
        "origem": origem,
        "destino": destino,
        "rota": rota_detalhada,
        "integracoes": integracoes,
        "resumo": {
            "total_paradas": len(caminho),
            "total_linhas_onibus": len(linhas_usadas),
            "total_integracoes": len(integracoes),
            "total_trechos_caminhada": len(trechos_caminhada),
            "linhas_utilizadas": linhas_usadas
        }
    }


@app.post("/grafo/reconstruir", tags=["Administração"])
def reconstruir_grafo(raio_caminhada: int = Query(200, description="Raio de caminhada em metros")):
    """Reconstrói o grafo com novo raio de caminhada"""
    
    if os.path.exists(caminho_arquivo_grafo):
        os.remove(caminho_arquivo_grafo)
    
    try:
        inicializar_grafo(raio_caminhada=raio_caminhada)
        return {
            "status": "sucesso",
            "raio_caminhada": raio_caminhada,
            "total_paradas": len(paradas_disponiveis),
            "total_conexoes": sum(len(v) for v in grafo.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


@app.get("/health", tags=["Status"])
def health_check():
    return {
        "status": "healthy",
        "grafo_disponivel": grafo is not None,
        "paradas_carregadas": len(paradas_disponiveis) > 0,
        "geometrias_carregadas": len(paradas_geo) > 0,
        "funcionalidade_caminhada": "ativa"
    }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  🚌 API DE ROTAS - VERSÃO COM CAMINHADA")
    print("  🚶 Raio de caminhada: 200 metros")
    print("="*60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=3001, log_level="info")