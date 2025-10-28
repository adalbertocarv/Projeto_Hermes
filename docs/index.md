# Projeto Hermes

## **Sistema de Rotas Otimizadas com Integração e Geolocalização**

---

## Visão Geral

O **Projeto Hermes** é uma solução de *backend* de alta performance focada em resolver o problema do caminho mais curto em redes de transporte público que integram o deslocamento a pé (*Last Mile*).

Seu núcleo é um motor de busca de rotas que utiliza o algoritmo **A\* (A-Star)** sobre um grafo direcional dinâmico, garantindo precisão e velocidade na resposta.

### Objetivos do Módulo de Rotas
* **Otimização de Rotas**: Encontrar o caminho de menor custo (otimizado por número de baldeações e distância) entre quaisquer duas paradas.
* **Integração de Modalidades**: Modelar e integrar trechos de **caminhada** de forma inteligente, permitindo baldeações eficientes entre paradas.
* **Alta Performance**: Persistência do grafo em memória/disco (`.pkl`) para inicialização rápida e uso de estruturas de dados otimizadas (dicionários, `heapq`).
* **Disponibilidade via API**: Expor todas as funcionalidades por uma API REST robusta e documentada (FastAPI).

### Tecnologias
| Categoria | Tecnologia | Uso no Projeto |
| :--- | :--- | :--- |
| **Linguagem** | Python | Linguagem principal para o *backend*, algoritmos (A\*) e manipulação de dados. |
| **Banco de Dados** | PostgreSQL/PostGIS | Armazenamento persistente dos dados geográficos de linhas, sequências e paradas. **PostGIS** é crucial para a manipulação e consulta de geometrias. |
| **API Web** | FastAPI | Desenvolvimento da API RESTful, garantindo alta performance assíncrona e documentação automática (`/docs`). |
| **Algoritmo** | A\* (A-Star) | Motor central de busca de rotas, utilizando heurística geográfica (Haversine) para otimização. |
| **Documentação** | MkDocs | Estrutura modular para a documentação técnica (incluído nesta visão). |

