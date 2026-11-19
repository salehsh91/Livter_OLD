import conster
from BlockManager import BlocksWorld
from camera import Camera
from cppfuncs import (
    DrawObj, GetRenderer, RenderFrame, present,
)
from npc import NPC, NPC_Contoroler
from object import obj
from hud import HUD
from inventory import Invertory

class World:
    def __init__(self, seed, display=None):
        self.seed = int(seed)
        self.display = display
        self.npcs = {}
        self.player = None
        self.blockManager = BlocksWorld(self.seed)
        self.blockManager.create()
        self.camera = Camera(self.blockManager)
        self.inventory = Invertory()
        self.hud = HUD(self.inventory)

    def update(self):
        # render() polls SDL events and clears the frame. Input must be read
        # after this call because keycont uses the current SDL event frame.
        if not RenderFrame():
            return False

        self.blockManager.update_background_loading()
        for npc_id, (data, controller) in list(self.npcs.items()):
            api = controller.getAPI()
            data.getAPI(api)
            data.cameradir = float(api.get("cameradir", 0.0))
            data.update()

        if self.player:
            self.blockManager.move(
                -self.player.last_dx,
                -self.player.last_dy,
            )
        return True

    def draw(self):
        self.blockManager.render_cpp()

        # Objects are drawn through SDL3 too; no pygame surface is involved.
        renderer = GetRenderer()
        for item in sorted(
            obj.objs.values(),
            key=lambda value: (value.world_z, value.world_y),
        ):
            if item.is_visible(self.camera.x, self.camera.y):
                DrawObj(
                    renderer,
                    item.world_x + self.camera.x,
                    item.world_y + self.camera.y,
                    item.width,
                    item.height,
                    item.texture,
                )

        NPC.render_entities(self.camera)
        self.hud.draw(self.player)
        present()

    def get_frame_data(self):
        return {
            "camera": (self.camera.x, self.camera.y),
            "npcs": [
                npc.to_render_data(self.camera)
                for npc in NPC.visible_npcs(self.camera)
            ] if hasattr(NPC, "visible_npcs") else [
                npc.to_render_data(self.camera)
                for npc in NPC.npcs if npc.is_visible(self.camera)
            ],
            "objects": obj.snapshot(self.camera.x, self.camera.y),
        }

    def newNPC(self, w, h, x, y, color=None, contoroler=None, player=False):
        if contoroler is None:
            contoroler = NPC_Contoroler()
        npc = NPC(
            w, h, x, y, None, self.blockManager, color,
            center=player, move=player, texture=color,
        )
        npc_id = npc.id
        self.npcs[npc_id] = (npc, contoroler)
        if player:
            self.player = npc
        return npc

    def newPlayer(self, w, h, x, y, color, contoroler=None):
        return self.newNPC(w, h, x, y, color, contoroler, True)
