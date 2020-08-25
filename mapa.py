import os
import logging
import random
from enum import IntFlag

logger = logging.getLogger("Map")
logger.setLevel(logging.DEBUG)


class Tiles(IntFlag):
    FLOOR = 0   # -
    GOAL = 1    # .
    MAN = 2     # @
    MAN_ON_GOAL = 3 # +
    BOX = 4     # $
    BOX_ON_GOAL = 5 # *
    WALL = 8    # #

TILES = {
    '-': Tiles.FLOOR,
    '.': Tiles.GOAL,
    '@': Tiles.MAN,
    '+': Tiles.MAN_ON_GOAL,
    '$': Tiles.BOX,
    '*': Tiles.BOX_ON_GOAL,
    '#': Tiles.WALL
        }


class Map:
    def __init__(self, filename):
        self._map = []
        self._level = filename
        self._keeper = None 

        with open(filename, 'r') as f:
            for line in f:
                codedline = []
                for c in line.strip():
                    assert c in TILES
                    tile = TILES[c]
                    codedline.append(tile)

                self._map.append(codedline)

        self._size = len(self._map[0]), len(self._map) # X, Y
        self.hor_tiles, self.ver_tiles = self._size


    def __str__(self):
        map_str = ""
        screen = {y:x for x,y in TILES.items()}
        for line in self._map:
            for c in line:
                map_str += screen[c]
            map_str += '\n'

        return map_str.strip()

    def __getstate__(self):
        return self._map

    def __setstate__(self, state):
        self._map = state

    @property
    def size(self):
        return self._size

    @property
    def completed(self):
        for l in self._map:
            for c in l:
                if c == Tiles.BOX:
                    return False
        return True

    @property
    def keeper(self):
        if self._keeper is None:
            # locate where we start
            y = 0
            for l in self._map:
                x = 0
                for tile in l:
                    if tile == Tiles.MAN:
                        self._keeper = x, y
                    x+=1
                y+=1

        return self._keeper
    
    @property
    def boxes(self):
        #TODO: don't search for boxes all the time (do the same as keeper)

        boxes = []
        y = 0
        for l in self._map:
            x = 0
            for tile in l:
                if tile in [Tiles.BOX, Tiles.BOX_ON_GOAL]:
                    boxes.append((x,y))
                x+=1
            y+=1
        print(boxes)
        return boxes

    def get_tile(self, pos):
        x, y = pos
        return self._map[y][x]

    def is_blocked(self, pos):
        x, y = pos
        if x not in range(self.hor_tiles) or y not in range(self.ver_tiles):
            logger.error("Position out of map")
            return True
        if self._map[y][x] in [Tiles.WALL]:
            logger.debug("Position is a wall")
            return True
        return False

    def is_wall(self, pos):
        x, y = pos
        if x >= self.hor_tiles or y >= self.ver_tiles: #everything outside of map is a WALL
            return True
        return self._map[x][y] in [Tiles.WALL]

    def move(self, cur, direction):
        assert direction in "wasd" or direction == ""

        cx, cy = cur
        ctile = self.get_tile(cur)

        npos = cur
        if direction == "w":
            npos = cx, cy - 1
        if direction == "a":
            npos = cx - 1, cy
        if direction == "s":
            npos = cx, cy + 1
        if direction == "d":
            npos = cx + 1, cy

        # test blocked
        if self.is_blocked(npos):
            logger.debug("Blocked ahead")
            return False
        if self.get_tile(npos) in [Tiles.BOX, Tiles.BOX_ON_GOAL]: #next position has a box?
            if ctile & Tiles.MAN == Tiles.MAN: #if you are the keeper you can push
                if not self.move(npos, direction): #as long as the pushed box can move
                    return False
            else: #you are not the Keeper, so no pushing
                return False
        
        # actually update map
        self._map[cy][cx] = ctile & 1
        nx, ny = npos
        self._map[ny][nx] = self.get_tile(npos) | ctile

        if ctile & Tiles.MAN == Tiles.MAN:
            self._keeper = npos

        return True


if __name__ == "__main__":
    mapa = Map('levels/1.xsb')
    print(mapa)
    assert mapa.keeper == (11,8)
    assert mapa.get_tile((4,2)) == Tiles.WALL
    assert mapa.get_tile((5,2)) == Tiles.BOX
    assert mapa.get_tile((2,7)) == Tiles.BOX
    assert mapa.get_tile(mapa.keeper) == Tiles.MAN

    assert mapa.move(mapa.keeper, 'w')
    assert mapa.move(mapa.keeper, 'd')
    assert mapa.move(mapa.keeper, 'd')
    assert mapa.move(mapa.keeper, 'd')
    assert mapa.move(mapa.keeper, 'd')
    assert mapa.move(mapa.keeper, 'd')
    print(mapa)
    assert mapa.keeper == (16,7)
    assert not mapa.move(mapa.keeper, 'd') #can't push any further
    assert mapa.get_tile((17,7)) == Tiles.BOX_ON_GOAL

