"""Data definitions for world blocks. Texture values are SDL texture IDs."""
from texture import Texture

BLOCK_IDS = {
    "air": 0,
    "grass": 1,
    "stone": 2,
    "water": 3,
    "sand": 4,
    "plank": 5,
    "oak": 6,
    "leaves": 7,
}
BLOCK_TYPES = {
    "air": "air",
    "grass": "ground",
    "stone": "solid",
    "water": "liquid",
    "sand": "ground",
    "plank": "item",
    "oak": "item",
    "leaves": "foliage",
}
SOLID_BLOCKS = {"stone", "plank", "oak"}

class BlockItem(dict):
    __slots__ = ()

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key, value):
        self[key] = value

    def to_c(self):
        return self["id"], int(self["solid"])

class Block:
    _items = {}

    @classmethod
    def getblock_status(cls, texture=None, name=None):
        if name is None:
            if isinstance(texture, str):
                name = texture
            elif isinstance(texture, int):
                name = next(
                    (n for n, block_id in BLOCK_IDS.items()
                     if block_id == texture),
                    "unknown",
                )
            else:
                name = "air"

        if name in cls._items:
            return cls._items[name]

        block_id = BLOCK_IDS.get(name, 0)
        item = BlockItem(
            id=block_id,
            name=name,
            type=BLOCK_TYPES.get(name, "unknown"),
            texture=block_id,
            solid=name in SOLID_BLOCKS,
        )
        cls._items[name] = item
        return item
