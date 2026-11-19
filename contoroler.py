import ctypes
import math
from cppfuncs import ck


class Contoroler_Key:
    def __init__(self, up="w", down="s", left="a", right="d",
                 drap="q", undrap="e", debug="t"):
        self.key_up = up
        self.key_down = down
        self.key_left = left
        self.key_right = right
        self.key_drap = drap
        self.key_undrap = undrap
        self.key_debug = debug
        self.grond = False

        # کلیدهای حرکتی و Q از نوع نگه‌داشتنی هستند.
        # SDL_Scancode: W=26, S=22, A=4, D=7, Q=20
        self.hold_scancodes = (ctypes.c_int * 5)(26, 22, 4, 7, 20)

        # E و T فقط در فریم شروع فشردن گزارش می‌شوند.
        # SDL_Scancode: E=8, T=23
        self.press_scancodes = (ctypes.c_int * 2)(8, 23)
        self.output = ctypes.create_string_buffer(256)

    def getAPI(self):
        self.output.value = b""
        ck(
            self.hold_scancodes, len(self.hold_scancodes),
            self.press_scancodes, len(self.press_scancodes),
            self.output, len(self.output),
        )

        result = self.output.value.decode("utf-8", errors="replace")
        held, pressed = set(), set()
        for section in result.split(";"):
            if section.startswith("H:"):
                held.update(filter(None, section[2:].split("+")))
            elif section.startswith("P:"):
                pressed.update(filter(None, section[2:].split("+")))

        x = int("D" in held) - int("A" in held)
        y = int("S" in held) - int("W" in held)
        moving = x != 0 or y != 0
        if moving:
            length = math.hypot(x, y)
            x, y = x / length, y / length

        direction = math.degrees(math.atan2(x, -y)) if moving else 0.0

        # Q تا وقتی نگه داشته شده، هر فریم فعال می‌ماند.
        # E و T فقط یک‌بار در لحظه فشردن فعال می‌شوند.
        action = 1 if "Q" in held else -1 if "E" in pressed else 0
        return {
            "x": x,
            "y": y,
            "dir": direction,
            "move": moving,
            "cameradir": direction,
            "drap": action,
            "debug": "T" in pressed,
            "Ground": self.grond,
        }
