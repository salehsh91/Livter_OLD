import conster
from blockitem import Block
from cppfuncs import DrawObj, GetRenderer

class obj:
    objs = {}
    _next_id = 1

    def __init__(self, x, y, z=0, objwidth=None, objheight=None,
                 name="plank", offset_x=0, offset_y=0):
        self.world_x = offset_x + ((x - offset_x) // conster.BLOCK_SIZE) * conster.BLOCK_SIZE
        self.world_y = offset_y + ((y - offset_y) // conster.BLOCK_SIZE) * conster.BLOCK_SIZE
        self.world_z = int(z)
        self.width = conster.BLOCK_SIZE if objwidth is None else objwidth
        self.height = conster.BLOCK_SIZE if objheight is None else objheight
        self.base_x = offset_x
        self.base_y = offset_y
        block = Block.getblock_status(name=name)
        self.block_id = block.id
        self.texture = block.texture
        self.type = block.type
        self.name = block.name
        self.id = None

    def create(self):
        for existing in self.objs.values():
            if (self.world_x == existing.world_x
                    and self.world_y == existing.world_y
                    and self.world_z == existing.world_z):
                return False
        self.id = obj._next_id
        obj._next_id += 1
        self.objs[self.id] = self
        return True

    @classmethod
    def remove(cls, x, y, world_z=None, objwidth=None, objheight=None,
               name=None, offset_x=0, offset_y=0, autogrand=False):
        wx = offset_x + ((x - offset_x) // conster.BLOCK_SIZE) * conster.BLOCK_SIZE
        wy = offset_y + ((y - offset_y) // conster.BLOCK_SIZE) * conster.BLOCK_SIZE
        for oid, item in list(cls.objs.items()):
            if item.world_x == wx and item.world_y == wy:
                if world_z is not None and item.world_z != world_z:
                    continue
                if name is not None and item.name != name:
                    continue
                del cls.objs[oid]
                return True, item.name
        return False, None

    @classmethod
    def zblock(cls, x, y, playerz=0, playerl=0,
               offset_x=0, offset_y=0, autoGround=True):
        wx = offset_x + ((x - offset_x) // conster.BLOCK_SIZE) * conster.BLOCK_SIZE
        wy = offset_y + ((y - offset_y) // conster.BLOCK_SIZE) * conster.BLOCK_SIZE
        if autoGround:
            occupied = {
                item.world_z for item in cls.objs.values()
                if item.world_x == wx and item.world_y == wy
            }
            z = 0
            while z in occupied:
                z += 1
            return z
        return max(0, playerz - playerl)

    def is_visible(self, bx, by):
        sx, sy = self.world_x + bx, self.world_y + by
        return not (
            sx + self.width < 0 or sx > conster.WIDTH
            or sy + self.height < 0 or sy > conster.HEIGHT
        )

    def draw(self, display=None, bx=0, by=0, player=None):
        return DrawObj(
            GetRenderer(), self.world_x + bx, self.world_y + by,
            self.width, self.height, self.texture,
        )

    @classmethod
    def drawObjects(cls, display=None, bx=0, by=0):
        for item in sorted(cls.objs.values(), key=lambda value: (value.world_z, value.world_y)):
            if item.is_visible(bx, by):
                item.draw(None, bx, by)

    @classmethod
    def getObjs(cls):
        return cls.objs

    @classmethod
    def snapshot(cls, bx=0, by=0):
        return [
            (item.block_id, item.world_x + bx, item.world_y + by, item.world_z)
            for item in cls.objs.values() if item.is_visible(bx, by)
        ]
