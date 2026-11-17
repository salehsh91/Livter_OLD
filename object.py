import ctypes

from conster import *
# from blockitem import Block


class ObjData(ctypes.Structure):
    _fields_ = [
        ("world_x", ctypes.c_float),
        ("world_y", ctypes.c_float),
        ("world_z", ctypes.c_int),
        ("texture", ctypes.c_int),
        ("type", ctypes.c_int),
        ("width", ctypes.c_float),
        ("height", ctypes.c_float),
        ("length", ctypes.c_float),
        ("base_x", ctypes.c_float),
        ("base_y", ctypes.c_float),
        ("display_alpha", ctypes.c_float),
    ]


MAX_OBJECTS = 10000
ObjArray = ObjData * MAX_OBJECTS


class obj:
    # Python lookup/storage for gameplay.
    objs = {}

    # One contiguous Python/C++ compatible render-data array.
    object_array = ObjArray()
    object_count = 0

    def __init__(
        self,
        x,
        y,
        z,
        objwidth=BLOCK_SIZE,
        objheight=BLOCK_SIZE,
        name="plank",
        offset_x=0,
        offset_y=0
    ):
        if obj.object_count >= MAX_OBJECTS:
            raise RuntimeError("MAX_OBJECTS reached")

        self.slot = obj.object_count
        obj.object_count += 1

        self.world_x = offset_x + ((x - offset_x) // BLOCK_SIZE) * BLOCK_SIZE
        self.world_y = offset_y + ((y - offset_y) // BLOCK_SIZE) * BLOCK_SIZE
        self.world_z = z

        self.width = objwidth
        self.height = objheight
        self.length = 1

        self.base_x = offset_x
        self.base_y = offset_y

        block = Block.getblock_status(name=name)
        self.texture = block.texture
        self.type = block.type
        self.name = block.name

        self.display_alpha = 255.0

        # Data required by the C++ renderer.
        self._update_render_data()

    def _update_render_data(self):
        data = obj.object_array[self.slot]

        data.world_x = self.world_x
        data.world_y = self.world_y
        data.world_z = self.world_z

        # texture must be a numeric texture ID understood by C++.
        data.texture = int(self.texture)

        data.type = int(self.type)
        data.width = self.width
        data.height = self.height
        data.length = self.length

        data.base_x = self.base_x
        data.base_y = self.base_y
        data.display_alpha = self.display_alpha

    @classmethod
    def get_cpp_buffer(cls):
        return cls.object_array

    @classmethod
    def get_cpp_pointer(cls):
        return ctypes.cast(
            cls.object_array,
            ctypes.POINTER(ObjData)
        )

    @classmethod
    def get_cpp_count(cls):
        return cls.object_count

    @classmethod
    def _clear_render_data(cls, slot):
        data = cls.object_array[slot]

        data.world_x = 0
        data.world_y = 0
        data.world_z = -1
        data.texture = 0
        data.type = 0
        data.width = 0
        data.height = 0
        data.length = 0
        data.base_x = 0
        data.base_y = 0
        data.display_alpha = 0

    def create(self):
        for object_ in self.objs.values():
            if (
                self.world_x == object_.world_x
                and self.world_y == object_.world_y
                and self.world_z == object_.world_z
            ):
                return False

        self.id = (self.world_x, self.world_y, self.world_z)
        self.objs[self.id] = self

        self._update_render_data()

        return True

    @classmethod
    def remove(
        cls,
        x,
        y,
        z,
        objwidth=BLOCK_SIZE,
        objheight=BLOCK_SIZE,
        name="plank",
        offset_x=0,
        offset_y=0,
        autogrand=False
    ):
        A_world_x = (
            offset_x
            + ((x - offset_x) // BLOCK_SIZE) * BLOCK_SIZE
        )

        A_world_y = (
            offset_y
            + ((y - offset_y) // BLOCK_SIZE) * BLOCK_SIZE
        )

        if autogrand:
            # پیدا کردن بالاترین بلاک در همین ستون x,y
            target_id = None
            target_z = None

            for id_, object_ in cls.objs.items():
                if (
                    object_.world_x == A_world_x
                    and object_.world_y == A_world_y
                ):
                    if (
                        target_z is None
                        or object_.world_z > target_z
                    ):
                        target_z = object_.world_z
                        target_id = id_

            if target_id is None:
                return (False, None)

            removed = cls.objs[target_id]
            name_removed = removed.name

            del cls.objs[target_id]
            cls._clear_render_data(removed.slot)

            return (True, name_removed)

        # حالت عادی: حذف بلاک دقیقاً در z مشخص‌شده
        for id_, object_ in list(cls.objs.items()):
            if (
                A_world_x == object_.world_x
                and A_world_y == object_.world_y
                and object_.world_z == z
            ):
                removed = object_
                name_removed = removed.name

                del cls.objs[id_]
                cls._clear_render_data(removed.slot)

                return (True, name_removed)

        return (False, None)

    @classmethod
    def zblock(
        cls,
        x,
        y,
        playerz,
        playerl,
        offset_x,
        offset_y,
        autoGround
    ):
        world_x = (
            offset_x
            + ((x - offset_x) // BLOCK_SIZE) * BLOCK_SIZE
        )

        world_y = (
            offset_y
            + ((y - offset_y) // BLOCK_SIZE) * BLOCK_SIZE
        )

        if autoGround:
            z = 1

            while True:
                occupied = False

                for object_ in cls.objs.values():
                    if (
                        object_.world_x == world_x
                        and object_.world_y == world_y
                        and object_.world_z == z
                    ):
                        occupied = True
                        break

                if not occupied:
                    return z

                z += 1

        return max(1, playerz - 1)

    @classmethod
    def getObj(
        cls,
        world_x,
        world_y,
        world_z,
        offset_x=0,
        offset_y=0
    ):
        x = (
            offset_x
            + ((world_x - offset_x) // BLOCK_SIZE) * BLOCK_SIZE
        )

        y = (
            offset_y
            + ((world_y - offset_y) // BLOCK_SIZE) * BLOCK_SIZE
        )

        return cls.objs.get((x, y, world_z))

    @classmethod
    def getObj3x3x3(
        cls,
        world_x,
        world_y,
        world_z,
        offset_x=0,
        offset_y=0
    ):
        objects = []

        for xX in range(-1, 2):
            x = world_x + (xX * BLOCK_SIZE)

            for xY in range(-1, 2):
                y = world_y + (xY * BLOCK_SIZE)

                for xZ in range(-1, 2):
                    z = world_z + xZ

                    object_ = cls.getObj(
                        x,
                        y,
                        z,
                        offset_x,
                        offset_y
                    )

                    if object_ is not None:
                        startx = object_.world_x
                        starty = object_.world_y

                        lastx = (
                            object_.world_x
                            + object_.width
                        )

                        lasty = (
                            object_.world_y
                            + object_.height
                        )

                        objects.append([
                            startx,
                            starty,
                            lastx,
                            lasty,
                            object_.world_z,
                            object_.length
                        ])

        return objects

    @classmethod
    def getObjs(cls, world, player):
        objects = {}

        wb = int(WIDTH // BLOCK_SIZE) + 2
        hb = int(HEIGHT // BLOCK_SIZE) + 1

        base_x = world.base_x
        base_y = world.base_y

        for ix in range(0, wb):
            x = (
                ix * BLOCK_SIZE
                + int(player.world_x - WIDTH / 2)
            )

            x = (
                base_x
                + ((x - base_x) // BLOCK_SIZE) * BLOCK_SIZE
            )

            for iy in range(0, hb):
                y = (
                    iy * BLOCK_SIZE
                    + int(player.world_y - HEIGHT / 2)
                )

                y = (
                    base_y
                    + ((y - base_y) // BLOCK_SIZE) * BLOCK_SIZE
                )

                for z in range(25):
                    object_ = cls.objs.get((x, y, z))

                    if object_ is not None:
                        id_ = len(objects) + 1
                        objects[id_] = object_

        return objects
