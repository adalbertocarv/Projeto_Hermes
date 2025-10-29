# api_geo.py - VERSÃO INTEGRADA COM API DE ROTAS
import sys
import os
import psycopg2
import requests
from fastapi import FastAPI, HTTPException, Query, Path
from typing import Optional, List
import asyncio

# Configuração de paths para importar módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
sys.path.append(project_root)

print(f"📍 Caminho atual: {current_dir}")
print(f"📍 Pasta do projeto: {project_root}")

try:
    from database import (
        obter_coordenadas_parada,
        obter_coordenadas_multiplas_paradas,
        obter_trecho_linha_entre_paradas,
        obter_trecho_linha_detalhado
    )
    print("✅ Módulos importados com sucesso!")
except ImportError as e:
    print(f"❌ Erro na importação: {e}")
    sys.exit(1)

app = FastAPI(
    title="API Geográfica de Rotas de Ônibus",
    description="API para consulta de dados geográficos e visualização de rotas completas",
    version="3.0.0"
)

# URL da API principal de rotas
API_ROTAS_URL = "http://127.0.0.1:3001"

async def obter_rotas_da_api(origem: int, destino: int, max_rotas: int = 3):
    """
    Obtém as rotas da API principal
    """
    try:
        response = requests.get(
            f"{API_ROTAS_URL}/rotas/",
            params={
                "origem": origem,
                "destino": destino,
                "max_rotas": max_rotas
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Erro na API de rotas: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao conectar com API de rotas: {e}")
        return None

@app.get("/", tags=["Status"])
def root():
    """Endpoint raiz com informações da API"""
    return {
        "mensagem": "API Geográfica de Rotas de Ônibus - Versão Integrada",
        "versao": "3.0.0",
        "status": "online",
        "endpoints_principais": {
            "visualizacao_rota_completa": "/visualizacao/rota/completa/?origem=1122&destino=1425",
            "geometrias_paradas": "/paradas/geometria/?id_origem=1122&id_destino=1425",
            "linestring_trecho": "/linhas/trecho/geometria/?cod_linha=154.2&sentido=IDA&id_parada_origem=2211&id_parada_destino=1425"
        },
        "documentacao": "/docs"
    }

# ... (mantenha todos os endpoints existentes: obter_coordenadas_parada_endpoint, 
# obter_coordenadas_multiplas_paradas_endpoint, obter_trecho_linha_entre_paradas_endpoint,
# obter_trecho_linha_detalhado_endpoint, obter_geometrias_paradas, obter_trecho_linha_geometria)

@app.get("/visualizacao/rota/completa/", tags=["Visualização"])
async def visualizar_rota_completa(
    origem: int = Query(..., description="ID da parada de origem"),
    destino: int = Query(..., description="ID da parada de destino"),
    max_rotas: int = Query(3, description="Número máximo de rotas a retornar", ge=1, le=5)
):
    """
    Endpoint COMPLETO que:
    1. Busca rotas na API principal
    2. Obtém geometrias das paradas
    3. Obtém LineStrings de todos os trechos de linha
    4. Retorna tudo pronto para visualização
    """
    try:
        print(f"🔄 Buscando rotas da API principal: {origem} → {destino}")
        
        # 1. Busca rotas na API principal
        rotas_data = await obter_rotas_da_api(origem, destino, max_rotas)
        
        if not rotas_data or rotas_data.get("status") != "sucesso":
            raise HTTPException(
                status_code=404, 
                detail="Não foi possível obter rotas da API principal"
            )
        
        rotas_com_geometrias = []
        
        # 2. Para cada rota encontrada, busca as geometrias
        for rota in rotas_data["rotas"]:
            rota_visualizacao = {
                "numero_rota": rota["numero_rota"],
                "custo_total": rota["custo_total"],
                "resumo": rota["resumo"],
                "paradas": [],
                "trechos_linha": [],
                "caminhadas": [],
                "geometrias_completas": {
                    "paradas": {},
                    "linhas": {}
                }
            }
            
            # 3. Coleta todas as paradas únicas da rota
            paradas_unicas = set()
            for trecho in rota["trechos"]:
                paradas_unicas.add(trecho["parada_origem"])
                paradas_unicas.add(trecho["parada_destino"])
            
            # 4. Obtém geometrias de todas as paradas
            for parada_id in paradas_unicas:
                try:
                    geometria_parada = obter_geometrias_paradas_simples(parada_id)
                    if geometria_parada:
                        rota_visualizacao["geometrias_completas"]["paradas"][parada_id] = geometria_parada
                        
                        # Adiciona informação da parada ao array
                        tipo_parada = "origem" if parada_id == origem else "destino" if parada_id == destino else "intermediaria"
                        rota_visualizacao["paradas"].append({
                            "id": parada_id,
                            "tipo": tipo_parada,
                            "coordenadas": geometria_parada["coordenadas"],
                            "geometria_geojson": geometria_parada["geometria_geojson"]
                        })
                except Exception as e:
                    print(f"⚠️  Erro ao obter geometria da parada {parada_id}: {e}")
            
            # 5. Obtém LineStrings de todos os trechos de ônibus
            for trecho in rota["trechos"]:
                if trecho["tipo"] == "onibus":
                    try:
                        # Extrai código da linha e sentido (assumindo formato "CODIGO-SENTIDO")
                        linha_completa = trecho["linha"]
                        partes = linha_completa.split('-')
                        cod_linha = partes[0] if partes else linha_completa
                        sentido = partes[1] if len(partes) > 1 else "IDA"
                        
                        # Obtém a LineString do trecho
                        linha_geometria = obter_trecho_linha_geometria_interno(
                            cod_linha, sentido, 
                            trecho["parada_origem"], trecho["parada_destino"]
                        )
                        
                        if linha_geometria:
                            rota_visualizacao["trechos_linha"].append({
                                "linha": linha_completa,
                                "cod_linha": cod_linha,
                                "sentido": sentido,
                                "parada_origem": trecho["parada_origem"],
                                "parada_destino": trecho["parada_destino"],
                                "geometria": linha_geometria
                            })
                            
                            # Armazena no objeto de geometrias completas
                            chave_linha = f"{cod_linha}_{sentido}_{trecho['parada_origem']}_{trecho['parada_destino']}"
                            rota_visualizacao["geometrias_completas"]["linhas"][chave_linha] = linha_geometria
                            
                    except Exception as e:
                        print(f"⚠️  Erro ao obter geometria da linha {trecho['linha']}: {e}")
                
                elif trecho["tipo"] == "caminhada":
                    # Para caminhadas, usamos as coordenadas das paradas
                    origem_coords = rota_visualizacao["geometrias_completas"]["paradas"].get(trecho["parada_origem"], {})
                    destino_coords = rota_visualizacao["geometrias_completas"]["paradas"].get(trecho["parada_destino"], {})
                    
                    if origem_coords and destino_coords:
                        rota_visualizacao["caminhadas"].append({
                            "origem": trecho["parada_origem"],
                            "destino": trecho["parada_destino"],
                            "distancia_metros": trecho.get("distancia_metros", 0),
                            "coordenadas_origem": origem_coords["coordenadas"],
                            "coordenadas_destino": destino_coords["coordenadas"]
                        })
            
            rotas_com_geometrias.append(rota_visualizacao)
        
        return {
            "status": "sucesso",
            "origem": origem,
            "destino": destino,
            "total_rotas": len(rotas_com_geometrias),
            "rotas": rotas_com_geometrias
        }
        
    except Exception as e:
        print(f"❌ Erro na visualização completa da rota: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na visualização: {str(e)}")

def obter_geometrias_paradas_simples(id_parada: int):
    """
    Versão simplificada para obter geometria de uma única parada
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
            geom_wkt, geom_geojson, longitude, latitude = resultado
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

def obter_trecho_linha_geometria_interno(cod_linha: str, sentido: str, id_origem: int, id_destino: int):
    """
    Versão interna para obter geometria de trecho de linha
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
                )::json AS trecho_linha_geojson
                
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
            return resultado[0]  # Retorna o GeoJSON diretamente
        return None
        
    except Exception as e:
        print(f"❌ Erro ao obter geometria interna da linha: {e}")
        return None

@app.get("/visualizacao/rota/detalhada/{numero_rota}", tags=["Visualização"])
async def visualizar_rota_detalhada(
    numero_rota: int = Path(..., description="Número da rota", ge=1, le=5),
    origem: int = Query(..., description="ID da parada de origem"),
    destino: int = Query(..., description="ID da parada de destino")
):
    """
    Retorna uma rota específica com TODAS as geometrias para visualização detalhada
    """
    try:
        # Obtém todas as rotas
        resultado_completo = await visualizar_rota_completa(origem, destino, max_rotas=5)
        
        if numero_rota > len(resultado_completo["rotas"]):
            raise HTTPException(
                status_code=404, 
                detail=f"Rota {numero_rota} não encontrada. Total disponível: {len(resultado_completo['rotas'])}"
            )
        
        rota_escolhida = resultado_completo["rotas"][numero_rota - 1]
        
        return {
            "status": "sucesso",
            "rota_escolhida": numero_rota,
            "origem": origem,
            "destino": destino,
            "dados_rota": rota_escolhida
        }
        
    except Exception as e:
        print(f"❌ Erro na visualização detalhada da rota: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na visualização: {str(e)}")

@app.get("/health", tags=["Status"])
def health_check():
    """Endpoint de health check para monitoramento"""
    return {
        "status": "healthy",
        "api": "geográfica",
        "versao": "3.0.0",
        "funcionalidades": [
            "Consulta de coordenadas de paradas",
            "Trechos de linhas entre paradas", 
            "Visualização completa de rotas",
            "Integração com API principal",
            "Geometrias em GeoJSON para mapas"
        ],
        "api_rotas_conectada": API_ROTAS_URL
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  🗺️  API GEOGRÁFICA DE ROTAS DE ÔNIBUS - v3.0")
    print("  📍 VISUALIZAÇÃO COMPLETA DE ROTAS")
    print("  🔗 Integrada com API principal de rotas")
    print("="*60)
    print(f"  🌐 API Rotas: {API_ROTAS_URL}")
    print("  🚀 Endpoint principal: /visualizacao/rota/completa/")
    print("="*60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=3002, log_level="info")