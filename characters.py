import random
import uuid
import math

DIR = "wasd"
DEFAULT_LIVES = 3

def distance(p1, p2):
    x1,y1 = p1
    x2,y2 = p2
    return math.hypot(x1-x2, y1-y2)

def vector2dir(vx, vy):
    m = max(abs(vx), abs(vy))
    if m == abs(vx):
        if vx < 0:
            d = 1  # a
        else:
            d = 3  # d
    else:
        if vy > 0:
            d = 2  # s
        else:
            d = 0  # w
    return d


class Character:
    def __init__(self, x=1, y=1):
        self._pos = x, y
        self._spawn_pos = self._pos

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = value

    @property
    def x(self):
        return self._pos[0]

    @property
    def y(self):
        return self._pos[1]

    def respawn(self):
        self.pos = self._spawn_pos


class Keeper(Character):
    def __init__(self, pos, lives=DEFAULT_LIVES):
        super().__init__(x=pos[0], y=pos[1])

    def to_dict(self):
        return {"pos": self.pos}

class Box(Character):
    def __init__(self, pos, stored=False):
        super().__init__(x=pos[0], y=pos[1])
        self._stored = stored

    @property
    def stored(self):
        return self._stored

    def to_dict(self):
        return {"pos": self.pos, "stored": self.stored}

