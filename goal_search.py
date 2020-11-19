import copy
from consts import Tiles, TILES
import asyncio
from agent_search import SearchAgent

# No de uma arvore de pesquisa
class SearchNode:
    def __init__(self, state, parent, key, depth, cost, heuristic): 
        self.state = state #mapa
        self.parent = parent
        self.keys = key
        self.depth = depth
        self.cost = cost
        self.heuristic = heuristic
    
    def findBoxes(self):
        l = []
        for i in range(self.state.size[0]):
            for j in range(self.state.size[1]):
                if self.state.get_tile((i,j)).name in [TILES["$"].name, TILES["*"].name]:
                    #print(self.state.get_tile((i,j)).name)
                    l.append((i,j))
        return l


    def __str__(self):
        return "no(" + str(self.state) + "," + str(self.parent) + ")"

    def __repr__(self):
        return str(self)

# Arvore de pesquisa
class SearchTree:

    # construtor
    def __init__(self, mapa):
        self.root = SearchNode(mapa, None, "", 0, 0, None)
        self.open_nodes = [self.root]
        #print(mapa._map)

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
    
    def isCornered(self, mapa):
        boxesPos = mapa.boxes
        # Positions = (Up, Down, Left Right)
        positions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        #print(boxesPos)
        for boxPos in boxesPos:
            # If the box is on goal, it is not considered a cornered box since it could be part of the solution
            if mapa.get_tile(boxPos) == Tiles.BOX_ON_GOAL:
                return False
            #print(box)

            box_upPos = mapa.get_tile( tuple(map( lambda t1, t2: t1 + t2, boxPos, positions[0] )) )
            box_downPos = mapa.get_tile( tuple(map( lambda t1, t2: t1 + t2, boxPos, positions[1] )) )
            box_leftPos = mapa.get_tile( tuple(map( lambda t1, t2: t1 + t2, boxPos, positions[2] )) )
            box_rightPos = mapa.get_tile( tuple(map( lambda t1, t2: t1 + t2, boxPos, positions[3] )) )

            if (box_leftPos == Tiles.WALL) and (box_upPos == Tiles.WALL):
                return True
            if (box_upPos == Tiles.WALL) and (box_rightPos == Tiles.WALL):
                return True
            if (box_rightPos == Tiles.WALL) and (box_downPos == Tiles.WALL):
                return True
            if (box_downPos == Tiles.WALL) and (box_leftPos == Tiles.WALL):
                return True
        return False

    # procurar a solucao
    async def search(self, limit=None):
        #print("----- Beggining Box Search -----\n")
        count = 0
        while self.open_nodes != []:
            node = self.open_nodes.pop(0)
            count+=1
            #print(count)

            #se cheguei a solucao
            if node.state.completed:
                self.solution = self.get_path(node)
                print(self.solution)
                print("Number of attempts: ", count, "\n")
                #print("----- Box Search Done -----\n")
                return None

            await asyncio.sleep(0) # this should be 0 in your code and this is REQUIRED

            #como nao cheguei tenho de obter uma lista de possiveis movimentos das caixas
            options = dict()
            for box in node.findBoxes():
                options[(box, "d")] = (1, 0)
                options[(box, "a")] = (-1, 0)
                options[(box, "s")] = (0, 1)
                options[(box, "w")] = (0, -1)

            #print(node.state)
            #print()
            for key, value in options.items():
                

                newnode = self.newNode(node, key[0], key[1], value)
                if newnode != None:
                    #print("acepted")
                    #adicionar o novo Node à lista
                    self.open_nodes.append(newnode)
                    self.open_nodes.sort(key=lambda x: x.cost + x.heuristic)
                    #print(self.open_nodes)
                #else:
                    #print()
                    #print("rejected")
                    #print(node.state)
                    #print(key[0])
                    #print(value)
                    #print()
            #print(node.state)
            #print()

        #print("----- Box Search Failed -----\n")
        return None
    
    #retorna um novo mapa caso seja um movimento possivel, senao retorna None
    def newNode(self, node, box, key, movement):
        #verificar se esta a ir contra uma parede ou caixa e verificar se o lugar do keeper esta vazio
        newTile = node.state.get_tile([box[0]+movement[0], box[1]+movement[1]]).name
        keeperTile = node.state.get_tile([box[0]-movement[0], box[1]-movement[1]]).name
        #print("keeper: ", keeperTile)
        #print("newTile: ", newTile)
        #print([TILES["#"].name, TILES["$"].name, TILES["*"].name])

        if any([tile in [TILES["#"].name, TILES["$"].name, TILES["*"].name] for tile in [keeperTile, newTile]]):
            #print("-----------")
            #print(newTile)
            #print(keeperTile)
            #print("---------------")
            return None
        
        #print("----- Calling Search Agent -----\n")
        #verificar se ha um caminho para o keeper
        agentSearch = SearchAgent(node.state, (box[0]-movement[0], box[1]-movement[1]))
        keys = agentSearch.search()
        
        if keys == None:
            #print(node.state)
            #print(box)
            #print(movement)
            return None

        #fazer uma copia do mapa e das coordenadas das caixas e atualizar ambos -> simular movimento
        newmap = copy.deepcopy(agentSearch.solution)

        #print(node.state) #aqui o node é diferente do print debaixo quando apenas mudamos no newmap
        #print(newmap)
        #print()
        # Mover a caixa...
        tile = newmap.get_tile(box)
        newmap.set_tile([box[0]+movement[0], box[1]+movement[1]], tile)
        #print("\n", newmap, "\n")
        newmap.clear_tile(box)
        #print(box)
        #print(movement)
        #print(tile)
        #print(node.state)
        #print(newmap)
        #print()

        # Mover o keeper...
        keeperCoord = newmap.keeper
        tile = newmap.get_tile(keeperCoord)
        newmap.clear_tile(keeperCoord)
        newmap.set_tile(box, tile)

        #print(newmap)
        if newmap.__str__() in self.get_path_str(node):
            return None
        if self.isCornered(newmap):
            return None

        newnode = SearchNode(newmap, node, keys+key, node.depth+1, node.cost+1, self.heuristic(newmap))
        #print(self.get_path(newnode))
        return newnode
