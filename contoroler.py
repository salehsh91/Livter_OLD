
from conster import *
from Button import *
from cppfuncs import ck
import math
import ctypes

class Contoroler_Key:
    def __init__(
        self,
        up="w",
        down="s",
        left="a",
        right="d",
        drap="q",
        undrap="e",
        debug="t"
    ):
        self.key_up = up
        self.key_down = down
        self.key_left = left
        self.key_right = right
        self.key_drap = drap
        self.key_undrap = undrap
        self.key_debug = debug

        self.grond = False

        # SDL_Scancode values: W=26, S=22, A=4, D=7
        self.hold_scancodes = (ctypes.c_int * 4)(26, 22, 4, 7)

        # SDL_Keycode values for Q, E, T
        self.press_keycodes = (ctypes.c_int * 3)(ord("q"), ord("e"), ord("t"))

        self.output = ctypes.create_string_buffer(256)

    def getAPI(self):
        ck(
            self.hold_scancodes,
            len(self.hold_scancodes),
            self.press_keycodes,
            len(self.press_keycodes),
            self.output,
            len(self.output)
        )

        result = self.output.value.decode("utf-8", errors="replace")

        held = set()
        pressed = set()

        

        for section in result.split(";"):
            if section.startswith("H:"):
                held.update(section[2:].split("+"))
            elif section.startswith("P:"):
                pressed.update(section[2:].split("+"))

        

        x = int("D" in held) - int("A" in held)
        y = int("S" in held) - int("W" in held)

        move = x != 0 or y != 0

        direction = (
            math.degrees(math.atan2(x, -y))
            if move else 0
        )

        drap = (
            1 if "Q" in pressed
            else -1 if "E" in pressed
            else 0
        )

        return {
            "dir": direction,
            "move": move,
            "cameradir": direction,
            "drap": drap,
            "debug": "T" in pressed,
            "Ground": self.grond
        }
