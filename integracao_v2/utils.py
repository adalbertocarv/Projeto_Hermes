import pickle
from collections import defaultdict

def salvar_grafo(grafo, caminho_arquivo):
    """Salva o grafo em arquivo pickle"""
    with open(caminho_arquivo, 'wb') as f:
        pickle.dump(dict(grafo), f)
    print(f"Grafo salvo em {caminho_arquivo}")


def carregar_grafo(caminho_arquivo):
    """Carrega o grafo de um arquivo pickle"""
    try:
        with open(caminho_arquivo, 'rb') as f:
            grafo = pickle.load(f)
        return defaultdict(list, grafo)
    except FileNotFoundError:
        return None
