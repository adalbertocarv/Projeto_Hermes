
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/adalbertocarv/Projeto_Hermes)

Este repositório oferece uma API de alta performance, desenvolvida com **FastAPI**, que converte dados **GeoJSON** em um banco de dados local **SQLite** e permite consultas rápidas de dados espaciais. A API suporta a busca de múltiplos `codDftrans` e retorna os resultados no formato **GeoJSON**, facilitando a integração com ferramentas de mapeamento.
## Hermes - Protetor dos viajantes: Ajudava viajantes, pastores e condutores de rebanhos, além de guiar as almas dos mortos para o submundo. 
### Principais Funcionalidades:
- **Busca Rápida**: Consultas otimizadas com SQLite garantem uma recuperação de dados geoespaciais de forma extremamente rápida, mesmo com grandes volumes de dados.
- **Implementação do Algoritmo A***: Inclui a implementação do algoritmo de busca A* (A-star) para calcular o caminho mais curto entre dois pontos geoespaciais, aprimorando a pesquisa e otimização de rotas.
- **Suporte a Múltiplas Consultas**: Permite a consulta de múltiplos pontos de parada ou locais geoespaciais ao mesmo tempo, retornando os resultados como uma `FeatureCollection` no formato GeoJSON.
- **Saída em GeoJSON**: Todos os dados são retornados no formato padrão GeoJSON, facilitando a integração com sistemas GIS ou aplicações de mapeamento.

Este projeto é ideal para sistemas de transporte, soluções de mapeamento ou qualquer aplicação que necessite de consultas geoespaciais rápidas e eficientes, combinadas com algoritmos poderosos de busca de rotas.

# Arquitetura do projeto:
![image](https://github.com/user-attachments/assets/0e7fc15c-04bc-4e11-bf49-2518e14e3a2e)# API GeoJSON para SQLite com Algoritmo A* para Busca Rápida Espacial
<div align="center">
<img src="[https://private-user-images.githubusercontent.com/107323618/378978982-ebc87bf6-3c7f-4c19-a75a-dd7585c31c32.jpg?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3Mjk4ODE3NTcsIm5iZiI6MTcyOTg4MTQ1NywicGF0aCI6Ii8xMDczMjM2MTgvMzc4OTc4OTgyLWViYzg3YmY2LTNjN2YtNGMxOS1hNzVhLWRkNzU4NWMzMWMzMi5qcGc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjQxMDI1JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI0MTAyNVQxODM3MzdaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT1kN2E2NTFkZjJhOTFhMjBlZmM3N2Y1NDAyODMzMWUwMGIxN2I5MDM2M2Q2NWFjMjBjNmU0Y2VkMWE4M2E1NWIwJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.zuPPZ3ExTRNGR48Jf00D6BJLEGfx7dFcUpMs2vfXqkw](https://private-user-images.githubusercontent.com/107323618/378978982-ebc87bf6-3c7f-4c19-a75a-dd7585c31c32.jpg?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MzAyMTA4MzAsIm5iZiI6MTczMDIxMDUzMCwicGF0aCI6Ii8xMDczMjM2MTgvMzc4OTc4OTgyLWViYzg3YmY2LTNjN2YtNGMxOS1hNzVhLWRkNzU4NWMzMWMzMi5qcGc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjQxMDI5JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI0MTAyOVQxNDAyMTBaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT1hMTJkMTViN2U2OWRjMTBkYWI3NDM5Y2RhYTZiNmE3ODA0Y2YzNTQ0YzBmMDE0ODllZjJjMDA3NzU2ZDM1NjViJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.PrlzBsZIyFhU-1ZRMg6mMWVdKH8G0tAVX2O3VDg9YPk)" width="700px" />
</div>
