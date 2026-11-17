import os
from cppfuncs import *
from conster import *

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")






class Texturep:
    pass

class Texture:
    grass = water = stone = sand = plank = health = hungry = oak = leaves = -2
    npc1 = -2

    
    
    def init():
        renderer = GetRenderer()
        grass = LoadImageTexture(renderer, b"assets/grass.png")
        water = LoadImageTexture(renderer, b"assets/water.png")
        stone = LoadImageTexture(renderer, b"assets/stone.png")
        sand = LoadImageTexture(renderer, b"assets/sand.png")
        plank = LoadImageTexture(renderer, b"assets/plank.png")
        health = LoadImageTexture(renderer, b"assets/health.png")
        hungry = LoadImageTexture(renderer, b"assets/hungry.png")
        oak = LoadImageTexture(renderer, b"assets/oak.png")
        leaves = LoadImageTexture(renderer, b"assets/leaves.png")

        npc1 = LoadTexture(renderer,255,0,0,255)