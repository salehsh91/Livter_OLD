import os
from cppfuncs import GetRenderer, LoadTexture, LoadImageTexture


class Texture:
    # These IDs must stay aligned with BLOCK_IDS in blockitem.py.
    air = 0
    grass = 1
    stone = 2
    water = 3
    sand = 4
    plank = 5
    oak = 6
    leaves = 7
    health = 8
    hungry = 9
    npc1 = 10
    _initialized = False

    @classmethod
    def init(cls):
        if cls._initialized:
            return

        renderer = GetRenderer()
        if not renderer:
            raise RuntimeError("SDL renderer is not initialized")

        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_dir, "assets")

        # Preserve the exact IDs expected by C++ chunk rendering.
        definitions = [
            ("air", None, (0, 0, 0, 0)),
            ("grass", "grass.png", (60, 160, 60, 255)),
            ("stone", "stone.png", (120, 120, 120, 255)),
            ("water", "water.png", (50, 90, 200, 255)),
            ("sand", "sand.png", (220, 200, 120, 255)),
            ("plank", "plank.png", (150, 100, 50, 255)),
            ("oak", "oak.png", (105, 75, 35, 255)),
            ("leaves", "leaves.png", (45, 135, 45, 210)),
            ("health", "health.png", (220, 40, 40, 255)),
            ("hungry", "hungry.png", (220, 150, 30, 255)),
            ("npc1", None, (255, 0, 0, 255)),
        ]

        loaded_ids = []
        for name, filename, color in definitions:
            texture_id = -1
            if filename:
                path = os.path.join(assets_dir, filename)
                if os.path.isfile(path):
                    texture_id = LoadImageTexture(renderer, os.fsencode(path))
            if texture_id < 0:
                texture_id = LoadTexture(renderer, *color)
            loaded_ids.append(texture_id)
            setattr(cls, name, texture_id)

        expected = list(range(len(definitions)))
        if loaded_ids != expected:
            raise RuntimeError(
                "Texture IDs do not match block IDs: "
                f"expected {expected}, got {loaded_ids}. "
                "Check that no texture was loaded before Texture.init()."
            )

        cls._initialized = True
