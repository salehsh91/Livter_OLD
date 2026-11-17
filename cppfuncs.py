import ctypes
import threading

class EntityData(ctypes.Structure):
    _fields_ = [
        ("kind", ctypes.c_int),          # 0 = obj ، 1 = NPC
        ("active", ctypes.c_int),        # 0 = inactive ، 1 = active

        ("id", ctypes.c_int),

        ("world_x", ctypes.c_float),
        ("world_y", ctypes.c_float),
        ("world_z", ctypes.c_float),

        ("texture", ctypes.c_int),

        ("width", ctypes.c_float),
        ("height", ctypes.c_float),
        ("length", ctypes.c_float),

        ("bx", ctypes.c_float),
        ("by", ctypes.c_float),

        ("display_alpha", ctypes.c_float),
    ]

lib = ctypes.CDLL("./cppmain.dll")


def loadFunction(name, one=None, two=None):
    f = getattr(lib, name)

    if one is not None:
        f.argtypes = one

    f.restype = two
    return f


class draw:

    @classmethod
    def draw(cls, array):
        pass


# -------------------------
# SDL / Window
# -------------------------

Init = loadFunction(
    "Init",
    two=ctypes.c_int
)

Quit = loadFunction(
    "Quit",
    two=ctypes.c_int
)

Render = loadFunction(
    "render",
    two=ctypes.c_int
)

present = loadFunction(
    "present"
)

GetRenderer = loadFunction(
    "GetRENDERER",
    two=ctypes.c_void_p
)

GetWindow = loadFunction(
    "GetWINDOW",
    two=ctypes.c_void_p
)

GetWinSize = loadFunction(
    "GetWindowsize",
    one=[
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int)
    ]
)


# -------------------------
# Texture
# -------------------------

LoadTexture = loadFunction(
    "LoadTexture",
    one=[
        ctypes.c_void_p,
        ctypes.c_uint8,
        ctypes.c_uint8,
        ctypes.c_uint8,
        ctypes.c_uint8
    ],
    two=ctypes.c_int
)

LoadImageTexture = loadFunction(
    "LoadImageTexture",
    one=[
        ctypes.c_void_p,
        ctypes.c_char_p
    ],
    two=ctypes.c_int
)


# -------------------------
# Drawing
# -------------------------

DrawObj = loadFunction(
    "drawobj",
    one=[
        ctypes.c_void_p,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_int
    ],
    two=None
)

pr = loadFunction(
    "pr",
    one=[
        ctypes.POINTER(ctypes.c_int32),
        ctypes.POINTER(ctypes.c_int32),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_float
    ],
    two=None
)


# -------------------------
# Input
# -------------------------

ck = loadFunction(
    "keycont",
    one=[
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_char),
        ctypes.c_int
    ],
    two=ctypes.c_char
)

CreateEntities = loadFunction(
    "CreateEntities",
    one=[ctypes.c_int],
    two=ctypes.POINTER(EntityData)
)
# -------------------------
# Helpers
# -------------------------

def getWinSize():
    width = ctypes.c_int()
    height = ctypes.c_int()

    GetWinSize(
        ctypes.byref(width),
        ctypes.byref(height)
    )

    return width.value, height.value