from database import carregar_dados_com_geolocalizacao
from graph import construir_grafo_completo, aplicar_direcionalidade
from a_star import encontrar_multiplos_caminhos, encontrar_linha_mais_direta, formatar_multiplos_caminhos, formatar_analise_detalhada
from utils import salvar_grafo, carregar_grafo
import time

def main():
    caminho_arquivo_grafo = 'grafo.pkl'
    
    print("=" * 60)
    print("🚀 SISTEMA DE BUSCA DE ROTAS COM CAMINHADAS")
    print("🎯 AGORA COM MÚLTIPLAS ROTAS ORDENADAS")
    print("=" * 60)
    
    # Carrega grafo existente ou constrói novo
    print("📂 Carregando dados...")
    grafo = carregar_grafo(caminho_arquivo_grafo)
    
    # SEMPRE carrega dados geográficos
    paradas, linhas_por_parada, sequencias, linhas_info, coordenadas_paradas = carregar_dados_com_geolocalizacao()
    
    if grafo is None:
        print("🔄 Construindo novo grafo direcional...")
        start_time = time.time()
        
        if not paradas:
            print("❌ Erro: Não foi possível carregar dados do banco.")
            return
        
        grafo_completo = construir_grafo_completo(paradas, linhas_por_parada)
        grafo = aplicar_direcionalidade(grafo_completo, sequencias)
        salvar_grafo(grafo, caminho_arquivo_grafo)
        
        end_time = time.time()
        print(f"✅ Grafo criado em {end_time - start_time:.2f} segundos")
    else:
        print("✅ Grafo carregado do arquivo")
    
    print(f"🗺️  {len(coordenadas_paradas)} paradas com coordenadas disponíveis")
    
    # Interface de busca
    while True:
        try:
            print("\n" + "-" * 40)
            origem = int(input("Digite a parada de origem: "))
            destino = int(input("Digite a parada de destino: "))
            
            # Verificações
            if origem not in grafo and origem not in coordenadas_paradas:
                print(f"❌ Parada {origem} não encontrada.")
                continue
            if destino not in grafo and destino not in coordenadas_paradas:
                print(f"❌ Parada {destino} não encontrada.")
                continue
            if origem == destino:
                print("❌ Origem e destino iguais.")
                continue
            
            # Verifica linha direta
            if origem in grafo:
                linha_direta, num_paradas = encontrar_linha_mais_direta(grafo, sequencias, origem, destino)
                if linha_direta:
                    print(f"✅ LINHA DIRETA ENCONTRADA: {linha_direta} ({num_paradas} paradas)")
            
            # Busca múltiplos caminhos com caminhadas
            print("🔄 Buscando múltiplas rotas (considerando caminhadas)...")
            start_time = time.time()
            
            caminhos = encontrar_multiplos_caminhos(grafo, coordenadas_paradas, origem, destino, max_caminhos=3)
            end_time = time.time()
            
            if caminhos:
                print(f"\n✅ {len(caminhos)} ROTAS ENCONTRADAS ({end_time - start_time:.2f}s)")
                print(formatar_multiplos_caminhos(caminhos))
                print("=" * 60)
                
                # Oferece opção para ver mais detalhes
                if len(caminhos) > 1:
                    try:
                        escolha = input("\nDeseja ver detalhes de uma rota específica? (1-{} ou Enter para continuar): ".format(len(caminhos)))
                        if escolha.isdigit() and 1 <= int(escolha) <= len(caminhos):
                            rota_escolhida = caminhos[int(escolha)-1]
                            print(formatar_analise_detalhada(rota_escolhida, escolha))
                    except:
                        pass
            else:
                print("\n❌ Nenhum caminho encontrado")
                
        except ValueError:
            print("❌ Digite apenas números")
        except KeyboardInterrupt:
            print("\n👋 Saindo...")
            break

if __name__ == "__main__":
    main()