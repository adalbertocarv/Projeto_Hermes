# database.py
import psycopg2
import os
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any

def carregar_dados_com_geolocalizacao():
    """
    Carrega dados do PostgreSQL/PostGIS com coordenadas geográficas das paradas
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
        
        # Carrega sequências de linhas
        cursor.execute('''
            SELECT 
                cod_linha,
                sentido,
                paradas as array_paradas
            FROM linha_sentido_parada.tab_paradas_linhas_seq_v1
        ''')
        
        sequencias = {}
        linhas_info = {}
        todas_paradas = set()
        linhas_por_parada = defaultdict(list)
        
        for cod_linha, sentido, array_paradas in cursor.fetchall():
            linha_id = f"{cod_linha}-{sentido}"
            linhas_info[linha_id] = sentido
            sequencias[linha_id] = array_paradas
            
            for parada in array_paradas:
                todas_paradas.add(parada)
                linhas_por_parada[parada].append(linha_id)
        
        # Carrega coordenadas geográficas das paradas - COLUNA CORRIGIDA
        cursor.execute('''
            SELECT 
                id,
                ST_X(geom) as longitude,
                ST_Y(geom) as latitude
            FROM linha_sentido_parada.paradas_v1
            WHERE geom IS NOT NULL
        ''')
        
        coordenadas_paradas = {}
        for id_parada, longitude, latitude in cursor.fetchall():
            coordenadas_paradas[id_parada] = (latitude, longitude)
        
        conn.close()
        
        print(f"✅ {len(sequencias)} linhas, {len(todas_paradas)} paradas, {len(coordenadas_paradas)} com coordenadas")
        return list(todas_paradas), linhas_por_parada, sequencias, linhas_info, coordenadas_paradas
        
    except Exception as e:
        print(f"❌ Erro no banco: {e}")
        return [], defaultdict(list), {}, {}, {}

def obter_coordenadas_parada(id_parada: int) -> Optional[Dict[str, float]]:
    """
    Retorna as coordenadas geográficas de uma parada específica
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
                ST_Y(geom) as latitude,
                ST_X(geom) as longitude
            FROM linha_sentido_parada.paradas_v1
            WHERE id = %s
        """, (id_parada,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if not resultado:
            return None
        
        parada_id, latitude, longitude = resultado
        
        return {
            "id": parada_id,
            "latitude": float(latitude),
            "longitude": float(longitude)
        }
        
    except Exception as e:
        print(f"❌ Erro ao obter coordenadas da parada {id_parada}: {e}")
        return None

def obter_coordenadas_multiplas_paradas(lista_paradas: List[int]) -> Dict[str, Any]:
    """
    Retorna as coordenadas geográficas de múltiplas paradas
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
        
        # Consulta para obter coordenadas das paradas
        placeholders = ','.join(['%s'] * len(lista_paradas))
        cursor.execute(f"""
            SELECT 
                id,
                ST_Y(geom) as latitude,
                ST_X(geom) as longitude
            FROM linha_sentido_parada.paradas_v1
            WHERE id IN ({placeholders})
        """, lista_paradas)
        
        resultados = cursor.fetchall()
        conn.close()
        
        paradas_encontradas = {}
        for parada_id, latitude, longitude in resultados:
            paradas_encontradas[parada_id] = {
                "latitude": float(latitude),
                "longitude": float(longitude)
            }
        
        # Verifica paradas não encontradas
        paradas_nao_encontradas = [id for id in lista_paradas if id not in paradas_encontradas]
        
        return {
            "paradas_encontradas": paradas_encontradas,
            "paradas_nao_encontradas": paradas_nao_encontradas,
            "total_solicitadas": len(lista_paradas),
            "total_encontradas": len(paradas_encontradas)
        }
        
    except Exception as e:
        print(f"❌ Erro ao obter coordenadas múltiplas: {e}")
        return {
            "paradas_encontradas": {},
            "paradas_nao_encontradas": lista_paradas,
            "total_solicitadas": len(lista_paradas),
            "total_encontradas": 0
        }

