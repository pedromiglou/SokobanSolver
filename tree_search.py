import sys
import copy
from consts import Tiles, TILES
import math
import asyncio

# Nos de uma arvore de pesquisa, state - mapa atual, parent - node anterior, key - tecla do parent para a node
class SearchNode:
    def __init__(self,state,parent, key, depth, cost, heuristic): 
        self.state = state
        self.parent = parent
        self.key = key
        self.depth = depth
        self.cost = cost
        self.heuristic = heuristic

    def __str__(self):
        return "no(" + str(self.state) + "," + str(self.parent) + ")"
    def __repr__(self):
        return str(self)

# Arvore de pesquisa
# ideia - ter um objeto mapa inicial e ir testando todos os mapas possiveis
class SearchTree:

    # construtor
    def __init__(self, initial_map):
        root = SearchNode(initial_map, None, None, 0, 0, self.heuristic(initial_map))
        self.open_nodes = [root]

    # obter o caminho (de teclas) da raiz ate um no
    def get_path(self,node):
        if node.parent == None:
            return ""
        path = self.get_path(node.parent)
        path += node.key
        return(path)
    
    # obter o caminho da raiz ate um no
    def get_path_str(self,node):
        if node.parent == None:
            return [node.state.__str__]
        path = self.get_path_str(node.parent)
        path += [node.state.__str__]
        return(path)
    
    def heuristic(self, map):
        #heuristica muito baixa para ser logo escolhido o mapa
        if map.completed:
            return -1000
        
        #tentativa de heuristica com a distancia do keeper as boxes
        keeper_coor = map.keeper

        boxes_coor = map.boxes

        return min([math.sqrt(pow(keeper_coor[0]-box[0],2) + pow(keeper_coor[1]-box[1],2)) for box in boxes_coor])

    # procurar a solucao
    async def search(self, limit=None):
        while self.open_nodes != []:
            node = self.open_nodes.pop(0)

            #se cheguei a solucao
            if node.state.completed:
                self.solution = self.get_path(node)
                return None

            await asyncio.sleep(0) # this should be 0 in your code and this is REQUIRED 
            #como nao cheguei tenho de obter uma lista de possiveis caminhos
            options = {"d":[1, 0], "a":[-1, 0], "s":[0, 1], "w":[0, -1]}

            for key, option in options.items():
                newmap = self.newmap(node, option)
                if newmap != None and newmap.__str__() not in self.get_path_str(node):
                    #calcular como fica o novo mapa com esse movimento
                    self.open_nodes.append(SearchNode(newmap, node, key, node.depth+1, node.cost+1, self.heuristic(newmap)))
                    self.open_nodes.sort(key=lambda x: x.cost + x.heuristic)

        return None
    
    #retorna um novo mapa caso seja um movimento possivel, senao retorna None
    def newmap(self, node, movement):
        keeper_coor = node.state.keeper

        #verificar se esta a ir contra uma parede
        # if node.state.is_blocked([keeper_coor[0]+movement[0], keeper_coor[1]+movement[1]]) or
        if node.state.get_tile([keeper_coor[0]+movement[0], keeper_coor[1]+movement[1]]).name == TILES["#"].name:
            return None
        
        #verificar se o tile depois do bloco esta vazio
        if (keeper_coor[0]+movement[0], keeper_coor[1]+movement[1]) in node.state.boxes:
            #if node.state.is_blocked([keeper_coor[0]+movement[0]*2, keeper_coor[1]+movement[1]*2]) or 
            if node.state.get_tile([keeper_coor[0]+movement[0]*2, keeper_coor[1]+movement[1]*2]).name not in [TILES['-'].name, TILES['.'].name]:
                return None
            else:
                hitBox = True
        else:
            hitBox = False

        newmap = copy.deepcopy(node.state)

        #print("newmap1")
        #print(movement)
        #print(newmap.__str__())

        if hitBox:
            tile = newmap.get_tile((keeper_coor[0]+movement[0], keeper_coor[1]+movement[1]))
            newmap.clear_tile((keeper_coor[0]+movement[0], keeper_coor[1]+movement[1]))
            newmap.set_tile((keeper_coor[0]+movement[0]*2, keeper_coor[1]+movement[1]*2), tile)

        tile = newmap.get_tile(keeper_coor)
        newmap.clear_tile(keeper_coor)

        newmap.set_tile((keeper_coor[0]+movement[0], keeper_coor[1]+movement[1]), tile)

        #print("newmap2")
        #print(movement)
        #print(newmap.__str__())

        return newmap
