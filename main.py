
import random
from cppfuncs import *
import ctypes
from npc import NPC
class EntityData(ctypes.Structure):
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

        ("type", ctypes.c_int),
        ("base_x", ctypes.c_float),
        ("base_y", ctypes.c_float),
        ("display_alpha", ctypes.c_float),
    ]

MAX_ENTITIES = 20000
EntityPointer = ctypes.POINTER(EntityData)
entities = CreateEntities(20000)
NPC.activate(entities,EntityPointer,MAX_ENTITIES)


from world import *

from texture import *
# from contoroler import *
# from hud import *
screen = None




running = True
# playerContoroler = Contoroler_JoyStick(None,200,HEIGHT-200)
playerContoroler = Contoroler_Key(screen)
seed = random.randint(0, 999999999)
print("seed:", seed)

world = World(seed)



player = world.newPlayer(
    50,
    50,
    WIDTH / 2-50/2,
    HEIGHT / 2-50/2,
    Texture.npc1,
    playerContoroler
)


# for _ in range( 100):

#     world.newNPC(
#         50,
#         50,
#         WIDTH / 2 + 200,
#         HEIGHT / 2,
#         COLORS["BLUE"],
#         Contoroler_Key(
#             pyg.K_i,
#             pyg.K_k,
#             pyg.K_j,
#             pyg.K_l,
#             pyg.K_u
#         )
#     )

# world.getHUD(HUD(screen, player.getStatus(world.blockManager)))
Init()
Texture.init()
print("game started")





running = 1
while running == 1:

    

    # world.update()

    # screen.fill((0, 0, 0))

    if Render:
        
        WIDTH,HEIGHT = getWinSize()
        
        running = world.draw()
    else:
        running = 0
        
        

Quit()

            