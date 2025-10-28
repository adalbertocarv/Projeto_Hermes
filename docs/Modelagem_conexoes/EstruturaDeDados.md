

### 1. Estruturas de Dados e Modelagem de Conexões

O sistema é um motor de busca de rotas baseado na Teoria dos Grafos, otimizado para integrar transporte público e deslocamento a pé.

| Estrutura de Dados | Implementação | Conteúdo e Função |
| :--- | :--- | :--- |
| **Grafo Principal** | `defaultdict(list)` (Python) | Representa a rede de mobilidade. As chaves são os **IDs das Paradas** (`int`). O valor é uma lista de tuplas `(parada_destino, linha_id)`, onde `linha_id` é o código da linha de ônibus (ex: `"504.1 - IDA"`) ou um identificador de caminhada (ex: `"🚶‍♂️ 400m"`). |
| **Sequências de Linhas** | `dict` de `list` | Mapeamento de `linha_id` para a **lista ordenada** das paradas que a linha percorre. Essencial para a função `aplicar_direcionalidade_rapida` (em `graph.py`) e garantir que só existam arestas no sentido correto da linha. |
| **Coordenadas Geográficas** | `dict` | Mapeamento de `ID da Parada` para `(latitude, longitude)`. Fundamental para calcular a **heurística** do A\* (distância em linha reta) e para a **integração de caminhadas** (distância Haversine). |
| **Linhas por Parada** | `defaultdict(list)` | Mapeamento de `ID da Parada` para a lista de `linha_id` que param nela. Usado na **construção inicial do grafo** para criar todas as conexões potenciais. |
| **Fila de Prioridade** | `heapq` (Módulo A\*) | Usada no algoritmo A\* para armazenar os nós a serem explorados. Prioriza o nó com o menor custo estimado total (`f(n) = g(n) + h(n)`), garantindo a eficiência na busca do caminho ótimo. |

---


### 5. Importância Estratégica do Arquivo `utils.py`

O módulo `utils.py` atua como um *toolkit* de funções genéricas e de alta importância, abstraindo lógicas complexas e repetitivas, o que é vital para a manutenção e clareza do código.

| Função | Módulo de Uso | Descrição e Impacto |
| :--- | :--- | :--- |
| `calcular_distancia_haversine(coord1, coord2)` | `a_star.py`, `api.py`, `graph.py` | Implementa a **Fórmula de Haversine** para calcular a distância do arco do círculo máximo entre dois pontos geográficos na superfície da Terra. É a base para: **Heurística** do A\* e **Integração de Caminhada** (filtrando paradas próximas). A constante `R = 6371000` (Raio da Terra em metros) garante a precisão do cálculo. |
| `salvar_grafo(grafo, caminho_arquivo)` | `api.py`, `main.py` | Serializa o grafo complexo (direcional e com caminhadas) usando o módulo **`pickle`** e o salva em disco (e.g., `grafo_com_caminhada.pkl`). |
| `carregar_grafo(caminho_arquivo)` | `api.py`, `main.py` | Deserializa o grafo do disco. É a chave para a **rapidez na inicialização da API**, evitando a lenta reconstrução do grafo a partir do banco de dados em cada *deploy* ou *restart*. |