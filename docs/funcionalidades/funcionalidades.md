### 3. Funcionalidades Implementadas e Algoritmo A\*

#### 3.1. Construção e Direcionalidade do Grafo (`graph.py`)

1.  **Grafo Completo (Inicial)**: A função `construir_grafo_completo_rapido` cria um grafo denso onde *toda parada* é conectada a *todas as outras* paradas que compartilham a mesma linha, independentemente da ordem. Isso simplifica a construção, mas gera redundância e caminhos inválidos.
2.  **Direcionalidade (Filtro)**: A função `aplicar_direcionalidade_rapida` é a etapa mais crítica. Ela usa as **sequências ordenadas** (`sequencias`) para filtrar as conexões inválidas. Uma aresta `A -> B` na linha `L` só é mantida se o índice de `B` na sequência de `L` for **maior** que o índice de `A`. Isso transforma o grafo em um modelo direcional válido.
3.  **Integração de Caminhada**: A função `adicionar_conexoes_caminhada` (chamada em `api.py`) adiciona arestas extras (de baldeação a pé) entre pares de paradas que estão a uma distância **menor ou igual ao raio de caminhada** (padrão 400m), usando o custo (peso) calculado pela distância Haversine.

#### 3.2. Algoritmo A\* e Custo (`a_star.py`)

* **Heurística (h)**: A função `heuristica` calcula a distância em linha reta (Haversine) entre a parada atual e o destino final, e divide por um fator (ex: 1000) para converter em uma estimativa de custo. Esta é uma heurística **admissível** (nunca superestima o custo real), garantindo que o A\* encontre o caminho ótimo.
* **Custo Acumulado (g)**: O custo `g` é a soma dos custos das arestas percorridas. O custo de uma aresta é determinado por:
    * **Ônibus**: Um custo baixo (geralmente fixo ou baseado no número de paradas) para priorizar o transporte público.
    * **Caminhada**: Um custo baseado na distância em metros, que é crucial para otimizar as baldeações.
    * **Penalidade de Troca**: É aplicada uma penalidade (implícita ou explícita) no custo acumulado `g` para desincentivar um grande número de baldeações entre linhas (contado pela função `contar_trocas_linha`).
* **Funcionalidade Multicaminho**: A função principal `encontrar_multiplos_caminhos` permite que o algoritmo A\* continue explorando após encontrar o primeiro caminho ótimo, retornando até `max_caminhos` (padrão 5) ordenados por custo.

---