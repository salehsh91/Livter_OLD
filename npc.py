import conster
from cppfuncs import EntityData, RenderEntities, DrawObj, GetRenderer
from object import obj

class NPC:
    npcs = []
    _entity_array = None
    _entity_capacity = 0

    @classmethod
    def activate(cls, entities, pointer_type=None, max_entities=0):
        # The pointer is allocated by C++ and its layout is EntityData above.
        cls._entity_array = entities
        cls._entity_capacity = int(max_entities)
        cls.npcs.clear()

    def __init__(self, w, h, x, y, display=None, world=None,
                 color=None, center=False, move=False, texture=None):
        self.id = len(self.npcs) + 1
        self.width = float(w)
        self.height = float(h)
        self.display = display
        self.world = world
        self.health = 100
        self.hungry = 100
        self.world_x = float(x)
        self.world_y = float(y)
        self.world_z = 0
        self.last_dx = 0.0
        self.last_dy = 0.0
        self.move = move
        self.center = center
        self.direction = (0, 1)
        self.texture = conster.DEFAULT_NPC_TEXTURE if texture is None else int(texture)
        self.npcs.append(self)

    def getAPI(self, api):
        if not api:
            self.last_dx = self.last_dy = 0.0
            return
        dx = float(api.get("x", 0.0)) * conster.NPC_SPEED
        dy = float(api.get("y", 0.0)) * conster.NPC_SPEED
        if dx or dy:
            self.direction = (api.get("x", 0.0), api.get("y", 0.0))
        self.world_x += dx
        self.world_y += dy
        self.last_dx, self.last_dy = dx, dy

        action = int(api.get("drap", 0) or 0)
        if action > 0:
            self.drap()
        elif action < 0:
            self.undrap()

    def drap(self):
        if self.world is None:
            return False
        x, y = self.directionManager()
        ox, oy = self.world.base_x, self.world.base_y
        z = obj.zblock(x, y, 0, 0, ox, oy, True)
        return obj(x, y, z, name="plank", offset_x=ox, offset_y=oy).create()

    def undrap(self):
        if self.world is None:
            return False
        x, y = self.directionManager()
        return obj.remove(
            x, y, offset_x=self.world.base_x, offset_y=self.world.base_y
        )[0]

    def update(self):
        pass

    def directionManager(self):
        ox, oy = self.world.base_x, self.world.base_y
        cx = self.world_x + self.width / 2
        cy = self.world_y + self.height / 2
        x = ox + ((cx - ox) // conster.BLOCK_SIZE) * conster.BLOCK_SIZE
        y = oy + ((cy - oy) // conster.BLOCK_SIZE) * conster.BLOCK_SIZE
        dx, dy = self.direction
        if dx > 0: x += conster.BLOCK_SIZE
        elif dx < 0: x -= conster.BLOCK_SIZE
        if dy > 0: y += conster.BLOCK_SIZE
        elif dy < 0: y -= conster.BLOCK_SIZE
        return x, y

    def getStatus(self):
        return {
            "health": self.health, "hungry": self.hungry,
            "x": self.world_x, "y": self.world_y,
        }

    def is_visible(self, camera, margin=0):
        return camera.is_visible(
            self.world_x, self.world_y, self.width, self.height, margin
        )

    def to_render_data(self, camera):
        sx, sy = camera.world_to_screen(self.world_x, self.world_y)
        return (self.id, sx, sy, self.width, self.height, self.texture)

    @classmethod
    def visible_npcs(cls, camera, margin=0):
        return [npc for npc in cls.npcs if npc.is_visible(camera, margin)]

    @classmethod
    def sync_entities(cls, camera):
        if cls._entity_array is None:
            return
        for index in range(cls._entity_capacity):
            cls._entity_array[index].active = 0
        write_index = 0
        for npc in cls.npcs:
            if write_index >= cls._entity_capacity:
                break
            if not npc.is_visible(camera):
                continue
            data = cls._entity_array[write_index]
            write_index += 1
            data.kind = 1
            data.active = 1
            data.id = npc.id
            data.world_x = npc.world_x
            data.world_y = npc.world_y
            data.world_z = npc.world_z
            data.texture = npc.texture
            data.width = npc.width
            data.height = npc.height
            data.length = 0.0
            data.bx = camera.x
            data.by = camera.y
            data.display_alpha = 1.0

    @classmethod
    def render_entities(cls, camera):
        cls.sync_entities(camera)
        if RenderEntities is not None:
            RenderEntities()
            return
        # Compatibility path for the DLL already included in the uploaded ZIP.
        renderer = GetRenderer()
        for npc in cls.npcs:
            if npc.is_visible(camera):
                DrawObj(
                    renderer,
                    npc.world_x + camera.x,
                    npc.world_y + camera.y,
                    npc.width,
                    npc.height,
                    npc.texture,
                )

class NPC_Contoroler:
    """Legacy-compatible controller; the active SDL controller lives in contoroler.py."""
    def getAPI(self, keys=None):
        return {"x": 0, "y": 0, "drap": 0}
