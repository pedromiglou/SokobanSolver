import os
import asyncio
import pygame
import random
from functools import partial
import json
import asyncio
import websockets
import logging
import argparse
import time
from mapa import Map, Tiles

logging.basicConfig(level=logging.DEBUG)
logger_websockets = logging.getLogger("websockets")
logger_websockets.setLevel(logging.WARN)

logger = logging.getLogger("Map")
logger.setLevel(logging.DEBUG)

KEEPER = {
    "up": (3 * 64, 4 * 64),
    "left": (3 * 64, 6 * 64),
    "down": (0, 4 * 64),
    "right": (0, 6 * 64),
}
BOX = (7 * 64, 0)
GOAL = (12 * 64, 5 * 64)
WALL = (8 * 64, 6 * 64)
PASSAGE = (12 * 64, 6 * 64)

CHAR_LENGTH = 64
CHAR_SIZE = CHAR_LENGTH, CHAR_LENGTH
SCALE = 1

COLORS = {
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "pink": (255, 105, 180),
    "blue": (135, 206, 235),
    "orange": (255, 165, 0),
    "yellow": (255, 255, 0),
    "grey": (120, 120, 120),
}
BACKGROUND = (0, 0, 0)
RANKS = {
    1: "1ST",
    2: "2ND",
    3: "3RD",
    4: "4TH",
    5: "5TH",
    6: "6TH",
    7: "7TH",
    8: "8TH",
    9: "9TH",
    10: "10TH",
}

SPRITES = None


async def messages_handler(ws_path, queue):
    async with websockets.connect(ws_path) as websocket:
        await websocket.send(json.dumps({"cmd": "join"}))

        while True:
            r = await websocket.recv()
            queue.put_nowait(r)


class GameOver(BaseException):
    pass


class Artifact(pygame.sprite.Sprite):
    def __init__(self, *args, **kw):
        self.x, self.y = None, None  # postpone to update_sprite()

        x, y = kw.pop("pos", ((kw.pop("x", 0), kw.pop("y", 0))))
        new_pos = scale((x, y))
        self.image = pygame.Surface(CHAR_SIZE)
        self.rect = pygame.Rect(new_pos + CHAR_SIZE)
        self.update_sprite((x, y))
        super().__init__()

    def update_sprite(self, pos=None):
        if not pos:
            pos = self.x, self.y
        else:
            pos = scale(pos)
        self.rect = pygame.Rect(pos + CHAR_SIZE)
        self.image.fill((0, 0, 230))
        self.image.blit(SPRITES, (0,0), (*PASSAGE, *scale((1, 1))))
        self.image.blit(*self.sprite)
        # self.image = pygame.transform.scale(self.image, scale((1, 1)))
        self.x, self.y = pos

    def update(self, *args):
        self.update_sprite()


class Keeper(Artifact):
    def __init__(self, *args, **kw):
        self.direction = "left"
        self.sprite = (SPRITES, (0, 0), (*KEEPER[self.direction], *scale((1, 1))))
        super().__init__(*args, **kw)

    def update(self, new_pos):
        x, y = scale(new_pos)

        if x > self.x:
            self.direction = "right"
        if x < self.x:
            self.direction = "left"
        if y > self.y:
            self.direction = "down"
        if y < self.y:
            self.direction = "up"

        self.sprite = (SPRITES, (0, 0), (*KEEPER[self.direction], *scale((1, 1))))
        self.update_sprite(tuple(new_pos))

class Wall(Artifact):
    def __init__(self, *args, **kw):
        self.sprite = (SPRITES, (0, 0), (*WALL, *scale((1, 1))))
        super().__init__(*args, **kw)

class Box(Artifact):
    def __init__(self, *args, **kw):
        self.sprite = (SPRITES, (0, 0), (*BOX, *scale((1, 1))))
        super().__init__(*args, **kw)


def clear_callback(surf, rect):
    """beneath everything there is a passage."""
    surf.blit(SPRITES, (rect.x, rect.y), (*PASSAGE, rect.width, rect.height))


def scale(pos):
    x, y = pos
    return int(x * CHAR_LENGTH / SCALE), int(y * CHAR_LENGTH / SCALE)


def draw_background(mapa):
    background = pygame.Surface(scale(mapa.size))
    for x in range(mapa.size[0]):
        for y in range(mapa.size[1]):
            wx, wy = scale((x, y))
            background.blit(SPRITES, (wx, wy), (*PASSAGE, *scale((1, 1))))
            if mapa.get_tile((x,y)) == Tiles.WALL:
                background.blit(SPRITES, (wx, wy), (*WALL, *scale((1, 1))))
            if mapa.get_tile((x,y)) == Tiles.GOAL:
                background.blit(SPRITES, (wx, wy), (*GOAL, *scale((1, 1))))

    return background


def draw_info(SCREEN, text, pos, color=(0, 0, 0), background=None):
    myfont = pygame.font.Font(None, int(22 / SCALE))
    textsurface = myfont.render(text, True, color, background)

    x, y = pos
    if x > SCREEN.get_width():
        pos = SCREEN.get_width() - (textsurface.get_width() +10), y
    if y > SCREEN.get_height():
        pos = x, SCREEN.get_height() - textsurface.get_height()

    if background:
        SCREEN.blit(background, pos)
    else:
        erase = pygame.Surface(textsurface.get_size())
        erase.fill(COLORS["grey"])

    SCREEN.blit(textsurface, pos)
    return textsurface.get_width(), textsurface.get_height()

async def main_loop(q):
    while True:
        await main_game()


