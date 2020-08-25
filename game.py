import asyncio
import json
import logging
import math
import os

import requests

from characters import Keeper, Box
from mapa import Map, Tiles

logger = logging.getLogger("Game")
logger.setLevel(logging.DEBUG)

INITIAL_SCORE = 0
TIMEOUT = 30000
GAME_SPEED = 10

class Game:
    def __init__(self, level=1, timeout=TIMEOUT):
        logger.info(f"Game(level={level})")
        self.initial_level = level
        self._running = False
        self._timeout = timeout
        self._score = 0
        self._step = 0
        self._total_steps = 0
        self._state = {}

    def info(self):
        return {
            "fps": GAME_SPEED,
            "timeout": TIMEOUT,
            "score": self.score,
            "map": f"levels/{self.initial_level}.xsb",
        }

    @property
    def running(self):
        return self._running

    @property
    def score(self):
        return self._score

    @property
    def total_steps(self):
        return self._total_steps

    def start(self, player_name):
        logger.debug("Reset world")
        self._player_name = player_name
        self._running = True
        self._total_steps = 0
        self._score = INITIAL_SCORE

        self.next_level(self.initial_level)

    def stop(self):
        logger.info("GAME OVER")
        self._total_steps += self._step
        self._running = False

    def next_level(self, level):
        self.level = level
        if level > 1:   #TODO determinar fim do jogo
            logger.info("You WIN!")
            self.stop()
            return

        logger.info("NEXT LEVEL")
        self.map = Map(f"levels/{level}.xsb")
        self._total_steps += self._step
        self._step = 0
        self._lastkeypress = ""

    def quit(self):
        logger.debug("Quit")
        self._running = False

    def keypress(self, key):
        self._lastkeypress = key

    def update_keeper(self):
        try:
            # Update position
            self.map.move(self.map.keeper, self._lastkeypress)
        except AssertionError:
            logger.error(
                "Invalid key <%s> pressed. Valid keys: w,a,s,d", self._lastkeypress
            )
        finally:
            self._lastkeypress = ""  # remove inertia

        if self.map.completed:
            logger.info(f"Level {self.level} completed")
            self.next_level(self.level + 1)

    async def next_frame(self):
        await asyncio.sleep(1.0 / GAME_SPEED)

        if not self._running:
            logger.info("Waiting for player 1")
            return

        self._step += 1
        if self._step == self._timeout:
            self.stop()

        if self._step % 100 == 0:
            logger.debug(
                f"[{self._step}] SCORE {self._score}"
            )

        self.update_keeper()

        self._state = {
            "level": self.level,
            "step": self._step,
            "timeout": self._timeout,
            "player": self._player_name,
            "score": self._score,
            "keeper": self.map.keeper,
            "boxes": self.map.boxes,
        }

    @property
    def state(self):
        #logger.debug(self._state)
        return json.dumps(self._state)
