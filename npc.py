
import pygame as pyg

from conster import *
from object import obj


class NPC:

    npcs = []

    def __init__(self, w, h, x, y, display, world, color=COLORS["RED"],
                 center=False, move=False):
        self.id = len(self.npcs) + 1
        self.color = color
        self.width = w
        self.height = h
        self.display = display
        self.realx = x
        self.realy = y
        self.world = world              # BlocksWorld
        self.health = 100
        self.hungry = 0
        self.world_x = x
        self.world_y = y
        self.last_dx = 0
        self.last_dy = 0
        self.move = move
        self.direction = (0, 1)
        self.npcs.append(self)

    # ------------------------------------------------------------------
    # API استاندارد (همان ورودی‌ای که بعداً مدل PyTorch هم می‌دهد)
    # API = {"x": -1..1, "y": -1..1, "drap": bool}
    # ------------------------------------------------------------------
    def getAPI(self, API):
        if API is None:
            self.last_dx = 0
            self.last_dy = 0
            return

        x = API["x"] * NPC_SPEED
        y = API["y"] * NPC_SPEED

        # جهت فقط وقتی عوض می‌شود که حرکتی باشد (قبلاً با ایستادن (0,0) می‌شد)
        if API["x"] != 0 or API["y"] != 0:
            self.direction = (API["x"], API["y"])

        self.world_x += x
        self.world_y += y
        self.last_dx = x
        self.last_dy = y

        if API["drap"]:
            self.drap()

    def drap(self):
        x, y = self.directionManager()
        ox, oy = self.world.base_x, self.world.base_y
        z = obj.zblock(x, y, 0, 0, ox, oy, True)
        item = obj(x, y, z, name="plank", offset_x=ox, offset_y=oy)
        return item.create()

    def update(self):
        pass

    def directionManager(self):
        # سلول زیر مرکز NPC، هم‌تراز با شبکه‌ی بلوک‌های جهان
        ox, oy = self.world.base_x, self.world.base_y
        cx = self.world_x + self.width / 2
        cy = self.world_y + self.height / 2
        x = ox + ((cx - ox) // BLOCK_SIZE) * BLOCK_SIZE
        y = oy + ((cy - oy) // BLOCK_SIZE) * BLOCK_SIZE

        dx, dy = self.direction
        if dx > 0:
            x += BLOCK_SIZE
        elif dx < 0:
            x -= BLOCK_SIZE
        if dy > 0:
            y += BLOCK_SIZE
        elif dy < 0:
            y -= BLOCK_SIZE
        return x, y

    def getStatus(self):
        return {"health": self.health, "hungry": self.hungry,
                "x": self.world_x, "y": self.world_y}

    # ------------------------------------------------------------------
    # دوربین
    # ------------------------------------------------------------------
    def is_visible(self, camera, margin=0):
        return camera.is_visible(self.world_x, self.world_y,
                                 self.width, self.height, margin)

    def to_render_data(self, camera):
        """یک ردیف ساده برای ارسال به رندر C++ (مختصات صفحه)"""
        sx, sy = camera.world_to_screen(self.world_x, self.world_y)
        return (self.id, sx, sy, self.width, self.height, self.color)

    @classmethod
    def visible_npcs(cls, camera, margin=0):
        return [n for n in cls.npcs if n.is_visible(camera, margin)]

    @classmethod
    def drawNPC(cls, camera=None):
        for npc in cls.npcs:
            if camera is not None:
                if not npc.is_visible(camera):
                    continue
                sx, sy = camera.world_to_screen(npc.world_x, npc.world_y)
            else:
                sx = npc.world_x + npc.world.bx
                sy = npc.world_y + npc.world.by
            pyg.draw.rect(npc.display, npc.color,
                          (sx, sy, npc.width, npc.height))


class NPC_Contoroler:

    def __init__(self, up=pyg.K_w, down=pyg.K_s, left=pyg.K_a, right=pyg.K_d,
                 drap=pyg.K_e, s=True):
        self.key_up = up
        self.key_down = down
        self.key_left = left
        self.key_right = right
        self.key_drap = drap
        self.s = s

    def getAPI(self, keys):
        x = 0
        y = 0
        if keys[self.key_up]:
            y -= 1
        if keys[self.key_down]:
            y += 1
        if keys[self.key_left]:
            x -= 1
        if keys[self.key_right]:
            x += 1
        api = {"x": x, "y": y, "drap": bool(keys[self.key_drap])}
        if self.s:
            return api
        return None
