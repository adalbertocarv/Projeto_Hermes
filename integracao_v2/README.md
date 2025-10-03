# 🚌 Sistema de Rotas de Ônibus com Grafo Direcional

Sistema inteligente de busca de rotas de ônibus que utiliza algoritmo A* para encontrar o menor caminho entre paradas, respeitando a direção das linhas e identificando pontos de integração.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Estrutura de Arquivos](#estrutura-de-arquivos)
- [Bancos de Dados](#bancos-de-dados)
- [Instalação](#instalação)
- [Como Usar](#como-usar)
- [Funcionamento Interno](#funcionamento-interno)
- [Exemplo de Uso](#exemplo-de-uso)
- [Tratamento de Erros](#tratamento-de-erros)

---

## 🎯 Visão Geral

Este sistema resolve um problema comum em sistemas de transporte público: **encontrar rotas viáveis respeitando a direção das linhas de ônibus**.

### Problema Resolvido

Em sistemas tradicionais, um grafo pode sugerir pegar uma linha "IDA" para voltar ao ponto de origem, simplesmente porque há uma conexão entre as paradas. Este sistema elimina esse problema ao:

1. Criar um grafo inicial com todas as conexões possíveis
2. Validar cada conexão usando a sequência real de paradas de cada linha
3. Manter apenas conexões direcionalmente válidas

### Características

- ✅ **Grafo Direcional**: Respeita a ordem das paradas em cada linha
- ✅ **Otimização A***: Busca eficiente do menor caminho
- ✅ **Detecção de Integrações**: Identifica onde trocar de linha
- ✅ **Cache Inteligente**: Salva o grafo processado para carregamento rápido
- ✅ **Interface Amigável**: Feedback claro e detalhado

---

## 🏗️ Arquitetura

### Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────┐
│  ETAPA 1: Carregamento de Dados                             │
│  ┌──────────────────────┐    ┌──────────────────────┐      │
│  │ paradas_linhas_2025  │    │  linhas_onibus.db    │      │
│  │     .db              │    │                       │      │
│  │                      │    │                       │      │
│  │ • ID das paradas     │    │ • Sequência de        │      │
│  │ • Linhas que passam  │    │   paradas por linha   │      │
│  └──────────────────────┘    └──────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  ETAPA 2: Construção do Grafo Inicial (Não-Direcional)     │
│                                                              │
│  Parada A ←→ Parada B  (Linha 504.1)                       │
│  Parada B ←→ Parada C  (Linha 504.1)                       │
│  Parada C ←→ Parada A  (Linha 602.1)                       │
│                                                              │
│  ⚠️  Pode conter conexões inválidas!                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  ETAPA 3: Validação Direcional                              │
│                                                              │
│  Para cada aresta (origem → destino, linha):                │
│    1. Busca sequência da linha no linhas_onibus.db         │
│    2. Verifica: índice(destino) > índice(origem)?          │
│    3. Mantém apenas se válido                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  ETAPA 4: Grafo Direcional Final                            │
│                                                              │
│  Parada A → Parada B  (Linha 504.1 - IDA)    ✓             │
│  Parada B → Parada C  (Linha 504.1 - IDA)    ✓             │
│  Parada C ✗ Parada A  (Linha 602.1 - IDA)    ✗ REMOVIDA    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  ETAPA 5: Busca de Rotas (Algoritmo A*)                    │
│                                                              │
│  Entrada: Origem + Destino                                  │
│  Saída: Caminho otimizado com integrações                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Estrutura de Arquivos

```
projeto/
│
├── database.py              # Módulo de acesso aos bancos de dados
│   ├── carregar_dados_bd()
│   └── carregar_sequencias_linhas()
│
├── graph.py                 # Módulo de construção e validação do grafo
│   ├── construir_grafo()
│   ├── validar_conexao_direcional()
│   └── aplicar_direcionalidade()
│
├── a_star.py                # Implementação do algoritmo A*
│   ├── heuristica()
│   └── encontrar_caminho_com_integracao_astar()
│
├── utils.py                 # Utilitários (cache/persistência)
│   ├── salvar_grafo()
│   └── carregar_grafo()
│
├── main.py                  # Ponto de entrada da aplicação
│
├── paradas_linhas_2025.db   # BD: Paradas e linhas
├── linhas_onibus.db         # BD: Sequências de paradas
└── grafo_direcional.pkl     # Cache do grafo processado (gerado)
```

---

## 💾 Bancos de Dados

### 1. `paradas_linhas_2025.db`

**Tabela:** `tab_linha_parada`

| Campo             | Tipo    | Descrição                           |
|-------------------|---------|-------------------------------------|
| `id_ponto_parada` | INTEGER | ID único da parada                  |
| `linhas`          | TEXT    | Linhas separadas por vírgula        |

**Exemplo:**
```
id_ponto_parada | linhas
----------------|------------------------------------------------
2466            | 0.604 - IDA, 0.641 - IDA, 504.1 - CIRCULAR, ...
2465            | 0.604 - IDA, 0.641 - IDA, 504.1 - CIRCULAR, ...
```

### 2. `linhas_onibus.db`

**Tabela:** `linhas_onibus`

| Campo       | Tipo    | Descrição                                    |
|-------------|---------|----------------------------------------------|
| `id`        | INTEGER | ID único da linha                            |
| `cod_linha` | TEXT    | Código da linha (ex: "504.1")                |
| `sentido`   | TEXT    | Sentido (ex: "IDA", "VOLTA", "CIRCULAR")     |
| `paradas`   | TEXT    | Sequência de IDs das paradas separados por vírgula |

**Exemplo:**
```
cod_linha | sentido | paradas
----------|---------|-------------------------
504.1     | IDA     | 2466, 2467, 2468, 2469
504.1     | VOLTA   | 2469, 2468, 2467, 2466
```

---

## 🚀 Instalação

### Requisitos

- Python 3.7+
- Bibliotecas padrão: `sqlite3`, `heapq`, `pickle`, `collections`

### Passos

1. **Clone ou baixe os arquivos do projeto**

2. **Verifique se os bancos de dados estão no diretório:**
   ```bash
   ls -l *.db
   # Deve mostrar: paradas_linhas_2025.db e linhas_onibus.db
   ```

3. **Execute o sistema:**
   ```bash
   python main.py
   ```

---

## 📖 Como Usar

### Primeira Execução

Na primeira vez, o sistema irá:

1. Carregar dados dos bancos
2. Construir o grafo inicial
3. Aplicar validação direcional
4. Salvar o grafo em cache (`grafo_direcional.pkl`)

```
=== Construindo grafo direcional ===

[1/4] Carregando paradas e linhas...
  ✓ 5432 paradas carregadas

[2/4] Construindo grafo inicial...
  ✓ 89234 conexões criadas

[3/4] Carregando sequências das linhas...
  ✓ 287 linhas com sequências carregadas

[4/4] Aplicando direcionalidade ao grafo...
  Arestas mantidas: 44617
  Arestas removidas: 44617

✓ Grafo direcional construído com sucesso!
```

### Execuções Seguintes

O sistema carregará o grafo do cache instantaneamente:

```
✓ Grafo direcional carregado do arquivo.
```

### Buscando Rotas

```
============================================================
       SISTEMA DE ROTAS DE ÔNIBUS - BUSCA DE CAMINHOS
============================================================

------------------------------------------------------------
Digite a parada de origem (ou 'sair' para encerrar): 2466
Digite a parada de destino: 2470

Buscando rota...

============================================================
✓ CAMINHO ENCONTRADO
============================================================

📍 PERCURSO:
   Parada 2466 → Linha [504.1 - IDA] → Parada 2467
   Parada 2467 → Linha [504.1 - IDA] → Parada 2468
   Parada 2468 → Linha [602.1 - IDA] → Parada 2470

🔄 INTEGRAÇÕES NECESSÁRIAS:
   Parada 2468: 504.1 - IDA → 602.1 - IDA

📊 RESUMO:
   • Total de paradas: 4
   • Linhas utilizadas: 2
   • Integrações: 1
   • Linhas: 504.1 - IDA, 602.1 - IDA
```

### Comandos de Saída

Para encerrar o programa, digite:
- `sair`
- `exit`
- `q`
- `0`

Ou pressione `Ctrl+C`

---

## ⚙️ Funcionamento Interno

### 1. Construção do Grafo Inicial

**Arquivo:** `graph.py` → `construir_grafo()`

```python
# Para cada parada
for parada in paradas:
    # Para cada linha que passa nela
    for linha in linhas_de_onibus[parada]:
        # Conecta com todas as outras paradas dessa linha
        for vizinha in paradas:
            if linha in linhas_de_onibus[vizinha]:
                grafo[parada].append((vizinha, linha))
```

**Resultado:** Grafo não-direcional com todas as conexões possíveis.

### 2. Validação Direcional

**Arquivo:** `graph.py` → `validar_conexao_direcional()`

```python
# Busca a sequência de paradas da linha
sequencia = sequencias[linha]

# Encontra posições da origem e destino
idx_origem = sequencia.index(parada_origem)
idx_destino = sequencia.index(parada_destino)

# Válido apenas se destino vem DEPOIS da origem
return idx_destino > idx_origem
```

**Exemplo:**

```
Linha 504.1 - IDA: [2466, 2467, 2468, 2469]

Conexão: 2466 → 2468 (Linha 504.1 - IDA)
  idx_origem = 0
  idx_destino = 2
  2 > 0? SIM ✓ VÁLIDA

Conexão: 2468 → 2466 (Linha 504.1 - IDA)
  idx_origem = 2
  idx_destino = 0
  0 > 2? NÃO ✗ INVÁLIDA (removida)
```

### 3. Algoritmo A*

**Arquivo:** `a_star.py` → `encontrar_caminho_com_integracao_astar()`

**Componentes:**

1. **Função Heurística:** `h(n) = |n - destino|`
   - Estimativa simples da distância até o destino
   - Baseada na diferença entre IDs

2. **Custo:** `g(n) = número de paradas percorridas`

3. **Custo Total:** `f(n) = g(n) + h(n)`

**Processo:**

```
1. Inicializa fila com origem
2. Enquanto fila não vazia:
   a. Remove parada com menor custo estimado
   b. Se é o destino, retorna caminho
   c. Expande vizinhos não visitados
   d. Adiciona à fila com custo atualizado
```

### 4. Cache do Grafo

**Arquivo:** `utils.py`

- **Formato:** Pickle (`.pkl`)
- **Conteúdo:** Dicionário com o grafo direcional processado
- **Vantagem:** Evita reprocessamento (construção pode levar minutos em bases grandes)

**Quando regenerar:**

```bash
# Exclua o arquivo de cache para forçar reconstrução
rm grafo_direcional.pkl
python main.py
```

---

## 📊 Exemplo de Uso

### Cenário: Rota com 1 Integração

```
Origem: Parada 2466
Destino: Parada 2475

Linhas disponíveis em 2466:
- 504.1 - IDA
- 602.1 - IDA
- 603.1 - IDA

Linhas disponíveis em 2475:
- 630.1 - IDA
- 602.1 - IDA
```

**Resultado:**

```
📍 PERCURSO:
   Parada 2466 → Linha [602.1 - IDA] → Parada 2470
   Parada 2470 → Linha [602.1 - IDA] → Parada 2475

📊 RESUMO:
   • Total de paradas: 3
   • Linhas utilizadas: 1
   • Integrações: 0
   • Linhas: 602.1 - IDA
```

### Cenário: Nenhum Caminho Encontrado

```
Origem: Parada 9999
Destino: Parada 1000

============================================================
✗ NENHUM CAMINHO ENCONTRADO
============================================================

Possíveis motivos:
  • As paradas não estão conectadas
  • Não há linha que conecte origem e destino
  • IDs de paradas inválidos
```

---

## 🛠️ Tratamento de Erros

### Erros Comuns e Soluções

| Erro | Causa | Solução |
|------|-------|---------|
| `FileNotFoundError: paradas_linhas_2025.db` | Banco de dados não encontrado | Verifique se o arquivo está no diretório correto |
| `ValueError: invalid literal for int()` | ID de parada inválido | Digite apenas números inteiros |
| `KeyError: linha não encontrada` | Linha sem sequência cadastrada | Verifique se `linhas_onibus.db` está completo |
| Grafo vazio após processamento | Formato incorreto das paradas em `linhas_onibus.db` | Verifique formato: "2466,2467,2468" |

### Debug: Verificar Dados

```python
# Adicione no main.py para debug
print("Amostra de linhas_de_onibus:")
for parada, linhas in list(linhas_de_onibus.items())[:5]:
    print(f"  Parada {parada}: {linhas}")

print("\nAmostra de sequencias:")
for linha, paradas in list(sequencias.items())[:5]:
    print(f"  {linha}: {paradas[:10]}...")  # Primeiras 10 paradas
```

---

## 🔧 Configurações Avançadas

### Modificar Heurística

Para rotas geograficamente distribuídas, considere usar coordenadas GPS:

```python
# a_star.py
import math

def heuristica(parada_atual, destino, coordenadas):
    """Heurística baseada em distância euclidiana"""
    x1, y1 = coordenadas[parada_atual]
    x2, y2 = coordenadas[destino]
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
```

### Priorizar Menos Integrações

Modifique o custo para penalizar trocas de linha:

```python
# a_star.py
PENALIDADE_INTEGRACAO = 5

# No loop do A*
custo_integracao = 0
if len(caminho) > 0 and caminho[-1] != linha:
    custo_integracao = PENALIDADE_INTEGRACAO

custo_estimado = custo + 1 + custo_integracao + heuristica(vizinho, destino)
```

---

## 📝 Notas Técnicas

### Complexidade

- **Construção do grafo:** O(P² × L) onde P = paradas, L = linhas médias por parada
- **Validação direcional:** O(E × S) onde E = arestas, S = tamanho médio das sequências
- **Busca A*:** O(E × log(V)) onde V = vértices, E = arestas

### Memória

- Grafo armazenado: ~50-200 MB para 5000-10000 paradas
- Recomenda-se mínimo 512 MB RAM disponível

### Performance

| Operação | Tempo Estimado |
|----------|----------------|
| Construção inicial | 30s - 2min |
| Validação direcional | 10s - 30s |
| Carregamento do cache | < 1s |
| Busca de rota (A*) | < 0.1s |

---

## 📄 Licença

Este projeto é de código aberto. Sinta-se livre para modificar e distribuir.

---

## 👥 Contribuindo

Melhorias sugeridas:

- [ ] Adicionar suporte a horários de operação das linhas
- [ ] Implementar busca por múltiplas rotas alternativas
- [ ] Interface web com mapa interativo
- [ ] API REST para integração com outros sistemas
- [ ] Considerar tempo de espera entre ônibus
- [ ] Calcular tempo estimado de viagem

---

## 📞 Suporte

Para dúvidas ou problemas:

1. Verifique a seção [Tratamento de Erros](#tratamento-de-erros)
2. Execute com modo debug ativado
3. Verifique a integridade dos bancos de dados

**Desenvolvido com ❤️ para sistemas de transporte público mais eficientes**