def obter_trecho_linha_entre_paradas(cod_linha: str, sentido: str, id_parada_origem: int, id_parada_destino: int) -> Dict[str, Any]:
    """
    Retorna o trecho da linha entre duas paradas específicas
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
        
        # Consulta otimizada para obter o trecho da linha entre as paradas
        cursor.execute("""
            WITH parametros AS (
                SELECT %s::text AS cod_linha, %s::text AS sentido, %s::integer AS id_p1, %s::integer AS id_p2
            )
            SELECT 
                ST_AsText(p1.geom) as geom_origem_wkt,
                ST_AsText(p2.geom) as geom_destino_wkt,
                ST_AsText(
                    ST_LineSubstring(
                        tl.geo_linhas_lin,
                        LEAST(
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p1.geom, 31983)),
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p2.geom, 31983))
                        ),
                        GREATEST(
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p1.geom, 31983)),
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p2.geom, 31983))
                        )
                    )
                ) AS trecho_linha_wkt,
                ST_AsGeoJSON(p1.geom)::json as geom_origem_geojson,
                ST_AsGeoJSON(p2.geom)::json as geom_destino_geojson,
                ST_AsGeoJSON(
                    ST_LineSubstring(
                        tl.geo_linhas_lin,
                        LEAST(
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p1.geom, 31983)),
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p2.geom, 31983))
                        ),
                        GREATEST(
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p1.geom, 31983)),
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p2.geom, 31983))
                        )
                    )
                )::json AS trecho_linha_geojson,
                p.cod_linha
            FROM parametros p
            JOIN linha_sentido_parada.tab_linhas tl 
              ON tl.cod_linha = p.cod_linha 
             AND tl.dsc_sentido = p.sentido
            JOIN linha_sentido_parada.paradas_v1 p1 ON p1.id = p.id_p1
            JOIN linha_sentido_parada.paradas_v1 p2 ON p2.id = p.id_p2
        """, (cod_linha, sentido, id_parada_origem, id_parada_destino))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if not resultado:
            return {
                "status": "erro",
                "mensagem": "Dados não encontrados para os parâmetros fornecidos"
            }
        
        # Extrai resultados
        (geom_origem_wkt, geom_destino_wkt, trecho_linha_wkt,
         geom_origem_geojson, geom_destino_geojson, trecho_linha_geojson,
         cod_linha_result) = resultado
        
        # Processa coordenadas das paradas
        def extrair_coordenadas_geojson(geojson_data):
            """Extrai coordenadas do GeoJSON"""
            if geojson_data and 'coordinates' in geojson_data:
                lon, lat = geojson_data['coordinates']
                return {"latitude": lat, "longitude": lon}
            return None
        
        coordenadas_origem = extrair_coordenadas_geojson(geom_origem_geojson)
        coordenadas_destino = extrair_coordenadas_geojson(geom_destino_geojson)
        
        return {
            "status": "sucesso",
            "linha": cod_linha_result,
            "sentido": sentido,
            "paradas": {
                "origem": {
                    "id": id_parada_origem,
                    "coordenadas": coordenadas_origem,
                    "geometria_wkt": geom_origem_wkt
                },
                "destino": {
                    "id": id_parada_destino,
                    "coordenadas": coordenadas_destino,
                    "geometria_wkt": geom_destino_wkt
                }
            },
            "trecho_linha": {
                "geometria_wkt": trecho_linha_wkt,
                "geometria_geojson": trecho_linha_geojson,
                "srid_original": 31983,
                "srid_saida": 4326
            }
        }
        
    except Exception as e:
        print(f"❌ Erro ao obter trecho da linha: {e}")
        return {
            "status": "erro",
            "mensagem": f"Erro na consulta: {str(e)}"
        }

def obter_trecho_linha_detalhado(cod_linha: str, sentido: str, id_parada_origem: int, id_parada_destino: int) -> Dict[str, Any]:
    """
    Retorna informações detalhadas do trecho da linha entre duas paradas
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
                SELECT %s::text AS cod_linha, %s::text AS sentido, %s::integer AS id_p1, %s::integer AS id_p2
            )
            SELECT 
                -- Geometrias em WKT
                ST_AsText(p1.geom) as geom_origem_wkt,
                ST_AsText(p2.geom) as geom_destino_wkt,
                ST_AsText(
                    ST_LineSubstring(
                        tl.geo_linhas_lin,
                        LEAST(
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p1.geom, 31983)),
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p2.geom, 31983))
                        ),
                        GREATEST(
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p1.geom, 31983)),
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p2.geom, 31983))
                        )
                    )
                ) AS trecho_linha_wkt,
                
                -- Geometrias em GeoJSON
                ST_AsGeoJSON(p1.geom)::json as geom_origem_geojson,
                ST_AsGeoJSON(p2.geom)::json as geom_destino_geojson,
                ST_AsGeoJSON(
                    ST_LineSubstring(
                        tl.geo_linhas_lin,
                        LEAST(
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p1.geom, 31983)),
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p2.geom, 31983))
                        ),
                        GREATEST(
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p1.geom, 31983)),
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p2.geom, 31983))
                        )
                    )
                )::json AS trecho_linha_geojson,
                
                -- Informações métricas
                ST_Length(
                    ST_LineSubstring(
                        tl.geo_linhas_lin,
                        LEAST(
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p1.geom, 31983)),
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p2.geom, 31983))
                        ),
                        GREATEST(
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p1.geom, 31983)),
                            ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p2.geom, 31983))
                        )
                    )
                ) as comprimento_metros,
                
                -- Posições relativas na linha
                ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p1.geom, 31983)) as posicao_relativa_origem,
                ST_LineLocatePoint(tl.geo_linhas_lin, ST_Transform(p2.geom, 31983)) as posicao_relativa_destino,
                
                p.cod_linha,
                tl.dsc_sentido
                
            FROM parametros p
            JOIN linha_sentido_parada.tab_linhas tl 
              ON tl.cod_linha = p.cod_linha 
             AND tl.dsc_sentido = p.sentido
            JOIN linha_sentido_parada.paradas_v1 p1 ON p1.id = p.id_p1
            JOIN linha_sentido_parada.paradas_v1 p2 ON p2.id = p.id_p2
        """, (cod_linha, sentido, id_parada_origem, id_parada_destino))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if not resultado:
            return {
                "status": "erro",
                "mensagem": "Dados não encontrados para os parâmetros fornecidos"
            }
        
        # Processa resultado detalhado
        (geom_origem_wkt, geom_destino_wkt, trecho_linha_wkt,
         geom_origem_geojson, geom_destino_geojson, trecho_linha_geojson,
         comprimento_metros, posicao_origem, posicao_destino,
         cod_linha_result, sentido_result) = resultado
        
        # Determina direção baseada nas posições relativas
        direcao = "progressiva" if posicao_destino > posicao_origem else "regressiva"
        
        return {
            "status": "sucesso",
            "linha": {
                "codigo": cod_linha_result,
                "sentido": sentido_result
            },
            "paradas": {
                "origem": {
                    "id": id_parada_origem,
                    "posicao_na_linha": float(posicao_origem)
                },
                "destino": {
                    "id": id_parada_destino,
                    "posicao_na_linha": float(posicao_destino)
                }
            },
            "trecho": {
                "comprimento_metros": float(comprimento_metros),
                "direcao": direcao,
                "diferenca_posicao": float(abs(posicao_destino - posicao_origem))
            },
            "geometrias": {
                "origem_wkt": geom_origem_wkt,
                "destino_wkt": geom_destino_wkt,
                "trecho_linha_wkt": trecho_linha_wkt,
                "origem_geojson": geom_origem_geojson,
                "destino_geojson": geom_destino_geojson,
                "trecho_linha_geojson": trecho_linha_geojson
            }
        }
        
    except Exception as e:
        print(f"❌ Erro ao obter trecho detalhado: {e}")
        return {
            "status": "erro",
            "mensagem": f"Erro na consulta: {str(e)}"
        }