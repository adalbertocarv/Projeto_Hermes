import psycopg2
import sqlite3
import json

# -------------------------------
# Conexão PostgreSQL
# -------------------------------
pg_conn = psycopg2.connect(
    host="10.233.46.51",
    dbname="bdg",
    user="adalberto_junior",
    password="senh@",
    port=5432
)
pg_cur = pg_conn.cursor()

# -------------------------------
# Conexão SQLite
# -------------------------------
sqlite_conn = sqlite3.connect("linhas_onibus.db")
sqlite_cur = sqlite_conn.cursor()

# Criação da tabela no SQLite
sqlite_cur.execute("""
CREATE TABLE IF NOT EXISTS tab_paradas_linhas_seq (
    id INTEGER PRIMARY KEY,
    cod_linha TEXT NOT NULL,
    sentido TEXT NOT NULL,
    paradas TEXT NOT NULL -- armazenado como JSON
);
""")

# -------------------------------
# Extração do PostgreSQL
# -------------------------------
pg_cur.execute("SELECT id, cod_linha, sentido, paradas FROM linha_sentido_parada.tab_paradas_linhas_seq;")
rows = pg_cur.fetchall()

# -------------------------------
# Inserção no SQLite
# -------------------------------
for row in rows:
    id_, cod_linha, sentido, paradas_array = row
    # Converte o array do PostgreSQL para JSON string
    paradas_json = json.dumps(paradas_array)
    sqlite_cur.execute("""
        INSERT INTO tab_paradas_linhas_seq (id, cod_linha, sentido, paradas)
        VALUES (?, ?, ?, ?)
    """, (id_, cod_linha, sentido, paradas_json))

sqlite_conn.commit()

# -------------------------------
# Fechar conexões
# -------------------------------
pg_cur.close()
pg_conn.close()
sqlite_cur.close()
sqlite_conn.close()

print("✅ Exportação concluída! Banco SQLite criado em 'linhas_onibus.db'")
