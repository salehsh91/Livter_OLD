
import pygame as pyg
from conster import *
from blockitem import Block


class obj:
    objs = {}
    _next_id = 1

    def __init__(self, x, y, z=0, objwidth=BLOCK_SIZE, objheight=BLOCK_SIZE,
                 name="plank", offset_x=0, offset_y=0):
        self.world_x = offset_x + ((x - offset_x) // BLOCK_SIZE) * BLOCK_SIZE
        self.world_y = offset_y + ((y - offset_y) // BLOCK_SIZE) * BLOCK_SIZE
        self.world_z = z
        self.width = objwidth
        self.height = objheight
        self.base_x = offset_x
        self.base_y = offset_y

        block = Block.getblock_status(name=name)
        self.block_id = block.id
        self.texture = block.texture
        self.type = block.type
        self.name = block.name

    def create(self):
        for o in self.objs.values():
            if (self.world_x == o.world_x and self.world_y == o.world_y
                    and self.world_z == o.world_z):
                return False
        self.id = obj._next_id          # با حذف شدن، id تکراری نمی‌شود
        obj._next_id += 1
        self.objs[self.id] = self
        return True

    @classmethod
    def remove(cls, x, y, objwidth=BLOCK_SIZE, objheight=BLOCK_SIZE,
               name="plank", offset_x=0, offset_y=0):
        wx = offset_x + ((x - offset_x) // BLOCK_SIZE) * BLOCK_SIZE
        wy = offset_y + ((y - offset_y) // BLOCK_SIZE) * BLOCK_SIZE
        for oid, o in cls.objs.items():
            if wx == o.world_x and wy == o.world_y:
                name_found = o.name
                del cls.objs[oid]
                return (True, name_found)
        return (False, None)

    @classmethod
    def zblock(cls, x, y, playerz, playerl, offset_x, offset_y, autoGround):
        wx = offset_x + ((x - offset_x) // BLOCK_SIZE) * BLOCK_SIZE
        wy = offset_y + ((y - offset_y) // BLOCK_SIZE) * BLOCK_SIZE

        if autoGround:
            z = 0
            while True:
                occupied = any(
                    o.world_x == wx and o.world_y == wy and o.world_z == z
                    for o in cls.objs.values()
                )
                if not occupied:
                    return z
                z += 1

        return max(0, playerz - playerl)

    def is_visible(self, bx, by):
        sx = self.world_x + bx
        sy = self.world_y + by
        return not (sx + self.width < 0 or sx > WIDTH or
                    sy + self.height < 0 or sy > HEIGHT)

    def draw(self, display, bx, by):
        display.blit(self.texture, (self.world_x + bx, self.world_y + by))

    @classmethod
    def drawObjects(cls, display, bx, by):
        # ترتیب رسم بر اساس z تا بلوک بالایی روی پایینی بیفتد
        for o in sorted(cls.objs.values(), key=lambda a: a.world_z):
            if o.is_visible(bx, by):
                o.draw(display, bx, by)

    @classmethod
    def getObjs(cls):
        return cls.objs

    @classmethod
    def snapshot(cls, bx, by):
        """فهرست ساده‌ی اشیای قابل‌دیدن برای C++: (block_id, screen_x, screen_y, z)"""
        return [
            (o.block_id, o.world_x + bx, o.world_y + by, o.world_z)
            for o in cls.objs.values() if o.is_visible(bx, by)
        ]
