import os
from cppfuncs import GetRenderer, LoadTexture, LoadImageTexture


class Texture:
    # These IDs stay aligned with the C++ block texture IDs.
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

        # PNGs must be loaded as real images. Do not silently replace a missing
        # or unreadable image with a solid-color texture: that caused the
        # previous 'single color instead of texture' failure to go unnoticed.
        image_files = [
            ("grass", "grass.png"),
            ("stone", "stone.png"),
            ("water", "water.png"),
            ("sand", "sand.png"),
            ("plank", "plank.png"),
            ("oak", "oak.png"),
            ("leaves", "leaves.png"),
            ("health", "health.png"),
            ("hungry", "hungry.png"),
        ]

        # ID 0: transparent air texture; ID 10: solid NPC placeholder.
        air_id = LoadTexture(renderer, 0, 0, 0, 0)
        if air_id != 0:
            raise RuntimeError(f"Expected air texture ID 0, got {air_id}")
        cls.air = air_id

        for expected_id, (name, filename) in enumerate(image_files, start=1):
            path = os.path.join(assets_dir, filename)
            if not os.path.isfile(path):
                raise FileNotFoundError(
                    f"Missing texture file: {path}. Put the original PNG in the assets folder."
                )

            texture_id = LoadImageTexture(renderer, os.fsencode(path))
            if texture_id != expected_id:
                raise RuntimeError(
                    f"Could not load {path} as texture ID {expected_id}; "
                    f"C++ returned {texture_id}. Check SDL3_image and the PNG file."
                )
            setattr(cls, name, texture_id)

        npc_id = LoadTexture(renderer, 255, 0, 0, 255)
        if npc_id != 10:
            raise RuntimeError(f"Expected NPC texture ID 10, got {npc_id}")
        cls.npc1 = npc_id
        cls._initialized = True
