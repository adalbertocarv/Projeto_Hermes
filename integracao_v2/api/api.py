from fastapi import FastAPI, HTTPException, Query
from database import carregar_dados_bd
from graph import construir_grafo
from a_star import encontrar_caminho_com_integracao_astar
from utils import carregar_grafo, salvar_grafo
import sqlite3

app = FastAPI()

# Caminhos dos bancos de dados
caminho_bd_roteamento = 'paradas_linhas.db'
caminho_arquivo_grafo = 'grafo.pkl'
caminho_bd_geojson = 'geojson_data.db'

# Função para conectar ao banco de dados geojson
def get_db_connection():
    conn = sqlite3.connect(caminho_bd_geojson)
    conn.row_factory = sqlite3.Row  # Para retornar os dados como dicionário
    return conn

# Carrega ou constrói o grafo na inicialização
grafo = carregar_grafo(caminho_arquivo_grafo)
if grafo is None:
    paradas, linhas_de_onibus = carregar_dados_bd(caminho_bd_roteamento)
    grafo = construir_grafo(paradas, linhas_de_onibus)
    salvar_grafo(grafo, caminho_arquivo_grafo)

# ------------------- ROTAS DE ROTEAMENTO -------------------

@app.get("/rotas/")
def obter_rota(origem: int, destino: int):
    caminho = encontrar_caminho_com_integracao_astar(grafo, origem, destino)
    
    if not caminho:
        raise HTTPException(status_code=404, detail="Nenhuma rota encontrada")
    
    rota_detalhada = []
    for i in range(0, len(caminho) - 1, 2):
        rota_detalhada.append({
            "parada_origem": caminho[i],
            "linha": caminho[i + 1],
            "parada_destino": caminho[i + 2] if i + 2 < len(caminho) else caminho[i]
        })
    
    return {"rota": rota_detalhada}

@app.get("/paradas/")
def listar_paradas():
    paradas, linhas_de_onibus = carregar_dados_bd(caminho_bd_roteamento)
    return {"paradas": paradas, "linhas": linhas_de_onibus}

# ------------------- ROTAS DE GEOLOCALIZAÇÃO (GeoJSON) -------------------

@app.get("/paradas/geo/")
def get_dados(codDftrans: list[str] = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Construir a consulta SQL com múltiplos valores de codDftrans
    query = f"SELECT * FROM geojson_data WHERE codDftrans IN ({','.join('?' * len(codDftrans))})"
    cursor.execute(query, codDftrans)
    
    rows = cursor.fetchall()
    conn.close()

    # Se nenhum dado for encontrado, retornar erro 404
    if not rows:
        raise HTTPException(status_code=404, detail="Nenhuma parada encontrada")

    # Montar a lista de objetos GeoJSON com os dados
    geojson_features = []
    for row in rows:
        geojson = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["longitude"], row["latitude"]]
            },
            "properties": {
                "sequencial": row["sequencial"],
                "sentido": row["sentido"],
                "codDftrans": row["codDftrans"]
            }
        }
        geojson_features.append(geojson)
    
    return {
        "type": "FeatureCollection",
        "features": geojson_features
    }

# ------------------- EXECUÇÃO DO UVICORN -------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
