import sys
import copy
from consts import Tiles, TILES

# Nos de uma arvore de pesquisa, state - mapa atual, parent - node anterior, key - tecla do parent para a node
class SearchNode:
    def __init__(self,state,parent, key): 
        self.state = state
        self.parent = parent
        self.key = key

    def __str__(self):
        return "no(" + str(self.state) + "," + str(self.parent) + ")"
    def __repr__(self):
        return str(self)

# Arvore de pesquisa
# ideia - ter um objeto mapa inicial e ir testando todos os mapas possiveis
class SearchTree:

    # construtor
    def __init__(self, initial_map):
        root = SearchNode(initial_map, None, None)
        self.open_nodes = [root]

    # obter o caminho (de teclas) da raiz ate um no
    def get_path(self,node):
        if node.parent == None:
            return []
        path = self.get_path(node.parent)
        path += [node.key]
        return(path)
    
    # obter o caminho da raiz ate um no
    def get_path_str(self,node):
        if node.parent == None:
            return [str(node.state._map)]
        path = self.get_path(node.parent)
        path += [str(node.state._map)]
        return(path)

    # procurar a solucao
    def search(self, limit=None):
        while self.open_nodes != []:
            node = self.open_nodes.pop(0)

            #se cheguei a solucao
            if node.state.completed:
                return self.get_path(node)

            #como nao cheguei tenho de obter uma lista de possiveis caminhos
            options = {"d":[1, 0], "a":[-1, 0], "s":[0, 1], "w":[0, -1]}

            for key, option in options.items():
                newmap = self.newmap(node, option)
                if newmap != None and str(newmap._map) not in self.get_path_str(node):
                    #calcular como fica o novo mapa com esse movimento
                    self.open_nodes.append(SearchNode(newmap, node, key))

        return None
    
    #retorna um novo mapa caso seja um movimento possivel, senao retorna None
    def newmap(self, node, movement):
        keeper_coor = node.state.keeper

        #verificar se esta a ir contra uma parede
        if node.state.is_blocked([keeper_coor[0]+movement[0], keeper_coor[1]+movement[1]]) or node.state.get_tile([keeper_coor[0]+movement[0], keeper_coor[1]+movement[1]]) == "#":
            return None
        
        if [keeper_coor[0]+movement[0], keeper_coor[1]+movement[1]] in node.state.boxes:
            if node.state.is_blocked([keeper_coor[0]+movement[0]*2, keeper_coor[1]+movement[1]*2]) or node.state.get_tile([keeper_coor[0]+movement[0]*2, keeper_coor[1]+movement[1]*2]) not in ['-', '.']:
                return None
            else:
                hitBox = True
        else:
            hitBox = False

        newmap = copy.deepcopy(node.state)

        if hitBox:
            tile = newmap.get_tile((keeper_coor[0]+movement[0], keeper_coor[1]+movement[1]))
            newmap.clear_tile((keeper_coor[0]+movement[0], keeper_coor[1]+movement[1]))
            newmap.set_tile((keeper_coor[0]+movement[0]*2, keeper_coor[1]+movement[1]*2), tile)

        tile = newmap.get_tile(keeper_coor)
        newmap.clear_tile(keeper_coor)
        newmap.set_tile((keeper_coor[0]+movement[0], keeper_coor[1]+movement[1]), tile)

        return newmap
