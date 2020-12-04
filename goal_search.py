from copy import deepcopy, copy
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
        self.goals = self.mapa.filter_tiles([Tiles.GOAL, Tiles.BOX_ON_GOAL, Tiles.MAN_ON_GOAL])
        self.defineWalls()
        self.visitedNodes = set()
        self.isWall = []
        self.isBlocked = []
        for x in range(mapa.size[0]):
            self.isWall.append([])
            self.isBlocked.append([])
            for y in range(mapa.size[1]):
                self.isWall[x].append(mapa.get_tile((x,y)) == Tiles.WALL)
                self.isBlocked[x].append(True if self.isWall[x][y] else self.isWalled((x,y)))
        
        for x in range(1, mapa.size[0]-1):
            for y in range(1, mapa.size[1]-1):
                self.isBlocked[x][y] = True if self.isBlocked[x][y] else self.isCornered((x,y))


    # obter o caminho (de teclas) da raiz ate um no
    def get_keys(self,node):
        if node.parent == None:
            return node.keys
        else:
            return self.get_keys(node.parent) + node.keys
    
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

        bestcost=[10000000]
        cost = min([(l[0][i], i) for i in range(size)])
        self.auxBruteForce(l, [cost[1]], 1, size, cost[0], bestcost)
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

    '''
    async def computeLowerBound(self, mapa):
        keeperPos = mapa.keeper
        mapa.clear_tile(keeperPos)
        boxes = mapa.filter_tiles([Tiles.BOX, Tiles.BOX_ON_GOAL])
        goals = mapa.filter_tiles([Tiles.GOAL, Tiles.BOX_ON_GOAL, Tiles.MAN_ON_GOAL])
        results = []
        
        n = 0
        for box in boxes:
            auxMapa = deepcopy(mapa)

            for x in [b for b in boxes if b != box]:
                auxMapa.clear_tile(x)
            aux = []
            for goal in goals:
                auxSearch = SearchAgent(auxMapa, (), box, goal)
                path = await auxSearch.search()
                aux.append(len(path))
                #results.insert(n, results[n] + [len(path)])
            n+=1
            results.append(aux)
        
        return sum([min(a) for a in results])
    ''' 

    def isCornered(self, boxPos):
        #if boxPos[0] == 0 or boxPos[1] == 0 or boxPos[0] == self.mapa.size[0]-1 or boxPos[1] == self.mapa.size[1]-1:
        #    return True

        # If the box is on goal, it is not considered a cornered box since it could be part of the solution
        if boxPos in self.goals:
            return False
            
        # Positions = (Up, Down, Left Right)
        box_upPos = self.isWall[boxPos[0]][boxPos[1]-1]
        box_downPos = self.isWall[boxPos[0]][boxPos[1]+1]
        box_leftPos = self.isWall[boxPos[0]-1][boxPos[1]]
        box_rightPos = self.isWall[boxPos[0]+1][boxPos[1]]

        if box_leftPos and box_upPos:
            return True
        if box_upPos and box_rightPos:
            return True
        if box_rightPos and box_downPos:
            return True
        if box_downPos and box_leftPos:
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
        if newBoxPos in self.goals:
            return False

        # If the position directly above is a wall...
        if self.isWall[x][y-1]:
            if (x-1, y) in allBoxPos:
                if self.isWall[x-1][y-1]:
                    return True
            if (x+1, y) in allBoxPos:
                if self.isWall[x+1][y-1]:
                    return True

        # If the position directly bellow is a wall...
        if self.isWall[x][y+1]:
            if (x-1, y) in allBoxPos:
                if self.isWall[x-1][y+1]:
                    return True
            if (x+1,y) in allBoxPos:
                if self.isWall[x+1][y+1]:
                    return True

        # If the position to the left is a wall...
        if self.isWall[x-1][y]:
            if (x, y-1) in allBoxPos:
                if self.isWall[x-1][y-1]:
                    return True
            if (x, y+1) in allBoxPos:
                if self.isWall[x-1][y+1]:
                    return True

        # If the position to the right is a wall...
        if self.isWall[x+1][y]:
            if (x, y-1) in allBoxPos:
                if self.isWall[x+1][y-1]:
                    return True
            if (x, y+1) in allBoxPos:
                if self.isWall[x+1][y+1]:
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
        for goalPos in self.goals:
            if goalPos[0] == 1:
                self.leftBlock = False
            if goalPos[1] == 1:
                self.upBlock = False
            if goalPos[0] == (dim[0] - 2):
                self.rightBlock = False
            if goalPos[1] == (dim[1] - 2):
                self.botBlock = False

    def tunnel(self, currBoxPos, newBoxPos, movement, newBoxes, keys):
        isTunnel = True
        
        if movement[0] == 0: #andou em y    0 + 1 -> direita ; 0 - 1 -> esquerda
            while isTunnel:
                if not (0 < newBoxPos[1]+2*movement[1] < self.mapa.size[1]):
                    isTunnel = False
                    continue

                if newBoxPos not in self.goals: #se a nova posicao da caixa n esta nos objetivos
                    if self.isWall[newBoxPos[0]+1][newBoxPos[1]] or self.isWall[newBoxPos[0]-1][newBoxPos[1]]: #se tem uma parede á esquerda ou á direita
                        if self.isWall[newBoxPos[0]+1][newBoxPos[1]+movement[1]] and self.isWall[newBoxPos[0]-1][newBoxPos[1]+movement[1]]: #se na posicao a seguir estiver rodeado de duas paredes
                            if (newBoxPos[0], newBoxPos[1]+movement[1]) not in newBoxes and not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movement[1]]:#se na posição seguinte não está uma caixa nem uma parede
                                keys += keys[-1]
                                newBoxes = [b for b in newBoxes if b != newBoxPos]
                                currBoxPos = newBoxPos
                                newBoxPos = (newBoxPos[0], newBoxPos[1]+movement[1])
                                newBoxes.append(newBoxPos)
                                continue
                        
                        elif self.isWall[newBoxPos[0]+1][newBoxPos[1]+movement[1]]: #se tem parede á direita e não tem parede á esquerda
                            if (newBoxPos[0], newBoxPos[1]+movement[1]) not in newBoxes and not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movement[1]]:#se na posição seguinte não está uma caixa nem uma parede
                                if (newBoxPos[0], newBoxPos[1]+movement[1]*2) not in newBoxes and not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movement[1]*2]:
                                    if not self.isWall[newBoxPos[0]-1][newBoxPos[1]+2*movement[1]] and (newBoxPos[0]-1, newBoxPos[1]+movement[1]*2) not in newBoxes:
                                        if (newBoxPos[0]-1, newBoxPos[1]+movement[1]) not in newBoxes:
                                            keys += keys[-1]
                                            newBoxes = [b for b in newBoxes if b != newBoxPos]
                                            currBoxPos = newBoxPos
                                            newBoxPos = (newBoxPos[0], newBoxPos[1]+movement[1])
                                            newBoxes.append(newBoxPos)
                                            continue

                        elif self.isWall[newBoxPos[0]-1][newBoxPos[1]+movement[1]]: #se tem parede á esquerda e não tem parede á direita
                            if (newBoxPos[0], newBoxPos[1]+movement[1]) not in newBoxes and not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movement[1]]:#se na posição seguinte não está uma caixa nem uma parede
                                if (newBoxPos[0], newBoxPos[1]+movement[1]*2) not in newBoxes and not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movement[1]*2]:
                                    if not self.isWall[newBoxPos[0]+1][newBoxPos[1]+2*movement[1]] and (newBoxPos[0]+1, newBoxPos[1]+movement[1]*2) not in newBoxes:
                                        if (newBoxPos[0]+1, newBoxPos[1]+movement[1]) not in newBoxes:
                                            keys += keys[-1]
                                            newBoxes = [b for b in newBoxes if b != newBoxPos]
                                            currBoxPos = newBoxPos
                                            newBoxPos = (newBoxPos[0], newBoxPos[1]+movement[1])
                                            newBoxes.append(newBoxPos)
                                            continue
                        

                isTunnel= False
        else: #andou em x  1 + 1 -> baixo    1 - 1 -> cima
            while isTunnel:
                if not (0 < newBoxPos[0]+2*movement[0] < self.mapa.size[0]):
                    isTunnel = False
                    continue

                if newBoxPos not in self.goals: #se a nova posicao da caixa n esta nos objetivos
                    if self.isWall[newBoxPos[0]][newBoxPos[1]+1] or self.isWall[newBoxPos[0]][newBoxPos[1]-1]: #se tem uma parede em baixo ou em cima
                        if self.isWall[newBoxPos[0]+movement[0]][newBoxPos[1]+1] and self.isWall[newBoxPos[0]+movement[0]][newBoxPos[1]-1]: #se na posicao a seguir estiver rodeado de duas paredes
                            if (newBoxPos[0] + movement[0], newBoxPos[1]) not in newBoxes and not self.isBlocked[newBoxPos[0]+movement[0]][newBoxPos[1]]:#se na posicao seguinte nao esta nem uma caixa nem uma parede
                                keys += keys[-1]
                                newBoxes = [b for b in newBoxes if b != newBoxPos]
                                currBoxPos = newBoxPos
                                newBoxPos = (newBoxPos[0]+movement[0], newBoxPos[1])
                                newBoxes.append(newBoxPos)
                                continue
                        
                        elif self.isWall[newBoxPos[0]+movement[0]][newBoxPos[1]+1]: #se na posicao seguinte tem parede em baixo mas nao tem em cima
                            if (newBoxPos[0] + movement[0], newBoxPos[1]) not in newBoxes and not self.isBlocked[newBoxPos[0]+movement[0]][newBoxPos[1]]:#se na posicao seguinte nao esta nem uma caixa nem uma parede
                                if (newBoxPos[0] + movement[0]*2, newBoxPos[1]) not in newBoxes and not self.isBlocked[newBoxPos[0]+movement[0]*2][newBoxPos[1]]:
                                    if not self.isWall[newBoxPos[0]+2*movement[0]][newBoxPos[1]-1] and (newBoxPos[0] + movement[0]*2, newBoxPos[1]-1) not in newBoxes:
                                        if (newBoxPos[0] + movement[0], newBoxPos[1]-1) not in newBoxes:
                                            keys += keys[-1]
                                            newBoxes = [b for b in newBoxes if b != newBoxPos]
                                            currBoxPos = newBoxPos
                                            newBoxPos = (newBoxPos[0]+movement[0], newBoxPos[1])
                                            newBoxes.append(newBoxPos)
                                            continue
                        elif self.isWall[newBoxPos[0]+movement[0]][newBoxPos[1]-1]: #se na posicao seguinte tem parede em baixo mas nao tem em cima
                            if (newBoxPos[0] + movement[0], newBoxPos[1]) not in newBoxes and not self.isBlocked[newBoxPos[0]+movement[0]][newBoxPos[1]]:#se na posicao seguinte nao esta nem uma caixa nem uma parede
                                if (newBoxPos[0] + movement[0]*2, newBoxPos[1]) not in newBoxes and not self.isBlocked[newBoxPos[0]+movement[0]*2][newBoxPos[1]]:
                                    if not self.isWall[newBoxPos[0]+2*movement[0]][newBoxPos[1]+1] and (newBoxPos[0] + movement[0]*2, newBoxPos[1]+1) not in newBoxes:
                                        if (newBoxPos[0] + movement[0], newBoxPos[1]+1) not in newBoxes:
                                            keys += keys[-1]
                                            newBoxes = [b for b in newBoxes if b != newBoxPos]
                                            currBoxPos = newBoxPos
                                            newBoxPos = (newBoxPos[0]+movement[0], newBoxPos[1])
                                            newBoxes.append(newBoxPos)
                                            continue
                        

                isTunnel= False
                
        return currBoxPos,newBoxPos,newBoxes,keys


    # procurar a solucao
    async def search(self, limit=None):
        count = 0
        #lowerBound = await self.computeLowerBound(self.mapa)

        while self.open_nodes != []:
            node = self.open_nodes.pop(0)
            count+=1
            #print(count)

            #se cheguei a solucao
            if all([coord in self.goals for coord in node.state[0]]):
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

                newBoxPos = (currBoxPos[0]+movement[0], currBoxPos[1]+movement[1])
                newKeeperPos = (currBoxPos[0]-movement[0], currBoxPos[1]-movement[1])

                #verificar se esta a ir contra uma parede ou caixa e verificar se o lugar do keeper esta vazio
                if self.isWall[newKeeperPos[0]][newKeeperPos[1]] or self.isBlocked[newBoxPos[0]][newBoxPos[1]]:
                    continue

                if newBoxPos in node.state[0] or newKeeperPos in node.state[0]:
                    continue

                #if self.isWalled(newBoxPos):
                #    continue

                #if self.isCornered(newBoxPos):
                #    continue

                newBoxes = [b for b in node.state[0] if b != currBoxPos]
                newBoxes.append(newBoxPos)

                if self.isBoxed(newBoxPos, newBoxes):
                    continue

                #verificar se ha um caminho para o keeper
                if node.state[1] != newKeeperPos:
                    agentSearch = SearchAgent(self.isWall, node.state[0], node.state[1], newKeeperPos)
                    keys = await agentSearch.search()
                    if keys == None:
                        continue
                else:
                    keys = ""
                
                addFactor = len(keys)/20
                
                keys += key

                currBoxPos, newBoxPos, newBoxes, keys = self.tunnel(currBoxPos, newBoxPos,movement,newBoxes,keys)

                if (frozenset(newBoxes), currBoxPos) in self.visitedNodes:
                    continue
                else:
                    self.visitedNodes.add((frozenset(newBoxes), currBoxPos))

                newnode = SearchNode((frozenset(newBoxes), currBoxPos), node, keys, node.depth+1, node.cost+addFactor, self.heuristic(newBoxes))
                #adicionar o novo Node à lista e sort ao mesmo tempo
                insort_left(self.open_nodes, newnode)

        print("----- Box Search Failed -----\n")
        return None
