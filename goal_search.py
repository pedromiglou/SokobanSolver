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
        self.defineWalls(mapa)

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
    
    def isCornered(self, mapa, boxPos):

        # If the box is on goal, it is not considered a cornered box since it could be part of the solution
        if mapa.get_tile(boxPos) == Tiles.BOX_ON_GOAL:
            return False
            
        # Positions = (Up, Down, Left Right)
        box_upPos = mapa.get_tile( tuple(map( lambda t1, t2: t1 + t2, boxPos, (0, -1) )) )
        box_downPos = mapa.get_tile( tuple(map( lambda t1, t2: t1 + t2, boxPos, (0, 1) )) )
        box_leftPos = mapa.get_tile( tuple(map( lambda t1, t2: t1 + t2, boxPos, (-1, 0) )) )
        box_rightPos = mapa.get_tile( tuple(map( lambda t1, t2: t1 + t2, boxPos, (1, 0) )) )

        if (box_leftPos == Tiles.WALL) and (box_upPos == Tiles.WALL):
            return True
        if (box_upPos == Tiles.WALL) and (box_rightPos == Tiles.WALL):
            return True
        if (box_rightPos == Tiles.WALL) and (box_downPos == Tiles.WALL):
            return True
        if (box_downPos == Tiles.WALL) and (box_leftPos == Tiles.WALL):
            return True

        return False

    def isWalled(self, mapa, boxPos):
        if not (self.leftBlock or self.upBlock or self.botBlock or self.rightBlock):
            return False

        dim = mapa.size

        # Check if the box position in a blocked wall
        if boxPos[0] == 1 and self.leftBlock:
            return True
        if boxPos[1] == 1 and self.upBlock:
            return True
        if boxPos[0] == (dim[0] - 2) and self.rightBlock:
            return True
        if boxPos[1] == (dim[1] - 2) and self.botBlock:
            return True

        return False
        

    def defineWalls(self, mapa):
        dim = mapa.size

        # All walls start out as blocked, meaning they don't have goals and the box should never reach them
        self.leftBlock = True
        self.upBlock = True
        self.rightBlock = True
        self.botBlock = True

        # If there is a goal on a certain border, that border will no longer be blocked
        for goalPos in mapa.filter_tiles([ Tiles.GOAL, Tiles.BOX_ON_GOAL, Tiles.MAN_ON_GOAL ]):
            if goalPos[0] == 1:
                self.leftBlock = False
            if goalPos[1] == 1:
                self.upBlock = False
            if goalPos[0] == (dim[0] - 2):
                self.rightBlock = False
            if goalPos[1] == (dim[1] - 2):
                self.botBlock = False

    # procurar a solucao
    async def search(self, limit=None):
        count = 0
        
        while self.open_nodes != []:
            node = self.open_nodes.pop(0)
            count+=1
            #print(count)detiuaveiro 

            #se cheguei a solucao
            if node.state.completed:
                self.solution = self.get_path(node)
                #print(self.solution)
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

                newBoxPos = (box[0]+movement[0], box[1]+movement[1])
                newKeeperPos = (box[0]-movement[0], box[1]-movement[1])

                #verificar se esta a ir contra uma parede ou caixa e verificar se o lugar do keeper esta vazio
                newTile = node.state.get_tile(newBoxPos)
                keeperTile = node.state.get_tile(newKeeperPos)

                if any([tile in [Tiles.BOX, Tiles.BOX_ON_GOAL, Tiles.WALL] for tile in [keeperTile, newTile]]):
                    continue

                #verificar se ha um caminho para o keeper
                agentSearch = SearchAgent(node.state, newKeeperPos)
                keys = await agentSearch.search()
                
                if keys == None:
                    continue

                #fazer uma copia do mapa e das coordenadas das caixas e atualizar ambos -> simular movimento
                newmap = copy.deepcopy(agentSearch.solution)

                # Mover a caixa...
                #tile = newmap.get_tile(box)
                newmap.set_tile(newBoxPos, Tiles.BOX)
                newmap.clear_tile(box)

                # Mover o keeper...
                keeperCoord = newmap.keeper
                #tile = newmap.get_tile(keeperCoord)
                newmap.clear_tile(keeperCoord)
                newmap.set_tile(box, Tiles.MAN)

                if newmap.__str__() in self.get_path_str(node):
                    continue
                if self.isCornered(newmap, newBoxPos):
                    continue

                if self.isWalled(newmap, newBoxPos):
                    continue

                newnode = SearchNode(newmap, node, keys+key, node.depth+1, node.cost+len(node.state.boxes), self.heuristic(newmap))

                #adicionar o novo Node à lista
                self.open_nodes.append(newnode)
                self.open_nodes.sort(key=lambda x: x.cost + x.heuristic)

        print("----- Box Search Failed -----\n")
        return None
