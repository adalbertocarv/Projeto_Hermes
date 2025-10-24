from database import carregar_dados_com_geolocalizacao
from graph import construir_grafo_completo, aplicar_direcionalidade
from a_star import encontrar_caminho_com_caminhadas, encontrar_linha_mais_direta, formatar_caminho
from utils import salvar_grafo, carregar_grafo
import time

def main():
    caminho_arquivo_grafo = 'grafo.pkl'
    
    print("=" * 60)
    print("🚀 SISTEMA DE BUSCA DE ROTAS COM CAMINHADAS")
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
                    print(f"✅ LINHA DIRETA: {linha_direta} ({num_paradas} paradas)")
            
            # Busca com caminhadas
            print("🔄 Buscando rota (considerando caminhadas)...")
            start_time = time.time()
            
            caminho = encontrar_caminho_com_caminhadas(grafo, coordenadas_paradas, origem, destino)
            end_time = time.time()
            
            if caminho:
                print(f"\n✅ ROTA ENCONTRADA ({end_time - start_time:.2f}s)")
                print("=" * 50)
                print(formatar_caminho(caminho))
                print("=" * 50)
            else:
                print("\n❌ Nenhum caminho encontrado")
                
        except ValueError:
            print("❌ Digite apenas números")
        except KeyboardInterrupt:
            print("\n👋 Saindo...")
            break

if __name__ == "__main__":
    main()