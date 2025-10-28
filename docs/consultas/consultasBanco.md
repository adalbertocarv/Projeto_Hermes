### 2. Consultas Detalhadas Utilizadas no Banco (PostgreSQL/PostGIS)

O carregamento inicial dos dados (`database.py`) é feito através de consultas ao PostgreSQL com a extensão PostGIS para dados geoespaciais. As credenciais de conexão são carregadas via variáveis de ambiente (`os.getenv`) ou *hardcoded* (e.g., `host='10.233.46.51'`, `user='ana_fialho'`).

| Objetivo da Consulta | Query SQL (em `database.py`) | Componente Chave |
| :--- | :--- | :--- |
| **Sequências de Linhas** | `SELECT cod_linha, sentido, paradas as array_paradas FROM linha_sentido_parada.tab_paradas_linhas_seq_v1` | Tabela: `tab_paradas_linhas_seq_v1`. Coluna `paradas` é crucial por ser um array que define a ordem das paradas de uma linha/sentido. |
| **Geometrias/Coordenadas** | `SELECT id, ST_X(geom) as longitude, ST_Y(geom) as latitude FROM linha_sentido_parada.paradas_v1 WHERE geom IS NOT NULL` | Tabela: `paradas_v1`. Uso das funções **PostGIS** `ST_X` e `ST_Y` para extrair as coordenadas (Longitude e Latitude) da coluna geométrica (`geom`). |
| **Busca de Paradas Próximas** | (Lógica implementada em Python na API) | Embora haja uma função `buscar_paradas_proximas` no `database.py` (ou a lógica na rota `/paradas/{id}/proximas` do `api.py`), ela usa as coordenadas carregadas e a função **Haversine** (em `utils.py`) para calcular as distâncias em tempo de execução, em vez de delegar ao PostGIS (com `ST_DWithin`, por exemplo). |

---