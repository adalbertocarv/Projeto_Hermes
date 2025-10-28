# API GeoJSON para SQLite com Algoritmo A* para Busca Rápida Espacial

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/adalbertocarv/Projeto_Hermes)

Este repositório oferece uma API de alta performance, desenvolvida com **FastAPI**, que converte dados **GeoJSON** em um banco de dados local **SQLite** e permite consultas rápidas de dados espaciais. A API suporta a busca de múltiplos `codDftrans` e retorna os resultados no formato **GeoJSON**, facilitando a integração com ferramentas de mapeamento.

## Hermes - Protetor dos viajantes: Ajudava viajantes, pastores e condutores de rebanhos, além de guiar as almas dos mortos para o submundo. 
### Principais Funcionalidades:
- **Busca Rápida**: Consultas otimizadas com SQLite garantem uma recuperação de dados geoespaciais de forma extremamente rápida, mesmo com grandes volumes de dados.
- **Implementação do Algoritmo A***: Inclui a implementação do algoritmo de busca A* (A-star) para calcular o caminho mais curto entre dois pontos geoespaciais, aprimorando a pesquisa e otimização de rotas.
- **Suporte a Múltiplas Consultas**: Permite a consulta de múltiplos pontos de parada ou locais geoespaciais ao mesmo tempo, retornando os resultados como uma `FeatureCollection` no formato GeoJSON.
- **Saída em GeoJSON**: Todos os dados são retornados no formato padrão GeoJSON, facilitando a integração com sistemas GIS ou aplicações de mapeamento.

Este projeto é ideal para sistemas de transporte, soluções de mapeamento ou qualquer aplicação que necessite de consultas geoespaciais rápidas e eficientes, combinadas com algoritmos poderosos de busca de rotas.

##  Acessando a Documentação

### Instalação e Execução da Documentação

1. **Instale o MkDocs e o tema Material**:
```bash
pip install mkdocs mkdocs-material
```

2. **Execute a documentação localmente**:
```bash
python -m mkdocs serve
```

3. **Acesse no navegador**:
```
http://localhost:8000
```

### Estrutura da Documentação
- **Home**: Visão geral do projeto
- **API**: Documentação completa dos endpoints
- **Consultas**: Exemplos e guias de consulta ao banco
- **Funcionalidades**: Detalhes de todas as features
- **Estrutura de Dados**: Modelagem do banco e esquemas

# Arquitetura do projeto:
![image](https://github.com/user-attachments/assets/0e7fc15c-04bc-4e11-bf49-2518e14e3a2e)

---

