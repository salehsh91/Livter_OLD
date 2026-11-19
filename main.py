import random
import ctypes

import conster
from cppfuncs import Init, Quit, getWinSize, CreateEntities, EntityData
from contoroler import Contoroler_Key
from npc import NPC
from texture import Texture
from world import World

MAX_ENTITIES = 20000

def main():
    result = Init()
    if result != 0:
        raise RuntimeError("SDL3 initialization failed")

    try:
        width, height = getWinSize()
        if width <= 0 or height <= 0:
            raise RuntimeError("Could not read SDL window dimensions")

        conster.WIDTH = width
        conster.HEIGHT = height

        Texture.init()

        entity_pointer = CreateEntities(MAX_ENTITIES)
        if not entity_pointer:
            raise MemoryError("C++ could not allocate the entity array")
        NPC.activate(
            entity_pointer,
            ctypes.POINTER(EntityData),
            MAX_ENTITIES,
        )

        seed = random.randint(0, 999999999)
        print("seed:", seed)

        controller = Contoroler_Key()
        world = World(seed)
        world.newPlayer(
            50,
            50,
            width / 2 - 25,
            height / 2 - 25,
            Texture.npc1,
            controller,
        )
        print("game started")

        running = True
        while running:
            running = world.update()
            if running:
                world.draw()

    finally:
        Quit()

if __name__ == "__main__":
    main()