async def main_game():
    global SPRITES, SCREEN

    main_group = pygame.sprite.LayeredUpdates()
    boxes_group = pygame.sprite.OrderedUpdates()

    logging.info("Waiting for map information from server")
    state = await q.get()  # first state message includes map information
    logging.debug("Initial game status: %s", state)
    newgame_json = json.loads(state)

    import pprint
    pprint.pprint(newgame_json)

    GAME_SPEED = newgame_json["fps"]
    mapa = Map(newgame_json["map"])
    TIMEOUT = newgame_json["timeout"]
    SCREEN = pygame.display.set_mode(scale(mapa.size))
    SPRITES = pygame.image.load("data/sokoban.png").convert_alpha()

    BACKGROUND = draw_background(mapa)
    SCREEN.blit(BACKGROUND, (0, 0))
    main_group.add(Keeper(pos=mapa.keeper))

    state = {"score": 0, "player": "player1", "keeper": mapa.keeper, "boxes": mapa.boxes}

    while True:
        SCREEN.blit(BACKGROUND, (0, 0))
        pygame.event.pump()
        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            asyncio.get_event_loop().stop()

        main_group.clear(SCREEN, clear_callback)
        boxes_group.clear(SCREEN, clear_callback)

        if "score" in state and "player" in state:
            text = str(state["score"])
            draw_info(SCREEN, text.zfill(6), (5, 1))
            text = str(state["player"]).rjust(32)
            draw_info(SCREEN, text, (4000, 1))

        if "level" in state:
            w,_ = draw_info(SCREEN, "level: ", (2*SCREEN.get_width()/4 ,1))        
            draw_info(SCREEN, f"{state['level']}", (2*SCREEN.get_width()/4 + w,1),color=(255, 0, 0))
        
        if "step" in state:
            w,_ = draw_info(SCREEN, "steps: ", (3*SCREEN.get_width()/4,1))
            draw_info(SCREEN, f"{state['step']}", (3*SCREEN.get_width()/4 + w ,1),color=(255, 0, 0))               

        if "boxes" in state:
            boxes_group.empty()
            for box in state["boxes"]:
                boxes_group.add(Box(pos=box))

        boxes_group.draw(SCREEN)
        main_group.draw(SCREEN)

        # Highscores Board
        if (
            ("step" in state and state["step"] >= TIMEOUT)
            or (
                "keeper" in state
                and "exit" in state
                and state["keeper"] == state["exit"]
            )
        ):
            highscores = newgame_json["highscores"]
            if (f"<{state['player']}>", state["score"]) not in highscores:
                highscores.append((f"<{state['player']}>", state["score"]))
            highscores = sorted(highscores, key=lambda s: s[1], reverse=True)[:-1]
            highscores = highscores[:len(RANKS)]

            HIGHSCORES = pygame.Surface(scale((20, 16)))
            HIGHSCORES.fill(COLORS["grey"])

            draw_info(HIGHSCORES, "THE 10 BEST PLAYERS", scale((5, 1)), COLORS["white"])
            draw_info(HIGHSCORES, "RANK", scale((2, 3)), COLORS["orange"])
            draw_info(HIGHSCORES, "SCORE", scale((6, 3)), COLORS["orange"])
            draw_info(HIGHSCORES, "NAME", scale((11, 3)), COLORS["orange"])

            for i, highscore in enumerate(highscores):
                c = (i % 5) + 1
                draw_info(
                    HIGHSCORES,
                    RANKS[i + 1],
                    scale((2, i + 5)),
                    list(COLORS.values())[c],
                )
                draw_info(
                    HIGHSCORES,
                    str(highscore[1]),
                    scale((6, i + 5)),
                    list(COLORS.values())[c],
                )
                draw_info(
                    HIGHSCORES,
                    highscore[0],
                    scale((11, i + 5)),
                    list(COLORS.values())[c],
                )

            SCREEN.blit(
                HIGHSCORES,
                (
                    (SCREEN.get_width() - HIGHSCORES.get_width()) / 2,
                    (SCREEN.get_height() - HIGHSCORES.get_height()) / 2,
                ),
            )

        if "keeper" in state:
            main_group.update(state["keeper"])

        pygame.display.flip()

        try:
            state = json.loads(q.get_nowait())

            if (
                "step" in state
                and state["step"] == 1
            ):

                # New level! lets clean everything up!
                SCREEN.blit(BACKGROUND, (0, 0))

                boxes_group.empty()
                main_group.empty()
                main_group.add(Keeper(pos=mapa.keeper))
                mapa.level = state["level"]

        except asyncio.queues.QueueEmpty:
            await asyncio.sleep(1.0 / GAME_SPEED)
            continue


if __name__ == "__main__":
    SERVER = os.environ.get("SERVER", "localhost")
    PORT = os.environ.get("PORT", "8000")

    parser = argparse.ArgumentParser()
    parser.add_argument("--server", help="IP address of the server", default=SERVER)
    parser.add_argument(
        "--scale", help="reduce size of window by x times", type=int, default=1
    )
    parser.add_argument("--port", help="TCP port", type=int, default=PORT)
    args = parser.parse_args()
    SCALE = args.scale

    LOOP = asyncio.get_event_loop()
    pygame.font.init()
    q = asyncio.Queue()

    ws_path = f"ws://{args.server}:{args.port}/viewer"

    try:
        LOOP.run_until_complete(
            asyncio.gather(messages_handler(ws_path, q), main_loop(q))
        )
    finally:
        LOOP.stop()
