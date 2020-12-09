from copy import deepcopy, copy
from consts import Tiles
import asyncio
from agent_search import SearchAgent
from bisect import insort_left
from array import *
import time

# No de uma arvore de pesquisa usando breath
class BreathNode:
    def __init__(self, state, parent, keys, depth):
        self.state = state
        self.parent = parent
        self.keys = keys
        self.depth = depth

    def __str__(self):
        return "no(" + str(self.state) + "," + str(self.parent) + ")"

    #funcao para fazer sort sem usar sempre key
    def __lt__(self, other):
        return self.depth < other.depth

# No de uma arvore de pesquisa usando A*
class StarNode:
    def __init__(self, state, parent, keys, cost, heuristic):
        self.state = state
        self.parent = parent
        self.keys = keys
        self.cost = cost
        self.priority = heuristic + cost

    def __str__(self):
        return "no(" + str(self.state) + "," + str(self.parent) + ")"

    #funcao para fazer sort sem usar sempre key
    def __lt__(self, other):
        return self.priority < other.priority

# Arvore de pesquisa
class SearchTree:
    # construtor
    def __init__(self, mapa):
        self.timer = time.time()
        self.mapa = mapa
        self.size = mapa.size
        self.goals = mapa.filter_tiles([Tiles.GOAL, Tiles.BOX_ON_GOAL, Tiles.MAN_ON_GOAL])

        if self.size[0]*self.size[1]*len(self.goals) > 500:
            self.isSimple = False
            self.root = StarNode((frozenset(mapa.boxes), mapa.keeper), None, "", 0, 1000000)
        else:
            self.isSimple = True
            self.root = BreathNode((frozenset(mapa.boxes), mapa.keeper), None, "", 0)

        self.open_nodes = [self.root]
        self.visitedNodes = set()
        self.visitedNodes.add(self.root.state)

        self.isWall = [] #True se for parede
        self.isBlocked = [] #True se resultar em deadlock
        for x in range(mapa.size[0]):
            self.isWall.append([])
            self.isBlocked.append([])
            for y in range(mapa.size[1]):
                self.isWall[x].append(mapa.get_tile((x,y)) == Tiles.WALL or x==0 or y==0 or x==self.size[0]-1 or y==self.size[1]-1)
                self.isBlocked[x].append(self.isWall[x][y])
        
        self.isWalled_Outer()
        self.isWalled_Inner()
        
        for x in range(1, mapa.size[0]-1):
            for y in range(1, mapa.size[1]-1):
                self.isBlocked[x][y] = True if self.isBlocked[x][y] else self.isCornered((x,y))

    #block positions next to outer wall with no goals
    def isWalled_Outer(self):
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
            if goalPos[0] == (self.size[0] - 2):
                self.rightBlock = False
            if goalPos[1] == (self.size[1] - 2):
                self.botBlock = False

        # Check if the box position in a blocked wall
        if self.leftBlock:
            for i in range(self.size[1]):
                self.isBlocked[1][i] = True
        
        if self.rightBlock:
            for i in range(self.size[1]):
                self.isBlocked[self.size[0]-2][i] = True
        
        if self.upBlock:
            for i in range(self.size[0]):
                self.isBlocked[i][1] = True
        
        if self.botBlock:
            for i in range(self.size[0]):
                self.isBlocked[i][self.size[1]-2] = True
    
    #block positions next to inner walls with no goals that result in deadlock
    def isWalled_Inner(self):
        dim = self.mapa.size

        for x in range(1, dim[0]-1):
            for y in range(1, dim[1]-1):
                if not self.isBlocked[x][y]:
                    
                    #verify if it is blocked to the left
                    isBlocked_Left = True
                    i = x
                    toBlock = []
                    while 0<i:
                        if self.isWall[i][y]:
                            break

                        if not(self.isWall[i][y-1] or self.isWall[i][y+1]) or (i, y) in self.goals:
                            isBlocked_Left = False
                            break

                        toBlock.append((i,y))
                        i -= 1
                    
                    if not isBlocked_Left:
                        continue
                    else:
                        #if blocked to the left verify to the right
                        isBlocked_Right = True
                        i = x+1
                        while i<dim[0]-1:
                            if self.isWall[i][y]:
                                break

                            if not(self.isWall[i][y-1] or self.isWall[i][y+1]) or (i, y) in self.goals:
                                isBlocked_Right = False
                                break

                            toBlock.append((i,y))
                            i += 1

                        if isBlocked_Right:
                            for tile in toBlock:
                                self.isBlocked[tile[0]][tile[1]] = True
                    
                    #verify if blocked upwards
                    isBlocked_Up = True
                    j=y
                    toBlock = []
                    while 0<j:
                        if self.isWall[x][j]:
                            break

                        if not(self.isWall[x-1][j] or self.isWall[x+1][j]) or (x, j) in self.goals:
                            isBlocked_Up = False
                            break

                        toBlock.append((x,j))
                        j -= 1
                    
                    if not isBlocked_Up:
                        continue
                    else:
                        #verify if blocked downwards
                        isBlocked_Down = True
                        j = y+1
                        while j<dim[1]-1:
                            if self.isWall[x][j]:
                                break

                            if not(self.isWall[x-1][j] or self.isWall[x+1][j]) or (x, j) in self.goals:
                                isBlocked_Down = False
                                break

                            toBlock.append((x,j))
                            j += 1

                        if isBlocked_Down:
                            for tile in toBlock:
                                self.isBlocked[tile[0]][tile[1]] = True
    
    #block corners
    def isCornered(self, boxPos):
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

    # obter o caminho (de teclas) da raiz ate um no
    async def get_keys(self,node):
        if node.parent == None:
            return ""
        else:
            agentSearch = SearchAgent(self.isWall, node.parent.state[0], node.parent.state[1], node.destination)
            keys = await agentSearch.search()
            parentkeys = await self.get_keys(node.parent)
            return parentkeys + keys + node.keys
    
    
    def heuristic(self, boxes):
        goals = [goal for goal in self.goals if goal not in boxes]
        boxes = [box for box in boxes if box not in self.goals]

        h = 0
        for i in range(len(goals)):
            h += min([abs(boxes[i][0]-goals[j][0]) + abs(boxes[i][1]-goals[j][1]) for j in range(len(goals))])
        
        return h
    
    
    """
    # calculo da heuristica
    def heuristic(self, boxes):
        goals = [goal for goal in self.goals if goal not in boxes]
        boxes = [box for box in boxes if box not in self.goals]
        size = len(goals)

        if size == 0:
            return 0
        
        if size == 1:
            return abs(boxes[0][0]-goals[0][0]) + abs(boxes[0][1]-goals[0][1])

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
    """

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

    """
    def deadlock(self, boxPos, newBoxes):
        if boxPos in self.goals or (boxPos[0], boxPos[1]+1) in self.goals:
            return False

        # DeadLock Pattern 1
        if (boxPos[0]+1, boxPos[1]) in newBoxes:  # There is a box to the right
            if (boxPos[0]+1, boxPos[1]+1) in self.goals:
                return False
            wall1 = (boxPos[0]-1, boxPos[1]+1)    # Wall x-1, y+1
            wall2 = (boxPos[0], boxPos[1]+2)      # Wall x, y+2
            wall3 = (boxPos[0]+1, boxPos[1]+2)    # Wall x+1, y+2
            wall4 = (boxPos[0]+2, boxPos[1]+1)    # Wall x+2, y+1
            if  not (wall1[0] > self.mapa.size[0]-1 or wall1[1] > self.mapa.size[1]-1 or wall2[0] > self.mapa.size[0]-1 or wall2[1] > self.mapa.size[1]-1 or wall3[0] > self.mapa.size[0]-1 or wall3[1] > self.mapa.size[1]-1 or wall4[0] > self.mapa.size[0]-1 or wall4[1] > self.mapa.size[1]-1):
                if self.isWall[wall1[0]][wall1[1]] and self.isWall[wall2[0]][wall2[1]] and self.isWall[wall3[0]][wall3[1]] and self.isWall[wall4[0]][wall4[1]]:
                    return True

        if (boxPos[0]-1, boxPos[1]) in newBoxes:  # There is a box to the left
            if (boxPos[0]-1, boxPos[1]+1) in self.goals:
                return False
            wall1 = (boxPos[0]+1, boxPos[1]+1)    # Wall x+1, y+1
            wall2 = (boxPos[0], boxPos[1]+2)      # Wall x, y+2
            wall3 = (boxPos[0]-1, boxPos[1]+2)    # Wall x-1, y+2
            wall4 = (boxPos[0]-2, boxPos[1]+1)    # Wall x-2, y+1
            if  not (wall1[0] > self.mapa.size[0]-1 or wall1[1] > self.mapa.size[1]-1 or wall2[0] > self.mapa.size[0]-1 or wall2[1] > self.mapa.size[1]-1 or wall3[0] > self.mapa.size[0]-1 or wall3[1] > self.mapa.size[1]-1 or wall4[0] > self.mapa.size[0]-1 or wall4[1] > self.mapa.size[1]-1):
                if self.isWall[wall1[0]][wall1[1]] and self.isWall[wall2[0]][wall2[1]] and self.isWall[wall3[0]][wall3[1]] and self.isWall[wall4[0]][wall4[1]]:
                    return True
                    
        # DeadLock Pattern 2
        box_rightPos = self.isWall[boxPos[0]+1][boxPos[1]] or (boxPos[0]+1, boxPos[1]) in newBoxes
        box_leftPos = self.isWall[boxPos[0]-1][boxPos[1]] or (boxPos[0]-1, boxPos[1]) in newBoxes

        if box_rightPos:
            box_upPos = self.isWall[boxPos[0]][boxPos[1]-1] or (boxPos[0], boxPos[1]-1) in newBoxes
            box_downPos = self.isWall[boxPos[0]][boxPos[1]+1] or (boxPos[0], boxPos[1]+1) in newBoxes
            box_upRightPos = self.isWall[boxPos[0]+1][boxPos[1]+1] or (boxPos[0]+1, boxPos[1]+1) in newBoxes
            box_downRightPos = self.isWall[boxPos[0]+1][boxPos[1]-1] or (boxPos[0]+1, boxPos[1]-1) in newBoxes

            if box_rightPos and box_upPos and box_upRightPos:
                return True
            if box_rightPos and box_downPos and box_downRightPos:
                return True        
        if box_leftPos:
            box_upPos = self.isWall[boxPos[0]][boxPos[1]-1] or (boxPos[0], boxPos[1]-1) in newBoxes
            box_downPos = self.isWall[boxPos[0]][boxPos[1]+1] or (boxPos[0], boxPos[1]+1) in newBoxes
            box_upLeftPos = self.isWall[boxPos[0]-1][boxPos[1]+1] or (boxPos[0]-1, boxPos[1]+1) in newBoxes
            box_downLeftPos = self.isWall[boxPos[0]-1][boxPos[1]-1] or (boxPos[0]-1, boxPos[1]-1) in newBoxes

            if box_leftPos and box_upPos and box_upLeftPos:
                return True
            if box_leftPos and box_downPos and box_downLeftPos:
                return True        
        return False
    """

    def tunnel(self, currBoxPos, newBoxPos, movX, movY, newBoxes, keys):
        if movX == 0: #andou em y    0 + 1 -> direita ; 0 - 1 -> esquerda
            if not (0 < newBoxPos[1]+2*movY < self.size[1]):
                return currBoxPos, newBoxPos, keys

            if newBoxPos not in self.goals: #se a nova posicao da caixa n esta nos objetivos
                if self.isWall[newBoxPos[0]+1][newBoxPos[1]] or self.isWall[newBoxPos[0]-1][newBoxPos[1]]: #se tem uma parede á esquerda ou á direita
                    if self.isWall[newBoxPos[0]+1][newBoxPos[1]+movY] and self.isWall[newBoxPos[0]-1][newBoxPos[1]+movY]: #se na posicao a seguir estiver rodeado de duas paredes
                        if not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movY] and (newBoxPos[0], newBoxPos[1]+movY) not in newBoxes:#se na posição seguinte não está uma caixa nem uma parede
                            currBoxPos, newBoxPos, keys = self.tunnel(newBoxPos, (newBoxPos[0], newBoxPos[1]+movY), movX, movY, newBoxes, keys + keys[-1])
                    
                    elif self.isWall[newBoxPos[0]+1][newBoxPos[1]+movY]: #se tem parede á direita e não tem parede á esquerda
                        if not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movY*2] and (newBoxPos[0], newBoxPos[1]+movY*2) not in newBoxes:#se na posição seguinte não está uma caixa nem uma parede
                            if not self.isWall[newBoxPos[0]-1][newBoxPos[1]+2*movY] and (newBoxPos[0]-1, newBoxPos[1]+movY*2) not in newBoxes:
                                if not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movY] and (newBoxPos[0], newBoxPos[1]+movY) not in newBoxes:
                                    if (newBoxPos[0]-1, newBoxPos[1]+movY) not in newBoxes:
                                        currBoxPos, newBoxPos, keys = self.tunnel(newBoxPos, (newBoxPos[0], newBoxPos[1]+movY), movX, movY, newBoxes, keys + keys[-1])

                    elif self.isWall[newBoxPos[0]-1][newBoxPos[1]+movY]: #se tem parede á esquerda e não tem parede á direita
                        if not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movY*2] and (newBoxPos[0], newBoxPos[1]+movY*2) not in newBoxes:
                            if not self.isWall[newBoxPos[0]+1][newBoxPos[1]+2*movY] and (newBoxPos[0]+1, newBoxPos[1]+movY*2) not in newBoxes:
                                if not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movY] and (newBoxPos[0], newBoxPos[1]+movY) not in newBoxes:
                                    if (newBoxPos[0]+1, newBoxPos[1]+movY) not in newBoxes:
                                        currBoxPos, newBoxPos, keys = self.tunnel(newBoxPos, (newBoxPos[0], newBoxPos[1]+movY), movX, movY, newBoxes, keys + keys[-1])
                    
        else: #andou em x  1 + 1 -> baixo    1 - 1 -> cima
            if not (0 < newBoxPos[0]+2*movX < self.size[0]):
                return currBoxPos, newBoxPos, keys

            if newBoxPos not in self.goals: #se a nova posicao da caixa n esta nos objetivos
                if self.isWall[newBoxPos[0]][newBoxPos[1]+1] or self.isWall[newBoxPos[0]][newBoxPos[1]-1]: #se tem uma parede em baixo ou em cima
                    if self.isWall[newBoxPos[0]+movX][newBoxPos[1]+1] and self.isWall[newBoxPos[0]+movX][newBoxPos[1]-1]: #se na posicao a seguir estiver rodeado de duas paredes
                        if not self.isBlocked[newBoxPos[0]+movX][newBoxPos[1]] and (newBoxPos[0] + movX, newBoxPos[1]) not in newBoxes:#se na posicao seguinte nao esta nem uma caixa nem uma parede
                            currBoxPos, newBoxPos, keys = self.tunnel(newBoxPos, (newBoxPos[0]+movX, newBoxPos[1]), movX, movY, newBoxes, keys + keys[-1])
                    
                    elif self.isWall[newBoxPos[0]+movX][newBoxPos[1]+1]: #se na posicao seguinte tem parede em baixo mas nao tem em cima
                        if not self.isBlocked[newBoxPos[0]+movX*2][newBoxPos[1]] and (newBoxPos[0] + movX*2, newBoxPos[1]) not in newBoxes:
                            if not self.isWall[newBoxPos[0]+2*movX][newBoxPos[1]-1] and (newBoxPos[0] + movX*2, newBoxPos[1]-1) not in newBoxes:
                                if not self.isBlocked[newBoxPos[0]+movX][newBoxPos[1]] and (newBoxPos[0] + movX, newBoxPos[1]) not in newBoxes:
                                    if (newBoxPos[0] + movX, newBoxPos[1]-1) not in newBoxes:
                                        currBoxPos, newBoxPos, keys = self.tunnel(newBoxPos, (newBoxPos[0]+movX, newBoxPos[1]), movX, movY, newBoxes, keys + keys[-1])

                    elif self.isWall[newBoxPos[0]+movX][newBoxPos[1]-1]: #se na posicao seguinte tem parede em baixo mas nao tem em cima
                        if not self.isBlocked[newBoxPos[0]+movX*2][newBoxPos[1]] and (newBoxPos[0] + movX*2, newBoxPos[1]) not in newBoxes:
                            if not self.isWall[newBoxPos[0]+2*movX][newBoxPos[1]+1] and (newBoxPos[0] + movX*2, newBoxPos[1]+1) not in newBoxes:
                                if not self.isBlocked[newBoxPos[0]+movX][newBoxPos[1]] and (newBoxPos[0] + movX, newBoxPos[1]) not in newBoxes:
                                    if (newBoxPos[0] + movX, newBoxPos[1]+1) not in newBoxes:
                                        currBoxPos, newBoxPos, keys = self.tunnel(newBoxPos, (newBoxPos[0]+movX, newBoxPos[1]), movX, movY, newBoxes, keys + keys[-1])
                    
        return currBoxPos, newBoxPos, keys
    
    async def definePassages(self):
        self.passages = []
        for x in range(2, self.size[0]-2):
            for y in range(2, self.size[1]-2):
                if (x, y) in self.goals or self.isWall[x][y]:
                    continue
                if self.isWall[x+1][y] and self.isWall[x-1][y] and not self.isWall[x][y-1] and not self.isWall[x][y+1]: #vertical
                    a = SearchAgent(self.isWall, [(x,y)], (x,y-1), (x, y+1))
                    if await a.search() == None:
                        self.passages.append((x,y))
                elif not self.isWall[x+1][y] and not self.isWall[x-1][y] and self.isWall[x][y-1] and self.isWall[x][y+1]: #horizontal
                    a = SearchAgent(self.isWall, [(x,y)], (x-1,y), (x+1, y))
                    if await a.search() == None:
                        self.passages.append((x,y))

    # procurar a solucao
    async def search(self, limit=None):
        count = 0
        #lowerBound = await self.computeLowerBound(self.mapa)
        await self.definePassages()

        while self.open_nodes != []:
            node = self.open_nodes.pop(0)
            count+=1

            #se cheguei a solucao
            if all([coord in self.goals for coord in node.state[0]]):
                print("Number of attempts: ", count, "\n")
                print("Time: ", time.time()-self.timer, "\n")
                keys = await self.get_keys(node)
                print(keys)
                return keys

            #if node.state.completed:
            #    print("Number of attempts: ", count, "\n")
            #    return self.get_keys(node)

            #await asyncio.sleep(0) # this should be 0 in your code and this is REQUIRED

            #encontrar os tiles para onde o agent pode ir
            agentSearch = SearchAgent(self.isWall, node.state[0], node.state[1], (0,0))
            await agentSearch.search()
            possibleTiles = agentSearch.visitedNodes

            #como nao cheguei tenho de obter uma lista de possiveis movimentos das caixas
            options = []
            for box in node.state[0]:
                options.append((box, "d", 1, 0))
                options.append((box, "a", -1, 0))
                options.append((box, "s", 0, 1))
                options.append((box, "w", 0, -1))

            for currBoxPos, keys, movX, movY in options:
                newBoxPos = (currBoxPos[0]+movX, currBoxPos[1]+movY)
                newKeeperPos = (currBoxPos[0]-movX, currBoxPos[1]-movY)

                #verificar se esta a ir contra uma parede ou caixa e verificar se o lugar do keeper esta vazio
                if self.isWall[newKeeperPos[0]][newKeeperPos[1]] or self.isBlocked[newBoxPos[0]][newBoxPos[1]]:
                    continue

                if newBoxPos in node.state[0] or newKeeperPos in node.state[0]:
                    continue

                newBoxes = [b for b in node.state[0] if b != currBoxPos]

                if self.isBoxed(newBoxPos, newBoxes):
                    continue

                #verificar se ha um caminho para o keeper
                if newKeeperPos not in possibleTiles:
                    continue
                
                addFactor = (abs(node.state[1][0]-newKeeperPos[0]) + abs(node.state[1][1]-newKeeperPos[1]))/20

                currBoxPos, newBoxPos, keys = self.tunnel(currBoxPos, newBoxPos, movX,movY,newBoxes,keys)

                if newBoxPos in self.passages:
                    if (newBoxPos[0]+movX, newBoxPos[1]+movY) not in self.goals and (newBoxPos[0]+movX*2, newBoxPos[1]+movY*2) not in self.goals:
                        if (newBoxPos[0]+movX, newBoxPos[1]+movY) in newBoxes or (newBoxPos[0]+movX*2, newBoxPos[1]+movY*2) in newBoxes:
                            continue
                        else:
                            currBoxPos = (currBoxPos[0]+movX*2, currBoxPos[1]+movY*2)
                            newBoxPos = (newBoxPos[0]+movX*2, newBoxPos[1]+movY*2)
                            keys += keys[-1] + keys[-1]
                            if self.isBoxed(newBoxPos, newBoxes):
                                continue

                newBoxes.append(newBoxPos)

                if (frozenset(newBoxes), currBoxPos) in self.visitedNodes:
                    continue
                else:
                    self.visitedNodes.add((frozenset(newBoxes), currBoxPos))

                ################################################################################################
                ## CODE FOR TESTING PURPOSES
                #currMap = deepcopy(self.mapa)
                # Clear map of all entities
                #for tile in self.mapa.filter_tiles([Tiles.BOX, Tiles.BOX_ON_GOAL, Tiles.MAN, Tiles.MAN_ON_GOAL]):
                #    currMap.clear_tile(tile)
                # Set boxes
                #for b in newBoxes:
                #    currMap.set_tile(b, Tiles.BOX)
                # Set keeper
                #currMap.set_tile(currBoxPos, Tiles.MAN)
                #print(currMap, "\n")
                ################################################################################################

                if self.isSimple:
                    newnode = BreathNode((frozenset(newBoxes), currBoxPos), node, keys, node.depth+1)
                else:
                    newnode = StarNode((frozenset(newBoxes), currBoxPos), node, keys, node.cost + addFactor, self.heuristic(newBoxes))
                newnode.destination = newKeeperPos
                #adicionar o novo Node à lista e sort ao mesmo tempo
                insort_left(self.open_nodes, newnode)

        print("----- Box Search Failed -----\n")
        return None
