from database import carregar_dados_bd, carregar_sequencias_linhas
from graph import construir_grafo, aplicar_direcionalidade
from a_star import encontrar_caminho_com_integracao_astar
from utils import salvar_grafo, carregar_grafo

def main():
    caminho_bd_paradas = 'paradas_linhas_2025.db'
    caminho_bd_linhas = 'linhas_onibus.db'
    caminho_arquivo_grafo = 'grafo_direcional.pkl'
    
    # Tenta carregar grafo já processado
    grafo = carregar_grafo(caminho_arquivo_grafo)
    
    if grafo is None:
        print("\n=== Construindo grafo direcional ===")
        
        # Etapa 1: Carregar dados das paradas
        print("\n[1/4] Carregando paradas e linhas...")
        paradas, linhas_de_onibus = carregar_dados_bd(caminho_bd_paradas)
        print(f"  ✓ {len(paradas)} paradas carregadas")
        
        # Etapa 2: Construir grafo inicial (não-direcional)
        print("\n[2/4] Construindo grafo inicial...")
        grafo_inicial = construir_grafo(paradas, linhas_de_onibus)
        total_conexoes = sum(len(v) for v in grafo_inicial.values())
        print(f"  ✓ {total_conexoes} conexões criadas")
        
        # Etapa 3: Carregar sequências das linhas
        print("\n[3/4] Carregando sequências das linhas...")
        sequencias = carregar_sequencias_linhas(caminho_bd_linhas)
        print(f"  ✓ {len(sequencias)} linhas com sequências carregadas")
        
        # Etapa 4: Aplicar direcionalidade
        print("\n[4/4] Aplicando direcionalidade ao grafo...")
        grafo = aplicar_direcionalidade(grafo_inicial, sequencias)
        
        # Salvar grafo processado
        salvar_grafo(grafo, caminho_arquivo_grafo)
        print("\n✓ Grafo direcional construído com sucesso!")
        
    else:
        print("✓ Grafo direcional carregado do arquivo.")
    
    # Loop de consultas
    print("\n" + "=" * 60)
    print("       SISTEMA DE ROTAS DE ÔNIBUS - BUSCA DE CAMINHOS")
    print("=" * 60)
    
    while True:
        try:
            print("\n" + "-" * 60)
            origem = input("Digite a parada de origem (ou 'sair' para encerrar): ")
            
            if origem.lower() in ['sair', 'exit', 'q', '0']:
                print("\nEncerrando sistema...")
                break
            
            origem = int(origem)
            destino = int(input("Digite a parada de destino: "))
            
            print("\nBuscando rota...")
            caminho = encontrar_caminho_com_integracao_astar(grafo, origem, destino)
            
            if caminho:
                print("\n" + "=" * 60)
                print("✓ CAMINHO ENCONTRADO")
                print("=" * 60)
                
                # Exibe o percurso completo
                print("\n📍 PERCURSO:")
                for i in range(0, len(caminho) - 1, 2):
                    if i + 2 < len(caminho):
                        print(f"   Parada {caminho[i]} → Linha [{caminho[i + 1]}] → Parada {caminho[i + 2]}")
                
                # Identifica pontos de integração (mudança de linha)
                integracoes = []
                linhas_usadas = []
                
                for i in range(1, len(caminho), 2):
                    linha_atual = caminho[i]
                    if linha_atual not in linhas_usadas:
                        linhas_usadas.append(linha_atual)
                    
                    # Verifica se há mudança de linha
                    if i > 1 and i + 1 < len(caminho):
                        linha_anterior = caminho[i - 2]
                        if linha_atual != linha_anterior:
                            integracoes.append((caminho[i - 1], linha_anterior, linha_atual))
                
                # Exibe integrações
                if integracoes:
                    print("\n🔄 INTEGRAÇÕES NECESSÁRIAS:")
                    for parada, linha_antiga, linha_nova in integracoes:
                        print(f"   Parada {parada}: {linha_antiga} → {linha_nova}")
                
                # Resumo
                print("\n📊 RESUMO:")
                print(f"   • Total de paradas: {len([p for i, p in enumerate(caminho) if i % 2 == 0])}")
                print(f"   • Linhas utilizadas: {len(linhas_usadas)}")
                print(f"   • Integrações: {len(integracoes)}")
                print(f"   • Linhas: {', '.join(linhas_usadas)}")
                
            else:
                print("\n" + "=" * 60)
                print("✗ NENHUM CAMINHO ENCONTRADO")
                print("=" * 60)
                print("\nPossíveis motivos:")
                print("  • As paradas não estão conectadas")
                print("  • Não há linha que conecte origem e destino")
                print("  • IDs de paradas inválidos")
                
        except ValueError:
            print("\n⚠ Erro: Digite apenas números válidos para os IDs das paradas.")
        except KeyboardInterrupt:
            print("\n\nEncerrando sistema...")
            break
        except Exception as e:
            print(f"\n⚠ Erro inesperado: {e}")

if __name__ == "__main__":
    main()