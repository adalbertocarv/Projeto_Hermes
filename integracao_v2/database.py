from collections import defaultdict
import psycopg2


POSTGIS = {
    "user": "adalberto_junior",
    "password": "348PPJDRDF0F@",
    "host": "10.233.46.51",
    "port": 5432,
    "database": "bdg"
}


def conectar_postgis(config=POSTGIS):
    """Cria e retorna uma conexão com o banco PostgreSQL/PostGIS"""
    try:
        conn = psycopg2.connect(
            user=config["user"],
            password=config["password"],
            host=config["host"],
            port=config["port"],
            database=config["database"]
        )
        return conn
    except Exception as e:
        raise ConnectionError(f"Erro ao conectar ao banco PostGIS: {e}")


def carregar_dados_postgis(config=POSTGIS):
    """
    Carrega paradas e linhas da tabela tab_linha_parada no banco PostgreSQL.
    Retorna uma lista de paradas e um dicionário com as linhas por parada.
    """
    conn = conectar_postgis(config)
    cursor = conn.cursor()

    paradas = []
    linhas_de_onibus = defaultdict(list)

    try:
        cursor.execute('SELECT id_ponto_parada, linhas FROM linha_sentido_parada.tab_linhas_paradas_v1')
        for id_ponto_parada, linhas_str in cursor.fetchall():
            if linhas_str:
                linhas = [l.strip() for l in linhas_str.split(',')]
                linhas_de_onibus[id_ponto_parada].extend(linhas)
            paradas.append(id_ponto_parada)
    except Exception as e:
        print(f"Erro ao carregar paradas e linhas: {e}")
    finally:
        cursor.close()
        conn.close()

    return paradas, linhas_de_onibus


def carregar_sequencias_linhas_postgis(config=POSTGIS):
    """
    Carrega as sequências de paradas por linha.
    Retorna um dicionário { 'cod_linha - sentido': [lista de paradas] }.
    """
    conn = conectar_postgis(config)
    cursor = conn.cursor()

    sequencias = {}

    try:
        cursor.execute("""
            SELECT cod_linha, sentido, paradas 
            FROM linha_sentido_parada.tab_paradas_linhas_seq_v1
        """)
        for cod_linha, sentido, paradas_array in cursor.fetchall():
            linha_id = f"{cod_linha} - {sentido}"

            if isinstance(paradas_array, list):
                sequencias[linha_id] = [int(p) for p in paradas_array]
            else:
                try:
                    sequencias[linha_id] = [int(p.strip()) for p in str(paradas_array).split(',')]
                except Exception:
                    print(f"Aviso: não foi possível processar paradas da linha {linha_id}")
                    continue

    except Exception as e:
        print(f"Erro ao carregar sequências das linhas: {e}")
    finally:
        cursor.close()
        conn.close()

    return sequencias


def carregar_paradas_com_geometria(config=POSTGIS):
    """
    Carrega paradas com suas coordenadas geográficas.
    Retorna um dicionário { id_parada: {'lat': ..., 'lon': ..., 'geom': ...} }
    """
    conn = conectar_postgis(config)
    cursor = conn.cursor()

    paradas_geo = {}

    try:
        cursor.execute("""
            SELECT 
                id, 
                ST_Y(geom) as latitude,
                ST_X(geom) as longitude,
                endereco
            FROM linha_sentido_parada.paradas_v1
            WHERE geom IS NOT NULL
        """)
        
        for id_parada, latitude, longitude, endereco in cursor.fetchall():
            paradas_geo[id_parada] = {
                'lat': latitude,
                'lon': longitude,
                'endereco': endereco
            }
        
        print(f"  ✓ {len(paradas_geo)} paradas com geometria carregadas")
        
    except Exception as e:
        print(f"Erro ao carregar geometria das paradas: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

    return paradas_geo


def buscar_paradas_proximas(config=POSTGIS, raio_metros=200):
    """
    Busca paradas próximas dentro de um raio especificado.
    Retorna um dicionário { id_parada: [(id_parada_proxima, distancia_metros)] }
    
    Usa PostGIS ST_DWithin para busca eficiente.
    """
    conn = conectar_postgis(config)
    cursor = conn.cursor()

    paradas_proximas = defaultdict(list)

    try:
        # Query otimizada usando ST_DWithin (usa índice espacial)
        # Geography para cálculo preciso em metros
        cursor.execute("""
            SELECT 
                p1.id as id_origem,
                p2.id as id_destino,
                ST_Distance(p1.geom::geography, p2.geom::geography) as distancia
            FROM 
                linha_sentido_parada.paradas_v1 p1,
                linha_sentido_parada.paradas_v1 p2
            WHERE 
                p1.id != p2.id
                AND p1.geom IS NOT NULL
                AND p2.geom IS NOT NULL
                AND ST_DWithin(p1.geom::geography, p2.geom::geography, %s)
            ORDER BY p1.id, distancia
        """, (raio_metros,))
        
        count = 0
        for id_origem, id_destino, distancia in cursor.fetchall():
            paradas_proximas[id_origem].append((id_destino, round(distancia, 2)))
            count += 1
        
        print(f"  ✓ {count} conexões de caminhada encontradas (raio: {raio_metros}m)")
        print(f"  ✓ {len(paradas_proximas)} paradas têm vizinhos próximos")
        
    except Exception as e:
        print(f"Erro ao buscar paradas próximas: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

    return paradas_proximas