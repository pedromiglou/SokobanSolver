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
        self.visitedNodes = set()
        self.isWall = [] #True se for parede
        self.isBlocked = [] #True se resultar em deadlock
        for x in range(mapa.size[0]):
            self.isWall.append([])
            self.isBlocked.append([])
            for y in range(mapa.size[1]):
                self.isWall[x].append(mapa.get_tile((x,y)) == Tiles.WALL)
                self.isBlocked[x].append(self.isWall[x][y])
        
        self.isWalled_Outer()
        self.isWalled_Inner()
        
        for x in range(1, mapa.size[0]-1):
            for y in range(1, mapa.size[1]-1):
                self.isBlocked[x][y] = True if self.isBlocked[x][y] else self.isCornered((x,y))

    #block positions next to outer wall with no goals
    def isWalled_Outer(self):
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

        # Check if the box position in a blocked wall
        if self.leftBlock:
            for i in range(dim[1]):
                self.isBlocked[1][i] = True
        
        if self.rightBlock:
            for i in range(dim[1]):
                self.isBlocked[dim[0]-2][i] = True
        
        if self.upBlock:
            for i in range(dim[0]):
                self.isBlocked[i][1] = True
        
        if self.botBlock:
            for i in range(dim[0]):
                self.isBlocked[i][dim[1]-2] = True
    
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

    def deadlock(self, boxPos, newBoxes):
        # DeadLock Pattern 1
        if (boxPos[0]+1, boxPos[1]) in newBoxes:  # There is a box to the right
            wall1 = (boxPos[0]-1, boxPos[1]+1)    # Wall x-1, y+1
            wall2 = (boxPos[0], boxPos[1]+2)      # Wall x, y+2
            wall3 = (boxPos[0]+1, boxPos[1]+2)    # Wall x+1, y+2
            wall4 = (boxPos[0]+2, boxPos[1]+1)    # Wall x+2, y+1
            if  not (wall1[0] > self.mapa.size[0]-1 or wall1[1] > self.mapa.size[1]-1 or wall2[0] > self.mapa.size[0]-1 or wall2[1] > self.mapa.size[1]-1 or wall3[0] > self.mapa.size[0]-1 or wall3[1] > self.mapa.size[1]-1 or wall4[0] > self.mapa.size[0]-1 or wall4[1] > self.mapa.size[1]-1):
                if self.isWall[wall1[0]][wall1[1]] and self.isWall[wall2[0]][wall2[1]] and self.isWall[wall3[0]][wall3[1]] and self.isWall[wall4[0]][wall4[1]]:
                    return True

        if (boxPos[0]-1, boxPos[1]) in newBoxes:  # There is a box to the right
            wall1 = (boxPos[0]+1, boxPos[1]+1)    # Wall x+1, y+1
            wall2 = (boxPos[0], boxPos[1]+2)      # Wall x, y+2
            wall3 = (boxPos[0]-1, boxPos[1]+2)    # Wall x-1, y+2
            wall4 = (boxPos[0]-2, boxPos[1]+1)    # Wall x-2, y+1
            if  not (wall1[0] > self.mapa.size[0]-1 or wall1[1] > self.mapa.size[1]-1 or wall2[0] > self.mapa.size[0]-1 or wall2[1] > self.mapa.size[1]-1 or wall3[0] > self.mapa.size[0]-1 or wall3[1] > self.mapa.size[1]-1 or wall4[0] > self.mapa.size[0]-1 or wall4[1] > self.mapa.size[1]-1):
                if self.isWall[wall1[0]][wall1[1]] and self.isWall[wall2[0]][wall2[1]] and self.isWall[wall3[0]][wall3[1]] and self.isWall[wall4[0]][wall4[1]]:
                    return True
        # DeadLock Pattern 2
        box_upPos = self.isWall[boxPos[0]][boxPos[1]-1] or (boxPos[0], boxPos[1]-1) in newBoxes
        box_downPos = self.isWall[boxPos[0]][boxPos[1]+1] or (boxPos[0], boxPos[1]+1) in newBoxes
        box_leftPos = self.isWall[boxPos[0]-1][boxPos[1]] or (boxPos[0]-1, boxPos[1]) in newBoxes
        box_rightPos = self.isWall[boxPos[0]+1][boxPos[1]] or (boxPos[0]+1, boxPos[1]) in newBoxes
        box_upRightPos = self.isWall[boxPos[0]+1][boxPos[1]+1] or (boxPos[0]+1, boxPos[1]+1) in newBoxes
        box_upLeftPos = self.isWall[boxPos[0]-1][boxPos[1]+1] or (boxPos[0]-1, boxPos[1]+1) in newBoxes
        box_downRightPos = self.isWall[boxPos[0]+1][boxPos[1]-1] or (boxPos[0]+1, boxPos[1]-1) in newBoxes
        box_downLeftPos = self.isWall[boxPos[0]-1][boxPos[1]-1] or (boxPos[0]-1, boxPos[1]-1) in newBoxes

        if box_leftPos and box_upPos and box_upLeftPos:
            return True
        if box_rightPos and box_upPos and box_upRightPos:
            return True
        if box_rightPos and box_downPos and box_downRightPos:
            return True
        if box_leftPos and box_downPos and box_downLeftPos:
            return True
        return False

    def tunnel(self, currBoxPos, newBoxPos, movement, newBoxes, keys):
        if movement[0] == 0: #andou em y    0 + 1 -> direita ; 0 - 1 -> esquerda
            if not (0 < newBoxPos[1]+2*movement[1] < self.mapa.size[1]):
                return currBoxPos, newBoxPos, keys

            if newBoxPos not in self.goals: #se a nova posicao da caixa n esta nos objetivos
                if self.isWall[newBoxPos[0]+1][newBoxPos[1]] or self.isWall[newBoxPos[0]-1][newBoxPos[1]]: #se tem uma parede á esquerda ou á direita
                    if self.isWall[newBoxPos[0]+1][newBoxPos[1]+movement[1]] and self.isWall[newBoxPos[0]-1][newBoxPos[1]+movement[1]]: #se na posicao a seguir estiver rodeado de duas paredes
                        if not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movement[1]] and (newBoxPos[0], newBoxPos[1]+movement[1]) not in newBoxes:#se na posição seguinte não está uma caixa nem uma parede
                            currBoxPos, newBoxPos, keys = self.tunnel(newBoxPos, (newBoxPos[0], newBoxPos[1]+movement[1]), movement, newBoxes, keys + keys[-1])
                    
                    elif self.isWall[newBoxPos[0]+1][newBoxPos[1]+movement[1]]: #se tem parede á direita e não tem parede á esquerda
                        if not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movement[1]*2] and (newBoxPos[0], newBoxPos[1]+movement[1]*2) not in newBoxes:#se na posição seguinte não está uma caixa nem uma parede
                            if not self.isWall[newBoxPos[0]-1][newBoxPos[1]+2*movement[1]] and (newBoxPos[0]-1, newBoxPos[1]+movement[1]*2) not in newBoxes:
                                if not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movement[1]] and (newBoxPos[0], newBoxPos[1]+movement[1]) not in newBoxes:
                                    if (newBoxPos[0]-1, newBoxPos[1]+movement[1]) not in newBoxes:
                                        currBoxPos, newBoxPos, keys = self.tunnel(newBoxPos, (newBoxPos[0], newBoxPos[1]+movement[1]), movement, newBoxes, keys + keys[-1])

                    elif self.isWall[newBoxPos[0]-1][newBoxPos[1]+movement[1]]: #se tem parede á esquerda e não tem parede á direita
                        if not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movement[1]*2] and (newBoxPos[0], newBoxPos[1]+movement[1]*2) not in newBoxes:
                            if not self.isWall[newBoxPos[0]+1][newBoxPos[1]+2*movement[1]] and (newBoxPos[0]+1, newBoxPos[1]+movement[1]*2) not in newBoxes:
                                if not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movement[1]] and (newBoxPos[0], newBoxPos[1]+movement[1]) not in newBoxes:
                                    if (newBoxPos[0]+1, newBoxPos[1]+movement[1]) not in newBoxes:
                                        currBoxPos, newBoxPos, keys = self.tunnel(newBoxPos, (newBoxPos[0], newBoxPos[1]+movement[1]), movement, newBoxes, keys + keys[-1])
                    
        else: #andou em x  1 + 1 -> baixo    1 - 1 -> cima
            if not (0 < newBoxPos[0]+2*movement[0] < self.mapa.size[0]):
                return currBoxPos, newBoxPos, keys

            if newBoxPos not in self.goals: #se a nova posicao da caixa n esta nos objetivos
                if self.isWall[newBoxPos[0]][newBoxPos[1]+1] or self.isWall[newBoxPos[0]][newBoxPos[1]-1]: #se tem uma parede em baixo ou em cima
                    if self.isWall[newBoxPos[0]+movement[0]][newBoxPos[1]+1] and self.isWall[newBoxPos[0]+movement[0]][newBoxPos[1]-1]: #se na posicao a seguir estiver rodeado de duas paredes
                        if not self.isBlocked[newBoxPos[0]+movement[0]][newBoxPos[1]] and (newBoxPos[0] + movement[0], newBoxPos[1]) not in newBoxes:#se na posicao seguinte nao esta nem uma caixa nem uma parede
                            currBoxPos, newBoxPos, keys = self.tunnel(newBoxPos, (newBoxPos[0]+movement[0], newBoxPos[1]), movement, newBoxes, keys + keys[-1])
                    
                    elif self.isWall[newBoxPos[0]+movement[0]][newBoxPos[1]+1]: #se na posicao seguinte tem parede em baixo mas nao tem em cima
                        if not self.isBlocked[newBoxPos[0]+movement[0]*2][newBoxPos[1]] and (newBoxPos[0] + movement[0]*2, newBoxPos[1]) not in newBoxes:
                            if not self.isWall[newBoxPos[0]+2*movement[0]][newBoxPos[1]-1] and (newBoxPos[0] + movement[0]*2, newBoxPos[1]-1) not in newBoxes:
                                if not self.isBlocked[newBoxPos[0]+movement[0]][newBoxPos[1]] and (newBoxPos[0] + movement[0], newBoxPos[1]) not in newBoxes:
                                    if (newBoxPos[0] + movement[0], newBoxPos[1]-1) not in newBoxes:
                                        currBoxPos, newBoxPos, keys = self.tunnel(newBoxPos, (newBoxPos[0]+movement[0], newBoxPos[1]), movement, newBoxes, keys + keys[-1])

                    elif self.isWall[newBoxPos[0]+movement[0]][newBoxPos[1]-1]: #se na posicao seguinte tem parede em baixo mas nao tem em cima
                        if not self.isBlocked[newBoxPos[0]+movement[0]*2][newBoxPos[1]] and (newBoxPos[0] + movement[0]*2, newBoxPos[1]) not in newBoxes:
                            if not self.isWall[newBoxPos[0]+2*movement[0]][newBoxPos[1]+1] and (newBoxPos[0] + movement[0]*2, newBoxPos[1]+1) not in newBoxes:
                                if not self.isBlocked[newBoxPos[0]+movement[0]][newBoxPos[1]] and (newBoxPos[0] + movement[0], newBoxPos[1]) not in newBoxes:
                                    if (newBoxPos[0] + movement[0], newBoxPos[1]+1) not in newBoxes:
                                        currBoxPos, newBoxPos, keys = self.tunnel(newBoxPos, (newBoxPos[0]+movement[0], newBoxPos[1]), movement, newBoxes, keys + keys[-1])
                    
        return currBoxPos, newBoxPos, keys


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

                newBoxes = [b for b in node.state[0] if b != currBoxPos]
                newBoxes.append(newBoxPos)

                if self.isBoxed(newBoxPos, newBoxes):
                    continue

                """
                if len(self.goals)>=4:
                    if self.deadlock(newBoxPos, newBoxes):
                        continue
                """

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

                newBoxes = [box for box in newBoxes if box != newBoxPos]
                currBoxPos, newBoxPos, keys = self.tunnel(currBoxPos, newBoxPos,movement,newBoxes,keys)
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

                newnode = SearchNode((frozenset(newBoxes), currBoxPos), node, keys, node.depth+1, node.cost+addFactor, self.heuristic(newBoxes))
                #adicionar o novo Node à lista e sort ao mesmo tempo
                insort_left(self.open_nodes, newnode)

        print("----- Box Search Failed -----\n")
        return None
