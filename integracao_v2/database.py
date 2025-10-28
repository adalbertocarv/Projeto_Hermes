import psycopg2
import os
from collections import defaultdict

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
