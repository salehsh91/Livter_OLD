
"""
blockitem.py  -  تعریف بلوک‌ها (داده‌محور و آماده‌ی انتقال به C++)

هر بلوک یک BlockItem است: هم مثل dict کار می‌کند (block["texture"]) و هم مثل
شیء (block.texture)، پس هم chunk.py و هم object.py بدون تغییر کار می‌کنند.
فیلد id یک عدد صحیح است تا بعداً مستقیم به uint16 در C++ تبدیل شود.
"""
import pygame as pyg
from conster import BLOCK_SIZE

# شناسه‌های عددی (در C++ همین مقادیر به enum تبدیل می‌شوند)
BLOCK_IDS = {
    "air": 0,
    "grass": 1,
    "stone": 2,
    "water": 3,
    "sand": 4,
    "plank": 5,
}
BLOCK_TYPES = {
    "air": "air",
    "grass": "ground",
    "stone": "solid",
    "water": "liquid",
    "sand": "ground",
    "plank": "item",
}
SOLID_BLOCKS = {"stone", "plank"}

# اگر Texture برای اسمی وجود نداشت، یک مربع رنگی ساخته می‌شود
FALLBACK_COLORS = {
    "grass": (60, 160, 60),
    "stone": (120, 120, 120),
    "water": (50, 90, 200),
    "sand": (220, 200, 120),
    "plank": (150, 100, 50),
}


class BlockItem(dict):
    """dict که با نقطه هم قابل دسترسی است."""
    __slots__ = ()

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    def to_c(self):
        """نمایش ساده برای C++: (id, solid_flag)"""
        return (self["id"], 1 if self["solid"] else 0)


class Block:
    _textures = {}      # name -> Surface
    _names_by_tex = {}  # id(Surface) -> name
    _items = {}         # name -> BlockItem (مشترک بین همه‌ی بلوک‌های هم‌نوع)

    @classmethod
    def _load_texture(cls, name):
        if name in cls._textures:
            return cls._textures[name]

        tex = None
        try:
            from texture import Texture
            tex = getattr(Texture, name, None)
        except Exception:
            tex = None

        if tex is None and name in FALLBACK_COLORS:
            tex = pyg.Surface((BLOCK_SIZE, BLOCK_SIZE))
            tex.fill(FALLBACK_COLORS[name])

        cls._textures[name] = tex
        if tex is not None:
            cls._names_by_tex[id(tex)] = name
        return tex

    @classmethod
    def _name_from_texture(cls, texture):
        key = id(texture)
        if key not in cls._names_by_tex:
            for name in BLOCK_IDS:
                if name != "air":
                    cls._load_texture(name)
        return cls._names_by_tex.get(key, "unknown")

    @classmethod
    def getblock_status(cls, texture=None, name=None):
        """
        getblock_status(texture)   <- روش chunk.py
        getblock_status(name="x")  <- روش object.py
        """
        if name is None:
            name = cls._name_from_texture(texture) if texture is not None else "air"

        if name in cls._items:
            return cls._items[name]

        if texture is None and name != "air":
            texture = cls._load_texture(name)

        item = BlockItem(
            id=BLOCK_IDS.get(name, -1),
            name=name,
            type=BLOCK_TYPES.get(name, "unknown"),
            texture=texture,
            solid=name in SOLID_BLOCKS,
        )
        cls._items[name] = item
        return item
