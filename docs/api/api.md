### 4. Como a API Funciona (`api.py`)

A API é implementada usando o *framework* **FastAPI**, garantindo alto desempenho e documentação automática (`/docs`).

| Etapa | Componentes Chave | Descrição Detalhada |
| :--- | :--- | :--- |
| **Inicialização** | `main.py`, `api.py`, `utils.py` | Ao iniciar, a API tenta carregar o grafo pré-construído (`grafo_com_caminhada.pkl`) via `carregar_grafo`. Se o arquivo não existir, o processo de **Reconstrução do Grafo** (carregamento do PostGIS, construção completa, direcionalidade e conexões de caminhada) é executado, e o resultado é salvo usando `salvar_grafo` (persistência via `pickle`). |
| **Endpoint Principal** | `GET /rotas/` | Recebe `origem` e `destino` (IDs das paradas). Chama a função `encontrar_caminho_com_integracao_astar` (ou a versão de múltiplos caminhos) de `a_star.py`. A resposta retorna um objeto JSON enriquecido, incluindo o status, a sequência detalhada da rota, e um resumo com integrações e linhas utilizadas. |
| **Endpoints Auxiliares** | `GET /paradas/{id}/proximas` | Calcula e retorna as paradas a até `raio` metros de distância da parada `{id}`, utilizando o `calcular_distancia_haversine` (`utils.py`) sobre as coordenadas em memória. |
| **Status e Controle** | `GET /health`, `POST /grafo/reconstruir` | O `health_check` verifica a disponibilidade do grafo e dos dados carregados. O `POST` permite disparar a reconstrução e salvamento do grafo em tempo de execução. |
| **Tratamento de Erros** | `HTTPException` | A API utiliza o mecanismo de exceções do FastAPI para retornar erros 404 (Parada não encontrada) ou 400 (Erro de validação) com mensagens claras. |

---