import os
import logging
import random
from functools import reduce
from operator import add

from consts import Tiles, TILES

logger = logging.getLogger("Map")
logger.setLevel(logging.DEBUG)


class Map:
    def __init__(self, filename):
        self._map = []
        self._level = filename
        self._keeper = None
        self._boxes = None

        with open(filename, "r") as f:
            for line in f:
                codedline = []
                for c in line.strip():
                    assert c in TILES, f"Invalid character '{c}' in map file"
                    tile = TILES[c]
                    codedline.append(tile)

                self._map.append(codedline)

        self.hor_tiles, self.ver_tiles = len(self._map[0]), len(self._map)  # X, Y

    def __str__(self):
        map_str = ""
        screen = {tile: symbol for symbol, tile in TILES.items()}
        for line in self._map:
            for tile in line:
                map_str += screen[tile]
            map_str += "\n"

        return map_str.strip()

    def __getstate__(self):
        return self._map

    def __setstate__(self, state):
        self._map = state
        self._keeper = None
        self._boxes = None
        self.hor_tiles, self.ver_tiles = len(self._map[0]), len(self._map)  # X, Y

    @property
    def size(self):
        return self.hor_tiles, self.ver_tiles

    @property
    def completed(self):
        """Map is completed when there are no BOX not ON GOAL."""
        return self.filter_tiles([Tiles.BOX]) == []

    @property
    def on_goal(self):
        """Number of boxes on goal.

           Counts per line and counts all lines using reduce
        """
        return reduce(
            add,
            [
                reduce(lambda a, b: a + int(b is Tiles.BOX_ON_GOAL), l, 0)
                for l in self._map
            ],
        )

    def filter_tiles(self, list_to_filter):
        return [
            (x, y)
            for y, l in enumerate(self._map)
            for x, tile in enumerate(l)
            if tile in list_to_filter
        ]

    @property
    def keeper(self):
        if self._keeper is None:
            self._keeper = self.filter_tiles([Tiles.MAN])[0]

        return self._keeper

    @property
    def boxes(self):
        if self._boxes is None:
            self._boxes = self.filter_tiles([Tiles.BOX, Tiles.BOX_ON_GOAL])
        return self._boxes

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

    def move(self, cur, direction):
        assert (
            direction in "wasd" or direction == ""
        ), f"Can't move in {direction} direction"

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
        if self.get_tile(npos) in [
            Tiles.BOX,
            Tiles.BOX_ON_GOAL,
        ]:  # next position has a box?
            if ctile & Tiles.MAN == Tiles.MAN:  # if you are the keeper you can push
                if not self.move(npos, direction):  # as long as the pushed box can move
                    return False
            else:  # you are not the Keeper, so no pushing
                return False

        # actually update map
        self._map[cy][cx] = ctile & 1
        nx, ny = npos
        self._map[ny][nx] = self.get_tile(npos) | ctile

        if ctile & Tiles.MAN == Tiles.MAN:
            self._keeper = npos
        if ctile & Tiles.BOX in [Tiles.BOX, Tiles.BOX_ON_GOAL]:
            idx = self._boxes.index(cur)
            self._boxes[idx] = npos

        return True


if __name__ == "__main__":
    mapa = Map("levels/2.xsb")
    print(mapa)
    assert mapa.keeper == (11, 8)
    assert mapa.get_tile((4, 2)) == Tiles.WALL
    assert mapa.get_tile((5, 2)) == Tiles.BOX
    assert mapa.get_tile((2, 7)) == Tiles.BOX
    assert mapa.get_tile(mapa.keeper) == Tiles.MAN
    print("")
    assert mapa.move(mapa.keeper, "w")
    assert mapa.move(mapa.keeper, "d")
    assert mapa.move(mapa.keeper, "d")
    assert mapa.move(mapa.keeper, "d")
    assert mapa.move(mapa.keeper, "d")
    assert mapa.move(mapa.keeper, "d")
    print(mapa)
    assert mapa.keeper == (16, 7)
    assert not mapa.move(mapa.keeper, "d")  # can't push any further
    assert mapa.get_tile((17, 7)) == Tiles.BOX_ON_GOAL
    assert mapa.on_goal == 1
    assert mapa.boxes == [(5, 2), (7, 3), (5, 4), (7, 4), (2, 7), (17, 7)]
