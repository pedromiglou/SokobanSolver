########################
### Group              #
# Pedro Santos - 93221 #
# Ricardo Cruz - 93118 #
# Pedro Amaral - 93283 #
########################

from copy import deepcopy, copy
from consts import Tiles
import asyncio
from agent_search import SearchAgent
from bisect import insort_left
import time

# search tree node using A*
class BoxNode:
    def __init__(self, state, parent, keys, cost, heuristic):
        self.state = state
        self.parent = parent
        self.keys = keys
        self.cost = cost
        self.priority = heuristic + cost

    def __str__(self):
        return "no(" + str(self.state) + "," + str(self.parent) + ")"

    #function used when these nodes are sorted
    def __lt__(self, other):
        return self.priority < other.priority

# search tree for the boxes
class SearchTree:

    #constructor
    def __init__(self, mapa):
        self.timer = time.time()
        self.mapa = mapa
        self.size = mapa.size
        self.goals = mapa.filter_tiles([Tiles.GOAL, Tiles.BOX_ON_GOAL, Tiles.MAN_ON_GOAL])

        if self.size[0]*self.size[1]*len(self.goals) >= 600: #will use greedy search
            self.isSimple = False
            self.root = BoxNode((frozenset(mapa.boxes), mapa.keeper), None, "", 0, 1000000)
        else: #will use uniform search
            self.isSimple = True
            self.root = BoxNode((frozenset(mapa.boxes), mapa.keeper), None, "", 0, 0)

        self.open_nodes = [self.root]
        self.visitedNodes = set()
        self.visitedNodes.add(self.root.state)

        self.isWall = [] #True if wall
        self.isBlocked = [] #True if wall or tile results in deadlock
        for x in range(mapa.size[0]):
            self.isWall.append([])
            self.isBlocked.append([])
            for y in range(mapa.size[1]):
                self.isWall[x].append(mapa.get_tile((x,y)) == Tiles.WALL or x==0 or y==0 or x==self.size[0]-1 or y==self.size[1]-1)
                self.isBlocked[x].append(self.isWall[x][y])
        
        #static deadlocks
        self.isWalled_Outer()
        self.isWalled_Inner()
        
        for x in range(1, mapa.size[0]-1):
            for y in range(1, mapa.size[1]-1):
                self.isBlocked[x][y] = True if self.isBlocked[x][y] else self.isCornered((x,y))
        
        #SearchAgent instance (walls are always the same)
        self.agentSearch = SearchAgent(self.isWall)

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

    #get all keys from the root until this node
    async def get_keys(self,node):
        if node.parent == None:
            return ""
        else:
            keys = await self.agentSearch.search(node.parent.state[0], node.parent.state[1], node.destination) #keeper keys
            parentkeys = await self.get_keys(node.parent) #parent keys
            return parentkeys + keys + node.keys #all keys

    #heuristic function
    #for all boxes not on goal get minimum manhattan distance to the closest empty goal
    def heuristic(self, boxes):
        goals = [goal for goal in self.goals if goal not in boxes]
        boxes = [box for box in boxes if box not in self.goals]

        h = 0
        for i in range(len(goals)):
            h += min([abs(boxes[i][0]-goals[j][0]) + abs(boxes[i][1]-goals[j][1]) for j in range(len(goals))])
        
        return h

    #Verify whether a box is directly next a box making them both unable to
    #move in any direction, making the make impossible to complete
    def isBoxed(self, newBoxPos, allBoxPos):
        x, y = newBoxPos
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

    #Detects more complex deadlock states dinamically, verifies according to the following checks:
    #If the box has a box directly above or bellow, it can't move in y axis
    #If the box's bellow and above tiles are deadlock positions, it can't move in y axis
    #If the box has a box next to it potentially blocking its move, checks whether that box is in a deadlock position
    #Repeats these steps for x axis, if both axis are blocked, the state is in deadlock
    def deadlock_detection(self, box, boxesPos, viewedBoxes):
        viewedBoxes.add(box)

        x, y = box
        top = (x, y-1)
        bot = (x, y+1)
        left = (x-1,y)
        right = (x+1,y)

        xDeadlock = False
        yDeadlock = False

        #If the box if blocked by a wall...
        if self.isWall[bot[0]][bot[1]] or bot in viewedBoxes or self.isWall[top[0]][top[1]] or top in viewedBoxes:
            yDeadlock = True
        if not yDeadlock:
            #If both positions next to it are blocked positions...
            if self.isBlocked[bot[0]][bot[1]] and self.isBlocked[top[0]][top[1]]:
                yDeadlock = True
            if not yDeadlock:
                #If there is a box directly below, checks if it is in deadlock
                if bot in boxesPos:
                    yDeadlock = self.deadlock_detection(bot, boxesPos, viewedBoxes)
                if not yDeadlock:
                #If there is a box directly above, checks if it is in deadlock
                    if top in boxesPos:
                        yDeadlock = self.deadlock_detection(top, boxesPos, viewedBoxes)
        
        #If it's not blocked along y axis, it can move so it's not a deadlock, so no need for further verifications
        if not yDeadlock:
            return False

        #If the box if blocked by a wall...
        if self.isWall[right[0]][right[1]] or right in viewedBoxes or self.isWall[left[0]][left[1]] or left in viewedBoxes:
            return True
        #If both positions next to it are blocked positions...
        if self.isBlocked[right[0]][right[1]] and self.isBlocked[left[0]][left[1]]:
            return True
        #If there is a box directly to the right, checks if it is in deadlock
        if right in boxesPos:
            if self.deadlock_detection(right, boxesPos, viewedBoxes):
                return True
        #If there is a box directly to the left, checks if it is in deadlock
        if left in boxesPos:
            if self.deadlock_detection(left, boxesPos, viewedBoxes):
                return True
        #If all four checks are false, it can move either left or right
        return False

    #verify if we have a tunnel in front of the keeper so that the keeper can make more pushes
    #also keeps pushing a box if it is next to a wall and fulfills certains conditions
    def tunnel(self, currBoxPos, newBoxPos, movX, movY, newBoxes, keys):
        if movX == 0: #vertical tunnel
            #if it is on the end of the map return
            if not (0 < newBoxPos[1]+2*movY < self.size[1]):
                return currBoxPos, newBoxPos, keys

            #if box isnt in a goal tile
            if newBoxPos not in self.goals:
                #if the box has a wall to the left or to the right
                if self.isWall[newBoxPos[0]+1][newBoxPos[1]] or self.isWall[newBoxPos[0]-1][newBoxPos[1]]:
                    #if the box will have a wall to the left and to the right in the next tile
                    if self.isWall[newBoxPos[0]+1][newBoxPos[1]+movY] and self.isWall[newBoxPos[0]-1][newBoxPos[1]+movY]:
                        #if the next tile doesn't result in deadlock, isn't a wall and isn't a box 
                        if not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movY] and (newBoxPos[0], newBoxPos[1]+movY) not in newBoxes:
                            currBoxPos, newBoxPos, keys = self.tunnel(newBoxPos, (newBoxPos[0], newBoxPos[1]+movY), movX, movY, newBoxes, keys + keys[-1])
                    
                    #if the box will have a wall only to the right
                    elif self.isWall[newBoxPos[0]+1][newBoxPos[1]+movY]:
                        #if the next tile doesn't have a deadlock, wall or box tile next to it
                        if not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movY*2] and (newBoxPos[0], newBoxPos[1]+movY*2) not in newBoxes:
                            #if the next tile doesn't have a wall or box tile diagonal to it
                            if not self.isWall[newBoxPos[0]-1][newBoxPos[1]+2*movY] and (newBoxPos[0]-1, newBoxPos[1]+movY*2) not in newBoxes:
                                #if the next tile doesn't result in deadlock, isn't a wall and isn't a box
                                if not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movY] and (newBoxPos[0], newBoxPos[1]+movY) not in newBoxes:
                                    #if the current tile doesn't have a box diagonal to it
                                    if (newBoxPos[0]-1, newBoxPos[1]+movY) not in newBoxes:
                                        currBoxPos, newBoxPos, keys = self.tunnel(newBoxPos, (newBoxPos[0], newBoxPos[1]+movY), movX, movY, newBoxes, keys + keys[-1])

                    #if the box will have a wall only to the left
                    elif self.isWall[newBoxPos[0]-1][newBoxPos[1]+movY]:
                        #if the next tile doesn't have a deadlock, wall or box tile next to it
                        if not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movY*2] and (newBoxPos[0], newBoxPos[1]+movY*2) not in newBoxes:
                            #if the next tile doesn't have a wall or box tile diagonal to it
                            if not self.isWall[newBoxPos[0]+1][newBoxPos[1]+2*movY] and (newBoxPos[0]+1, newBoxPos[1]+movY*2) not in newBoxes:
                                #if the next tile doesn't result in deadlock, isn't a wall and isn't a box
                                if not self.isBlocked[newBoxPos[0]][newBoxPos[1]+movY] and (newBoxPos[0], newBoxPos[1]+movY) not in newBoxes:
                                    #if the current tile doesn't have a box diagonal to it
                                    if (newBoxPos[0]+1, newBoxPos[1]+movY) not in newBoxes:
                                        currBoxPos, newBoxPos, keys = self.tunnel(newBoxPos, (newBoxPos[0], newBoxPos[1]+movY), movX, movY, newBoxes, keys + keys[-1])

        else: #horizontal tunnel
            #if it is on the end of the map return
            if not (0 < newBoxPos[0]+2*movX < self.size[0]):
                return currBoxPos, newBoxPos, keys

            #if box isnt in a goal tile
            if newBoxPos not in self.goals:
                #if the box has a wall to the top or to the bottom
                if self.isWall[newBoxPos[0]][newBoxPos[1]+1] or self.isWall[newBoxPos[0]][newBoxPos[1]-1]:
                    #if the box will have a wall to the top and to the bottow in the next tile
                    if self.isWall[newBoxPos[0]+movX][newBoxPos[1]+1] and self.isWall[newBoxPos[0]+movX][newBoxPos[1]-1]:
                        #if the next tile doesn't result in deadlock, isn't a wall and isn't a box 
                        if not self.isBlocked[newBoxPos[0]+movX][newBoxPos[1]] and (newBoxPos[0] + movX, newBoxPos[1]) not in newBoxes:
                            currBoxPos, newBoxPos, keys = self.tunnel(newBoxPos, (newBoxPos[0]+movX, newBoxPos[1]), movX, movY, newBoxes, keys + keys[-1])
                    
                    #if the box will have a wall only to the bottom
                    elif self.isWall[newBoxPos[0]+movX][newBoxPos[1]+1]:
                        #if the next tile doesn't have a deadlock, wall or box tile next to it
                        if not self.isBlocked[newBoxPos[0]+movX*2][newBoxPos[1]] and (newBoxPos[0] + movX*2, newBoxPos[1]) not in newBoxes:
                            #if the next tile doesn't have a wall or box tile diagonal to it
                            if not self.isWall[newBoxPos[0]+2*movX][newBoxPos[1]-1] and (newBoxPos[0] + movX*2, newBoxPos[1]-1) not in newBoxes:
                                #if the next tile doesn't result in deadlock, isn't a wall and isn't a box
                                if not self.isBlocked[newBoxPos[0]+movX][newBoxPos[1]] and (newBoxPos[0] + movX, newBoxPos[1]) not in newBoxes:
                                    #if the current tile doesn't have a box diagonal to it
                                    if (newBoxPos[0] + movX, newBoxPos[1]-1) not in newBoxes:
                                        currBoxPos, newBoxPos, keys = self.tunnel(newBoxPos, (newBoxPos[0]+movX, newBoxPos[1]), movX, movY, newBoxes, keys + keys[-1])

                    #if the box will have a wall only to the top
                    elif self.isWall[newBoxPos[0]+movX][newBoxPos[1]-1]:
                        #if the next tile doesn't have a deadlock, wall or box tile next to it
                        if not self.isBlocked[newBoxPos[0]+movX*2][newBoxPos[1]] and (newBoxPos[0] + movX*2, newBoxPos[1]) not in newBoxes:
                            #if the next tile doesn't have a wall or box tile diagonal to it
                            if not self.isWall[newBoxPos[0]+2*movX][newBoxPos[1]+1] and (newBoxPos[0] + movX*2, newBoxPos[1]+1) not in newBoxes:
                                #if the next tile doesn't result in deadlock, isn't a wall and isn't a box
                                if not self.isBlocked[newBoxPos[0]+movX][newBoxPos[1]] and (newBoxPos[0] + movX, newBoxPos[1]) not in newBoxes:
                                    #if the current tile doesn't have a box diagonal to it
                                    if (newBoxPos[0] + movX, newBoxPos[1]+1) not in newBoxes:
                                        currBoxPos, newBoxPos, keys = self.tunnel(newBoxPos, (newBoxPos[0]+movX, newBoxPos[1]), movX, movY, newBoxes, keys + keys[-1])
                    
        return currBoxPos, newBoxPos, keys
    
    #get a list of tiles that connect different areas of the map, if this tile has a box the keeper can't reach the other area
    async def definePassages(self):
        self.passages = []
        for x in range(2, self.size[0]-2):
            for y in range(2, self.size[1]-2):
                if (x, y) in self.goals or self.isWall[x][y]:
                    continue
                if self.isWall[x+1][y] and self.isWall[x-1][y] and not self.isWall[x][y-1] and not self.isWall[x][y+1]: #vertical
                    if await self.agentSearch.search([(x,y)], (x,y-1), (x, y+1)) == None:
                        self.passages.append((x,y))
                elif not self.isWall[x+1][y] and not self.isWall[x-1][y] and self.isWall[x][y-1] and self.isWall[x][y+1]: #horizontal
                    if await self.agentSearch.search([(x,y)], (x-1,y), (x+1, y)) == None:
                        self.passages.append((x,y))
    
    #try to get a first move that will significantly increase the area the keeper can reach
    async def expandMap(self):
        node = self.open_nodes[0]
        #find the tiles that the keeper can reach
        possibleTiles = await self.agentSearch.getMoves(node.state[0], node.state[1])
        initialSize = len(possibleTiles) #initial number of tiles that the keeper can reach

        options = []
        for box in node.state[0]:
            options.append((box, "d", 1, 0))
            options.append((box, "a", -1, 0))
            options.append((box, "s", 0, 1))
            options.append((box, "w", 0, -1))
        
        for currBoxPos, keys, movX, movY in options:
            newBoxPos = (currBoxPos[0]+movX, currBoxPos[1]+movY)
            newKeeperPos = (currBoxPos[0]-movX, currBoxPos[1]-movY)

            #verify if the keeper reaches the position it needs to be to push the box
            if newKeeperPos not in possibleTiles:
                continue

            #verify if the tile the box will be pushed into doesn't have boxes in it
            if newBoxPos in node.state[0]:
                continue

            #verify if the tile the box will be pushed into isn't a wall or a static deadlock tile
            if self.isBlocked[newBoxPos[0]][newBoxPos[1]]:
                continue

            newBoxes = [b for b in node.state[0] if b != currBoxPos]

            #if the number of boxes is lower than 4, call function isBoxed, if not verify more advanced deadlocks
            if len(self.goals) > 4:
                if self.isBoxed(newBoxPos, newBoxes):
                    continue
            else:
                viewedBoxes = set()
                x = self.deadlock_detection(newBoxPos, newBoxes, viewedBoxes)
                flag = False
                if x:
                    for b in viewedBoxes:
                        if b not in self.goals:
                            flag = True
                            break
                    if flag:
                        continue

            #passage deadlock -> if it has a box in the tiles the box needs to be pushed into
            if newBoxPos in self.passages:
                if (newBoxPos[0]+movX, newBoxPos[1]+movY) not in self.goals and (newBoxPos[0]+movX*2, newBoxPos[1]+movY*2) not in self.goals:
                    if (newBoxPos[0]+movX, newBoxPos[1]+movY) in newBoxes or (newBoxPos[0]+movX*2, newBoxPos[1]+movY*2) in newBoxes:
                        continue

            newBoxes.append(newBoxPos)
            
            newPossibleTiles = await self.agentSearch.getMoves(newBoxes, currBoxPos)
            finalSize = len(newPossibleTiles) #eventual number of tiles that the keeper can reach

            if finalSize > initialSize + 2: #if there are a lot more tiles the keeper can reach
                #give the nodes that result from this move more priority than the others
                #because the root has a very high heuristic
                newnode = BoxNode((frozenset(newBoxes), currBoxPos), node, keys, 0, self.heuristic(newBoxes))
                insort_left(self.open_nodes, newnode)
                self.visitedNodes = set()
                self.visitedNodes.add(newnode.state)
                newnode.destination = newKeeperPos
                return

    #main function -> search for the solution
    async def search(self, limit=None):
        count = 0

        await self.definePassages()

        if not self.isSimple:
            await self.expandMap()

        if len(self.goals) > 4:
            simpleDeadlocks = False
        else:
            simpleDeadlocks = True

        while self.open_nodes != []:
            node = self.open_nodes.pop(0)
            count+=1

            #if we reached the solution of the level
            if all([coord in self.goals for coord in node.state[0]]):
                print("Number of attempts: ", count, "\n")
                print("Time: ", time.time()-self.timer, "\n")
                keys = await self.get_keys(node)
                print(keys)
                return keys

            #find the tiles that the keeper can reach
            possibleTiles = await self.agentSearch.getMoves(node.state[0], node.state[1])

            options = []
            for box in node.state[0]:
                options.append((box, "d", 1, 0))
                options.append((box, "a", -1, 0))
                options.append((box, "s", 0, 1))
                options.append((box, "w", 0, -1))

            for currBoxPos, keys, movX, movY in options:
                newBoxPos = (currBoxPos[0]+movX, currBoxPos[1]+movY)
                newKeeperPos = (currBoxPos[0]-movX, currBoxPos[1]-movY)

                #verify if the keeper reaches the position it needs to be to push the box
                if newKeeperPos not in possibleTiles:
                    continue

                #verify if the tile the box will be pushed into doesn't have boxes in it
                if newBoxPos in node.state[0]:
                    continue

                #verify if the tile the box will be pushed into isn't a wall or a static deadlock tile
                if self.isBlocked[newBoxPos[0]][newBoxPos[1]]:
                    continue

                newBoxes = [b for b in node.state[0] if b != currBoxPos]

                #if the number of boxes is lower than 4, call function isBoxed, if not verify more advanced deadlocks
                if simpleDeadlocks:
                    if self.isBoxed(newBoxPos, newBoxes):
                        continue
                else:
                    viewedBoxes = set()
                    x = self.deadlock_detection(newBoxPos, newBoxes, viewedBoxes)
                    flag = False
                    if x:
                        for b in viewedBoxes:
                            if b not in self.goals:
                                flag = True
                                break
                        if flag:
                            continue
                
                #ideal number of tiles from the keeper to the the tile where he can push the box
                auxCost = abs(node.state[1][0]-newKeeperPos[0]) + abs(node.state[1][1]-newKeeperPos[1])

                #macros
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

                #verify if we are in a new state
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
                #print(currMap)
                ################################################################################################

                cost = len(keys) + auxCost/100 #given the way the score is calculated
                if self.isSimple: #if we are in a simple level -> uniform search
                    newnode = BoxNode((frozenset(newBoxes), currBoxPos), node, keys, node.cost + cost, 0)
                else: #if we are in a harder level -> greedy search
                    newnode = BoxNode((frozenset(newBoxes), currBoxPos), node, keys, 0, self.heuristic(newBoxes))
                newnode.destination = newKeeperPos #save the tile the keeper will need to be to push the box

                #add a node and sort
                insort_left(self.open_nodes, newnode)

        print("----- Box Search Failed -----\n")
        return None
