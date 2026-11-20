import ctypes
import os


class EntityData(ctypes.Structure):
    # Must match struct EntityData in cmain.cpp exactly.
    _fields_ = [
        ("kind", ctypes.c_int),
        ("active", ctypes.c_int),
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


_DLL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "cppmain.dll",
)
lib = ctypes.CDLL(_DLL_PATH)


def loadFunction(name, args=None, result=None):
    fn = getattr(lib, name)
    if args is not None:
        fn.argtypes = args
    fn.restype = result
    return fn


Init = loadFunction("Init", result=ctypes.c_int)
Quit = loadFunction("Quit", result=ctypes.c_int)
RenderFrame = loadFunction("render", result=ctypes.c_int)
present = loadFunction("present")

GetRenderer = loadFunction("GetRENDERER", result=ctypes.c_void_p)
GetWindow = loadFunction("GetWINDOW", result=ctypes.c_void_p)

GetWindowSizeRaw = loadFunction(
    "GetWindowsize",
    args=[
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_void_p,
    ],
)

LoadTexture = loadFunction(
    "LoadTexture",
    args=[
        ctypes.c_void_p,
        ctypes.c_uint8,
        ctypes.c_uint8,
        ctypes.c_uint8,
        ctypes.c_uint8,
    ],
    result=ctypes.c_int,
)

LoadImageTexture = loadFunction(
    "LoadImageTexture",
    args=[ctypes.c_void_p, ctypes.c_char_p],
    result=ctypes.c_int,
)

# FPS is calculated and drawn inside C++.
# HUDSetData keeps its original signature; no FPS parameter is needed.
HUDSetData = loadFunction(
    "HUDSetData",
    args=[
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
    ],
)

HUDDraw = loadFunction("HUDDraw", args=[ctypes.c_int])
HUDGetSelectedSlot = loadFunction(
    "HUDGetSelectedSlot",
    result=ctypes.c_int,
)
HUDGetInventoryOpen = loadFunction(
    "HUDGetInventoryOpen",
    result=ctypes.c_int,
)

DrawObj = loadFunction(
    "drawobj",
    args=[
        ctypes.c_void_p,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_int,
    ],
    result=ctypes.c_bool,
)

pr = loadFunction(
    "pr",
    args=[
        ctypes.POINTER(ctypes.c_int32),
        ctypes.POINTER(ctypes.c_int32),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_float,
    ],
)

ck = loadFunction(
    "keycont",
    args=[
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_char),
        ctypes.c_int,
    ],
)

CreateEntities = loadFunction(
    "CreateEntities",
    args=[ctypes.c_int],
    result=ctypes.POINTER(EntityData),
)

try:
    RenderEntities = loadFunction(
        "RenderEntities",
        result=ctypes.c_int,
    )
except AttributeError:
    # Older DLL builds do not yet export this optional batch renderer.
    RenderEntities = None


def getWinSize():
    width = ctypes.c_int()
    height = ctypes.c_int()

    GetWindowSizeRaw(
        ctypes.byref(width),
        ctypes.byref(height),
        GetWindow(),
    )

    return width.value, height.value
