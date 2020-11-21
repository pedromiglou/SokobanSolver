import copy
from consts import Tiles, TILES
import asyncio
from agent_search import SearchAgent

# No de uma arvore de pesquisa
class SearchNode:
    def __init__(self, state, parent, key, depth, cost, heuristic): 
        self.state = state #mapa
        self.reducedState = str(sorted(self.state.boxes)) + str(self.state.keeper)
        self.parent = parent
        self.keys = key
        self.depth = depth
        self.cost = cost
        self.heuristic = heuristic

    def __str__(self):
        return "no(" + str(self.state) + "," + str(self.parent) + ")"

    # def reduced_State(self):
    #    return str(sorted(self.state.boxes)) + str(self.state.keeper) #if self.reducedState == "" else self.reducedState

# Arvore de pesquisa
class SearchTree:

    # construtor
    def __init__(self, mapa):
        self.root = SearchNode(mapa, None, "", 0, 0, None)
        self.open_nodes = [self.root]

    # obter o caminho (de teclas) da raiz ate um no
    def get_path(self,node):
        if node.parent == None:
            return node.keys
        else:
            return self.get_path(node.parent) + node.keys
    
    # analisar se um estado anterior é igual ao atual
    def state_in_path(self, node, newstate):
        if node.reducedState == newstate:
            return True
        else:
            if node.parent != None:
                return self.state_in_path(node.parent, newstate)
            else:
                return False
    
    # calculo da heuristica
    def heuristic(self, map):
        boxes_coor = map.boxes
        goals_coor = map.empty_goals

        #if len(boxes_coor) > len(goals_coor):
        #    boxes_coor = [x for x in boxes_coor if map.get_tile(x) != Tiles.MAN_ON_GOAL]

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

        for boxPos in boxesPos:
            # If the box is on goal, it is not considered a cornered box since it could be part of the solution
            if mapa.get_tile(boxPos) == Tiles.BOX_ON_GOAL:
                return False

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
                return None

            await asyncio.sleep(0) # this should be 0 in your code and this is REQUIRED

            #como nao cheguei tenho de obter uma lista de possiveis movimentos das caixas
            options = dict()
            for box in node.state.boxes:
                options[(box, "d")] = (1, 0)
                options[(box, "a")] = (-1, 0)
                options[(box, "s")] = (0, 1)
                options[(box, "w")] = (0, -1)

            for key, movement in options.items():
                box = key[0]
                key = key[1]
                #verificar se esta a ir contra uma parede ou caixa e verificar se o lugar do keeper esta vazio
                newTile = node.state.get_tile([box[0]+movement[0], box[1]+movement[1]])
                keeperTile = node.state.get_tile([box[0]-movement[0], box[1]-movement[1]])

                if any([tile in [Tiles.BOX, Tiles.BOX_ON_GOAL, Tiles.WALL] for tile in [keeperTile, newTile]]):
                    continue

                #verificar se ha um caminho para o keeper
                agentSearch = SearchAgent(node.state, (box[0]-movement[0], box[1]-movement[1]))
                keys = await agentSearch.search()
                
                if keys == None:
                    continue

                #fazer uma copia do mapa e das coordenadas das caixas e atualizar ambos -> simular movimento
                newmap = copy.deepcopy(agentSearch.solution)

                # Mover a caixa...
                tile = newmap.get_tile(box)
                newmap.set_tile([box[0]+movement[0], box[1]+movement[1]], tile)
                newmap.clear_tile(box)

                # Mover o keeper...
                keeperCoord = newmap.keeper
                tile = newmap.get_tile(keeperCoord)
                newmap.clear_tile(keeperCoord)
                newmap.set_tile(box, tile)

                if self.state_in_path(node, str(sorted(newmap.boxes)) + str(newmap.keeper)):
                    continue
                if self.isCornered(newmap):
                    continue

                newnode = SearchNode(newmap, node, keys+key, node.depth+1, node.cost+len(node.state.boxes), self.heuristic(newmap))

                #encontrou um túnel
                #if movement[0] == 0: #andou em y
                #    if node.state.get_tile([box[0]+1, box[1]+movement[1]]) == Tiles.WALL and node.state.get_tile([box[0]-1, box[1]+movement[1]]) == Tiles.WALL:
                #        newnode.keys += newnode.keys[-1]
                #else:
                #    if node.state.get_tile([box[0]+movement[0], box[1]+1]) == Tiles.WALL and node.state.get_tile([box[0]+movement[0], box[1]-1]) == Tiles.WALL:
                #        newnode.keys += newnode.keys[-1]

                #adicionar o novo Node à lista
                self.open_nodes.append(newnode)
                self.open_nodes.sort(key=lambda x: x.cost + x.heuristic)

        print("----- Box Search Failed -----\n")
        return None
