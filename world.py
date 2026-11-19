
import pygame as pyg

from conster import *
from BlockManager import *
from npc import *
from object import *
from camera import Camera


class World:

    def __init__(self, seed, display):
        self.npcs = {}
        self.player = None
        self.seed = seed
        self.display = display
        self.blockManager = BlocksWorld(seed)
        self.blockManager.create(self.display)
        self.camera = Camera(self.blockManager)

    def update(self):
        self.blockManager.update_background_loading(self.display)

        keys = pyg.key.get_pressed()
        for npc_id, (data, contoroler) in self.npcs.items():
            data.getAPI(contoroler.getAPI(keys))
            data.update()

        if self.player:
            self.blockManager.move(-self.player.last_dx, self.player.last_dy)

    def draw(self):
        self.blockManager.drawBlocks(self.display)
        obj.drawObjects(self.display, self.camera.x, self.camera.y)
        NPC.drawNPC(self.camera)

    def get_frame_data(self):
        """
        همه‌ی چیزهایی که رندر C++ لازم دارد، فقط برای آنچه در دوربین است.
        """
        return {
            "camera": (self.camera.x, self.camera.y),
            "npcs": [n.to_render_data(self.camera)
                     for n in NPC.visible_npcs(self.camera)],
            "objects": obj.snapshot(self.camera.x, self.camera.y),
        }

    def newNPC(self, w, h, x, y, color, contoroler=None, player=False):
        if contoroler is None:
            contoroler = NPC_Contoroler()
        npc_id = len(self.npcs) + 1
        npc = NPC(w, h, x, y, self.display, self.blockManager, color, True, player)
        self.npcs[npc_id] = (npc, contoroler)
        if player:
            self.player = npc
        return npc

    def newPlayer(self, w, h, x, y, color, contoroler=None):
        return self.newNPC(w, h, x, y, color, contoroler, True)
