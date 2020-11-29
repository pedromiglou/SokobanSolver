from copy import deepcopy
from consts import Tiles
import asyncio
from agent_search import SearchAgent
from bisect import insort_left
from array import *

# No de uma arvore de pesquisa
class SearchNode:
    def __init__(self, state, parent, key, depth, cost, heuristic): 
        self.state = state
        #self.reducedState = str(sorted(self.state.boxes)) + str(self.state.keeper)
        self.parent = parent
        self.keys = key
        self.depth = depth
        self.cost = cost
        self.heuristic = heuristic

    def __str__(self):
        return "no(" + str(self.state) + "," + str(self.parent) + ")"

    #funcao para fazer sort sem usar sempre key
    def __lt__(self, other):
        return self.cost + self.heuristic < other.cost + other.heuristic
        #return self.heuristic < other.heuristic

# Arvore de pesquisa
class SearchTree:
    # construtor
    def __init__(self, mapa):
        self.root = SearchNode((set(mapa.boxes), mapa.keeper), None, "", 0, 0, None)
        self.mapa = mapa
        self.open_nodes = [self.root]
        self.defineWalls()
        self.visitedNodes = set()
        self.goals = self.mapa.filter_tiles([Tiles.GOAL, Tiles.BOX_ON_GOAL, Tiles.MAN_ON_GOAL])

    # obter o caminho (de teclas) da raiz ate um no
    def get_keys(self,node):
        if node.parent == None:
            return node.keys
        else:
            return self.get_keys(node.parent) + node.keys
    
    # analisar se um estado anterior é igual ao atual
    def state_in_path(self, node, newstate):
        if node.state == newstate:
            #print(node.state[0], " == ", newstate)
            return True
        else:
            if node.parent != None:
                return self.state_in_path(node.parent, newstate)
            else:
                return False
    
    # calculo da heuristica
    def heuristic(self, boxes):
        goals = [goal for goal in self.goals if goal not in boxes]
        boxes = [box for box in boxes if box not in self.goals]

        if len(goals) == 0:
            return 0
        
        if len(goals) == 1:
            return abs(boxes[0][0]-goals[0][0]) + abs(boxes[0][1]-goals[0][1])

        size = len(goals)

        l = []
        for i in range(size):
            l.append([])
            for j in range(size):
                l[i].append(abs(boxes[i][0]-goals[j][0]) + abs(boxes[i][1]-goals[j][1]))

        """
        print("memes")
        a = [[2,2,3,4],[2,4,5,6],[3,3,4,5],[6,4,3,2]]
        bestcost=[10000000]
        cost = min([(a[0][i], i) for i in range(4)])
        self.auxBruteForce(a, [cost[1]], 1, 4, cost[0], bestcost)
        print(bestcost)
        """

        bestcost=[10000000]
        #cost = min([(l[0][i], i) for i in range(size)])
        self.auxBruteForce(l, [], 0, size, 0, bestcost)
        return bestcost[0]
    
    def auxBruteForce(self, l, selected, row, size, cost, bestcost):
        for i in range(size):
            if i not in selected:
                if row != size-1:
                    if cost + l[row][i] >= bestcost[0]:
                        return
                    self.auxBruteForce(l, selected + [i], row+1, size, cost+l[row][i], bestcost)
                else:
                    if bestcost[0] > cost + l[row][i]:
                        bestcost[0] = cost + l[row][i]

    
    def isCornered(self, boxPos):

        # If the box is on goal, it is not considered a cornered box since it could be part of the solution
        if self.mapa.get_tile(boxPos) == Tiles.GOAL or self.mapa.get_tile(boxPos) == Tiles.BOX_ON_GOAL:
            return False
            
        # Positions = (Up, Down, Left Right)
        box_upPos = self.mapa.get_tile( tuple(map( lambda t1, t2: t1 + t2, boxPos, (0, -1) )) )
        box_downPos = self.mapa.get_tile( tuple(map( lambda t1, t2: t1 + t2, boxPos, (0, 1) )) )
        box_leftPos = self.mapa.get_tile( tuple(map( lambda t1, t2: t1 + t2, boxPos, (-1, 0) )) )
        box_rightPos = self.mapa.get_tile( tuple(map( lambda t1, t2: t1 + t2, boxPos, (1, 0) )) )

        if (box_leftPos == Tiles.WALL) and (box_upPos == Tiles.WALL):
            return True
        if (box_upPos == Tiles.WALL) and (box_rightPos == Tiles.WALL):
            return True
        if (box_rightPos == Tiles.WALL) and (box_downPos == Tiles.WALL):
            return True
        if (box_downPos == Tiles.WALL) and (box_leftPos == Tiles.WALL):
            return True

        return False

    def isWalled(self, boxPos):
        if not (self.leftBlock or self.upBlock or self.botBlock or self.rightBlock):
            return False

        dim = self.mapa.size

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
        
    def isBoxed(self, newBoxPos, allBoxPos):
        x = newBoxPos[0]
        y = newBoxPos[1]
        if self.mapa.get_tile(newBoxPos) in [Tiles.GOAL, Tiles.BOX_ON_GOAL]:
            return False

        # If the position directly above is a wall...
        if self.mapa.get_tile((x, y-1)) == Tiles.WALL:
            if (x-1, y) in allBoxPos:
                if (self.mapa.get_tile((x-1, y-1))) == Tiles.WALL:
                    return True
            if (x+1, y) in allBoxPos:
                if (self.mapa.get_tile((x+1, y-1))) == Tiles.WALL:
                    return True

        # If the position directly bellow is a wall...
        if self.mapa.get_tile((x, y+1)) == Tiles.WALL:
            if (x-1, y) in allBoxPos:
                if (self.mapa.get_tile((x-1, y+1))) == Tiles.WALL:
                    return True
            if (x+1, y) in allBoxPos:
                if (self.mapa.get_tile((x+1, y+1))) == Tiles.WALL:
                    return True

        # If the position to the left is a wall...
        if self.mapa.get_tile((x-1, y)) == Tiles.WALL:
            if (x, y-1) in allBoxPos:
                if (self.mapa.get_tile((x-1, y-1))) == Tiles.WALL:
                    return True
            if (x, y+1) in allBoxPos:
                if (self.mapa.get_tile((x-1, y+1))) == Tiles.WALL:
                    return True

        # If the position to the right is a wall...
        if self.mapa.get_tile((x+1, y)) == Tiles.WALL:
            if (x, y-1) in allBoxPos:
                if (self.mapa.get_tile((x+1, y-1))) == Tiles.WALL:
                    return True
            if (x, y+1) in allBoxPos:
                if (self.mapa.get_tile((x+1, y+1))) == Tiles.WALL:
                    return True
        
        return False

    def defineWalls(self):
        dim = self.mapa.size

        # All walls start out as blocked, meaning they don't have goals and the box should never reach them
        self.leftBlock = True
        self.upBlock = True
        self.rightBlock = True
        self.botBlock = True

        # If there is a goal on a certain border, that border will no longer be blocked
        for goalPos in self.mapa.filter_tiles([ Tiles.GOAL, Tiles.BOX_ON_GOAL, Tiles.MAN_ON_GOAL ]):
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
            #print(count)

            #se cheguei a solucao
            if all([self.mapa.get_tile(coord) in [Tiles.BOX_ON_GOAL, Tiles.GOAL, Tiles.MAN_ON_GOAL] for coord in node.state[0]]):
                #print(node.state)
                print("Number of attempts: ", count, "\n")
                print(self.get_keys(node))
                return self.get_keys(node)

            #if node.state.completed:
            #    print("Number of attempts: ", count, "\n")
            #    return self.get_keys(node)

            await asyncio.sleep(0) # this should be 0 in your code and this is REQUIRED

            #como nao cheguei tenho de obter uma lista de possiveis movimentos das caixas
            options = dict()
            for box in node.state[0]:
                options[(box, "d")] = (1, 0)
                options[(box, "a")] = (-1, 0)
                options[(box, "s")] = (0, 1)
                options[(box, "w")] = (0, -1)
            

            for key, movement in options.items():
                currBoxPos = key[0]
                key = key[1]

                if count == 2:
                    pass

                newBoxPos = (currBoxPos[0]+movement[0], currBoxPos[1]+movement[1])
                newKeeperPos = (currBoxPos[0]-movement[0], currBoxPos[1]-movement[1])

                #verificar se esta a ir contra uma parede ou caixa e verificar se o lugar do keeper esta vazio
                newTile = self.mapa.get_tile(newBoxPos)
                keeperTile = self.mapa.get_tile(newKeeperPos)

                if any([tile == Tiles.WALL for tile in [keeperTile, newTile]]):
                    continue

                if newBoxPos in node.state[0] or newKeeperPos in node.state[0]:
                    continue

                if self.isCornered(newBoxPos):
                    continue

                if self.isWalled(newBoxPos):
                    continue

                newBoxes = [b for b in node.state[0] if b != currBoxPos]
                newBoxes.append(newBoxPos)

                if self.isBoxed(newBoxPos, newBoxes):
                    continue

                #verificar se ha um caminho para o keeper
                agentSearch = SearchAgent(self.mapa, node.state[0], node.state[1], newKeeperPos)

                keys = await agentSearch.search()
                
                if keys == None:
                    continue

                if (frozenset(newBoxes), currBoxPos) in self.visitedNodes:
                    continue
                else:
                    self.visitedNodes.add((frozenset(newBoxes), currBoxPos))

                newnode = SearchNode((frozenset(newBoxes), currBoxPos), node, keys+key, node.depth+1, node.cost+1, self.heuristic(newBoxes))

                #encontrou um túnel
                #if movement[0] == 0: #andou em y
                #    if node.state.get_tile([box[0]+1, box[1]+movement[1]]) == Tiles.WALL and node.state.get_tile([box[0]-1, box[1]+movement[1]]) == Tiles.WALL:
                #        newnode.keys += newnode.keys[-1]
                #else:
                #    if node.state.get_tile([box[0]+movement[0], box[1]+1]) == Tiles.WALL and node.state.get_tile([box[0]+movement[0], box[1]-1]) == Tiles.WALL:
                #        newnode.keys += newnode.keys[-1]

                #adicionar o novo Node à lista e sort ao mesmo tempo
                insort_left(self.open_nodes, newnode)

        print("----- Box Search Failed -----\n")
        return None
