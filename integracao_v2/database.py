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
                # Suporta formatos: "123, 456" ou "123,456"
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
    Carrega as sequências de paradas por linha da tabela 
    linha_sentido_parada.tab_paradas_linhas_seq_v1 no banco PostgreSQL.
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

            # paradas_array já é uma lista de inteiros
            if isinstance(paradas_array, list):
                sequencias[linha_id] = [int(p) for p in paradas_array]
            else:
                # fallback: se vier como string (situação rara)
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
