import sqlite3
from collections import defaultdict

def carregar_dados_bd(caminho_bd):
    """Carrega paradas e linhas do paradas_linhas_2025.db"""
    conn = sqlite3.connect(caminho_bd)
    cursor = conn.cursor()
    
    paradas = []
    linhas_de_onibus = defaultdict(list)
    
    cursor.execute('SELECT id_ponto_parada, linhas FROM tab_linha_parada')
    for row in cursor.fetchall():
        id_ponto_parada = row[0]
        linhas_str = row[1]
        
        if linhas_str:
            linhas = linhas_str.split(', ')
            linhas_de_onibus[id_ponto_parada].extend(linhas)
        
        paradas.append(id_ponto_parada)
    
    conn.close()
    return paradas, linhas_de_onibus


def carregar_sequencias_linhas(caminho_bd):
    """Carrega as sequências de paradas de cada linha do linhas_onibus.db"""
    conn = sqlite3.connect(caminho_bd)
    cursor = conn.cursor()
    
    sequencias = {}
    
    # Assume que a tabela tem: id, cod_linha, sentido, paradas
    cursor.execute('SELECT cod_linha, sentido, paradas FROM tab_paradas_linhas_seq')
    
    for row in cursor.fetchall():
        cod_linha = row[0]
        sentido = row[1]
        paradas_str = row[2]
        
        # Cria identificador único linha + sentido
        linha_id = f"{cod_linha} - {sentido}"
        
        # Converte string de paradas para lista de inteiros
        if paradas_str:
            # Tenta diferentes formatos possíveis
            try:
                # Formato: "2466, 2465, 2470" ou "2466,2465,2470"
                paradas = [int(p.strip()) for p in paradas_str.split(',')]
            except ValueError:
                # Formato alternativo (JSON, etc)
                import json
                try:
                    paradas = json.loads(paradas_str)
                except:
                    print(f"Aviso: Não foi possível processar paradas da linha {linha_id}")
                    continue
            
            sequencias[linha_id] = paradas
    
    conn.close()
    return sequencias
