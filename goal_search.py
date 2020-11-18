import copy
from consts import Tiles, TILES
import asyncio
from agent_search import SearchAgent

# No de uma arvore de pesquisa
class SearchNode:
    def __init__(self, state, boxes, parent, key, depth, cost, heuristic): 
        self.state = state #mapa
        self.boxes = boxes #coordenadas das caixas
        self.parent = parent
        self.keys = key
        self.depth = depth
        self.cost = cost
        self.heuristic = heuristic

    def __str__(self):
        return "no(" + str(self.state) + "," + str(self.parent) + ")"
    def __repr__(self):
        return str(self)

# Arvore de pesquisa
class SearchTree:

    # construtor
    def __init__(self, mapa):
        self.root = SearchNode(mapa, [list(tup) for tup in mapa.boxes], None, "", 0, 0, None)
        self.open_nodes = [self.root]

    # obter o caminho (de teclas) da raiz ate um no
    def get_path(self,node):
        if node.parent == None:
            return node.keys
        else:
            return self.get_path(node.parent) + node.keys
    
    # obter o caminho da raiz ate um no
    def get_path_str(self,node):
        if node.parent == None:
            return [node.state.__str__()]
        path = self.get_path_str(node.parent)
        path += [node.state.__str__()]
        return(path)
    
    # calculo da heuristica
    def heuristic(self, map):
        boxes_coor = map.boxes

        goals_coor = map.empty_goals

        if len(goals_coor) == 0:
            return 0

        h = 1
        for box in boxes_coor:
            for goal in goals_coor:
                h += abs(box[0]-goal[0]) + abs(box[1]-goal[1])
        
        return h

    # procurar a solucao
    async def search(self, limit=None):
        #print("----- Beggining Search -----\n")
        count = 0
        while self.open_nodes != []:
            node = self.open_nodes.pop(0)
            count+=1
            print(count)
            #print(node.state)

            #se cheguei a solucao
            if node.state.completed:
                self.solution = self.get_path(node)
                #print(self.node.keys)
                print("Cheguei à solução")
                return None

            await asyncio.sleep(0) # this should be 0 in your code and this is REQUIRED

            #como nao cheguei tenho de obter uma lista de possiveis movimentos das caixas
            options = dict()
            for i in range(len(node.boxes)):
                options[(i, "d")] = [1, 0]
                options[(i, "a")] = [-1, 0]
                options[(i, "s")] = [0, 1]
                options[(i, "w")] = [0, -1]

            for key, value in options.items():
                newnode = self.newNode(node, key[0], key[1], value)
                if newnode != None:
                    #print("----- Adding Node to Open Nodes -----\n")
                    #adicionar o novo Node à lista
                    self.open_nodes.append(newnode)
                    self.open_nodes.sort(key=lambda x: x.cost + x.heuristic)
                    #print(self.open_nodes)
        return None
    
    #retorna um novo mapa caso seja um movimento possivel, senao retorna None
    def newNode(self, node, box_id, key, movement):
        box = node.boxes[box_id]

        #verificar se esta a ir contra uma parede ou caixa e verificar se o lugar do keeper esta vazio
        newTile = node.state.get_tile([box[0]+movement[0], box[1]+movement[1]]).name
        keeperTile = node.state.get_tile([box[0]-movement[0], box[1]-movement[1]]).name
        #print("keeper: ", keeperTile)
        #print("newTile: ", newTile)
        #print(not all([tile not in [TILES["#"].name, TILES["$"].name, TILES["*"].name] for tile in [keeperTile, newTile]]))

        if not all([tile not in [TILES["#"].name, TILES["$"].name, TILES["*"].name] for tile in [keeperTile, newTile]]):
            return None
        
        #print("----- Calling Search Agent -----\n")
        #verificar se ha um caminho para o keeper
        agentSearch = SearchAgent(node.state, (box[0]-movement[0], box[1]-movement[1]))
        keys = agentSearch.search()
        
        if keys == None:
            return None

        #fazer uma copia do mapa e das coordenadas das caixas e atualizar ambos -> simular movimento
        newmap = agentSearch.solution
        boxes = copy.deepcopy(node.boxes)

        boxes[box_id][0] += movement[0]
        boxes[box_id][1] += movement[1]

        # Mover a caixa...
        tile = newmap.get_tile(box)
        #print("\n", newmap, "\n")
        newmap.clear_tile(box)
        #print(box)
        #print(movement)
        #print(tile)
        newmap.set_tile(( boxes[box_id][0], boxes[box_id][1] ), tile)

        # Mover o keeper...
        keeperCoord = newmap.keeper
        tile = newmap.get_tile(keeperCoord)
        newmap.clear_tile(keeperCoord)
        newmap.set_tile(box, tile)


        #provavelmente preciso de mudar a posicao do keeper, maybe receber mapa do AgentSearch
        #print(newmap)
        if newmap.__str__() in self.get_path_str(node):
            return None

        newnode = SearchNode(newmap, boxes, node, keys+key, node.depth+1, node.cost+1, self.heuristic(newmap))
        #print(self.get_path(newnode))
        return newnode
