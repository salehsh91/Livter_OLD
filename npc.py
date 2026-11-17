import ctypes
import math
import time

from conster import *

from blockitem import *

from object import obj

# from blockitem import Item

from structures import *






class NPC:

    # Pointer to the C++-owned shared entity array.
    npcs = None

    # Python-side gameplay instances. Rendering data is NOT stored here.
    instances = []
    npc_count = 0
    MaxEn = 0
    @classmethod
    def activate(cls, pointer, EntityPointer, MaxEn):
        """Connect NPC rendering data to the C++-owned shared array."""
        cls.npcs = ctypes.cast(pointer, EntityPointer)
        cls.instances = []
        cls.npc_count = 0
        cls.MaxEn = MaxEn


    def __init__(self, w, h, x, y, display, world,

                 texture = Texture.npc1, center=False, move=False):


        if NPC.npcs is None:
            raise RuntimeError("NPC.activate(pointer) must be called first")

        self.slot = self._find_free_slot()
        if self.slot < 0:
            raise RuntimeError("MAX_ENTITIES reached")

        self.id = self.slot + 1
        NPC.npc_count += 1
        
        

        self.texture = texture

        self.width = w

        self.height = h

        self.length = 2

        self.display = display


        self.realx = x

        self.realy = y


        self.space = 1


        self.world = world

        self.health = 100

        self.hungry = 100


        self.world_x = x

        self.world_y = y

        self.world_z = 1


        self.last_dx = 0

        self.last_dy = 0


        self.move = move


        # True = Player

        # False = NPC

        self.center = center


        # محدوده دید NPC

        # دید Player از این مقدار استفاده نمی‌کند

        self.vision_range = 10


        self.dir_angle = 0

        self.camdir_angle = 0


        self.invertory = None


        self.rightHand = None

        self.Auto_Ground = True


        self.bx = 0

        self.by = 0


        self.last_drap_time = 0

        self.drap_delay = 500  # میلی‌ثانیه


        self._update_render_data()
        NPC.instances.append(self)


    @classmethod
    def _find_free_slot(cls):
        for slot in range(cls.MaxEn):
            if cls.npcs[slot].active == 0:
                return slot
        return -1

    def _update_render_data(self):
        data = NPC.npcs[self.slot]
        data.kind = 1
        data.active = 1
        data.id = self.id
        data.world_x = self.world_x
        data.world_y = self.world_y
        data.world_z = self.world_z
        data.texture = int(self.texture)
        data.width = self.width
        data.height = self.height
        data.length = self.length
        data.bx = self.bx
        data.by = self.by

    @classmethod
    def get_cpp_buffer(cls):
        return cls.npcs

    @classmethod
    def get_cpp_pointer(cls):
        return cls.npcs

    @classmethod
    def get_cpp_count(cls):
        return cls.npc_count

    @staticmethod
    def _rects_collide(ax, ay, aw, ah, bx, by, bw, bh):
        return (
            ax < bx + bw
            and ax + aw > bx
            and ay < by + bh
            and ay + ah > by
        )


    def addinvertory(self, invertory):

        self.invertory = invertory


        # self.invertory.add(

        #     Item.getitem_status(name="plank"),

        #     999

        # )


        # self.invertory.add(

        #     Item.getitem_status(name="stone"),

        #     999

        # )


    def update(self, bManager):

        blocks = bManager.getblock(

            self.world_x,

            self.world_y,

            self.width,

            self.height

        )


        self.bx = bManager.bx

        self.by = bManager.by


        for key, block_type in blocks.items():

            if block_type == "water" and self.world_z <= 1:

                self.health -= Block.getblock_status(

                    type=block_type

                ).damage

                break

        self._update_render_data()


    def getAPI(self, API):

        self.Auto_Ground = API["Ground"]


        if API["move"]:

            rad = math.radians(API["dir"])

            dx = math.sin(rad)

            dy = -math.cos(rad)

            self.dir_angle = API["dir"]

        else:

            dx = 0

            dy = 0


        x = dx * NPC_SPEED

        y = dy * NPC_SPEED


        old_x = self.world_x

        old_y = self.world_y


        self.world_x += x

        self.world_y += y


        self.last_dx = x

        self.last_dy = y


        self.camdir_angle = API["cameradir"]

        now = (time.monotonic_ns() // 1_000_000)


        if True:

            base_x = self.world.base_x

            base_y = self.world.base_y


            npc_rect = Rect(

                self.world_x + self.bx,

                self.world_y + self.by,

                self.width,

                self.height

            )


            hit_object = False

            highest_z = 1


            for o in obj.getObj3x3x3(

                self.world_x + self.width / 2,

                self.world_y + self.height / 2,

                self.world_z,

                base_x,

                base_y

            ):

                object_rect = Rect(

                    o[0] + self.bx,

                    o[1] + self.by,

                    o[2] - o[0],

                    o[3] - o[1]

                )


                if npc_rect.colliderect(object_rect):

                    hit_object = True

                    object_top = o[4] + o[5]


                    if object_top > highest_z:

                        highest_z = object_top


            if hit_object:

                if self.world_z + self.space >= highest_z:

                    self.world_z = highest_z

                else:

                    self.world_x = old_x

                    self.world_y = old_y

                    self.last_dx = 0

                    self.last_dy = 0

            else:

                self.world_z = max(1, self.world_z - 1)


        if now - self.last_drap_time >= self.drap_delay:

            self.last_drap_time = now

            self.drap(API["drap"])


            if API["debug"]:

                Structers.Tree(self.world,self.world_x,self.world_y)

        self._update_render_data()


    def drap(self, drap):

        if self.invertory is None or drap == 0:

            return


        key = None


        for k, data in self.invertory.slots.items():

            if len(data) >= 3 and data[2] == True:

                key = k

                break


        if key is None:

            return


        slot = self.invertory.slots[key]


        self.rightHand = slot


        if len(slot) < 3:

            return


        item = slot[0]

        count = slot[1]

        active = slot[2]


        if count <= 0 or active == False:

            return


        x = WIDTH / 2

        y = HEIGHT / 2


        rad = math.radians(self.camdir_angle)


        end_x = x + math.sin(rad) * camdirline

        end_y = y - math.cos(rad) * camdirline


        w = item.block.w

        h = item.block.h


        base_x = self.world.base_x

        base_y = self.world.base_y


        world_x = end_x - self.world.bx

        world_y = end_y - self.world.by


        z1 = obj.zblock(

            world_x,

            world_y,

            self.world_z,

            self.length,

            base_x,

            base_y,

            self.Auto_Ground

        )


        world_z = z1


        if drap >= 1:


            new_obj = obj(

                world_x,

                world_y,

                world_z,

                w,

                h,

                name=item.name,

                offset_x=base_x,

                offset_y=base_y

            )


            if new_obj.create():


                self.invertory.slots[key] = (

                    item,

                    count - 1,

                    active

                )


        elif drap <= -1:


            result = obj.remove(

                world_x,

                world_y,

                world_z,

                w,

                h,

                name=item.name,

                offset_x=base_x,

                offset_y=base_y,

                autogrand=self.Auto_Ground

            )


            if result[0]:

                a = False


                i = Item.getitem_status(

                    name=result[1]

                )


                if slot[0] == i:

                    a = True


                self.invertory.add(

                    i,

                    1,

                    a

                )


    # =========================================================

    # دید NPC از بلوک‌ها

    # =========================================================


    def getVisibleBlocks(self, bManager):

        blocks = {}


        # Player از سیستم دید NPC استفاده نمی‌کند

        if self.center:

            return blocks


        for nx in range(

            -self.vision_range,

            self.vision_range + 1

        ):

            for ny in range(

                -self.vision_range,

                self.vision_range + 1

            ):


                x = self.world_x + nx * BLOCK_SIZE

                y = self.world_y + ny * BLOCK_SIZE


                blocks[(nx, ny)] = bManager.getblock(

                    x,

                    y,

                    BLOCK_SIZE,

                    BLOCK_SIZE

                )


        return blocks


    # =========================================================

    # دید NPC از Object ها

    # =========================================================


    def getVisibleObjects(self):

        visible_objects = []


        if self.center:

            return visible_objects


        vision_size = self.vision_range * BLOCK_SIZE


        min_x = self.world_x - vision_size

        max_x = self.world_x + vision_size


        min_y = self.world_y - vision_size

        max_y = self.world_y + vision_size


        for object_ in obj.objs.values():


            if (

                min_x <= object_.world_x <= max_x

                and

                min_y <= object_.world_y <= max_y

            ):

                visible_objects.append(object_)


        return visible_objects


    # =========================================================

    # دید NPC از NPC های دیگر

    # =========================================================


    def getVisibleNPCs(self):

        visible_npcs = []


        if self.center:

            return visible_npcs


        vision_size = self.vision_range * BLOCK_SIZE


        min_x = self.world_x - vision_size

        max_x = self.world_x + vision_size


        min_y = self.world_y - vision_size

        max_y = self.world_y + vision_size


        for npc in NPC.instances:


            if npc is self:

                continue


            if (

                min_x <= npc.world_x <= max_x

                and

                min_y <= npc.world_y <= max_y

            ):

                visible_npcs.append(npc)


        return visible_npcs


    def getStatus(self, bManager):

        blocks = {}

        id = 0


        for nx in range(-10, 10):

            for ny in range(-10, 10):


                x = nx * BLOCK_SIZE + self.world_x

                y = ny * BLOCK_SIZE + self.world_y


                id += 1


                blocks[id] = bManager.getblock(

                    x,

                    y,

                    BLOCK_SIZE,

                    BLOCK_SIZE

                )


        return {

            "blocks": blocks,

            "invertory": self.invertory.slots,

            "numslots": self.invertory.slotnum,

            "health": self.health,

            "hungry": self.hungry,

            "x": self.world_x,

            "y": self.world_y,

            "cameradir": self.camdir_angle

        }
