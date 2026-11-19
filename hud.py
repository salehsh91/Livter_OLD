
"""
hud.py  -  HUD جدا از pygame.

ایده: HUD فقط «فهرست دستورهای رسم» می‌سازد (داده‌ی خالص، با layout ثابت).
  - بک‌اند pygame (همین فایل) آن فهرست را می‌کشد.
  - بک‌اند C++/SDL3 همان آرایه را از طریق ctypes می‌گیرد (hud_abi.h).
پس HUD وقتی رندر عوض شود، دست نمی‌خورد.
"""
import ctypes
import pygame as pyg

# --- انواع دستور / آیکون‌ها (باید با hud_abi.h یکی باشد) ---
CMD_ICON = 1

ICON_HEALTH = 1
ICON_FILES = {ICON_HEALTH: "assets/health.png"}


class HUDCommand(ctypes.Structure):
    """layout ثابت، ۲۸ بایت. معادل struct HUDCommand در C++."""
    _fields_ = [
        ("kind", ctypes.c_int32),
        ("icon", ctypes.c_int32),
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("w", ctypes.c_float),
        ("h", ctypes.c_float),
        ("value", ctypes.c_float),
    ]


def build_commands(status, icon_size=10):
    """status = NPC.getStatus() → فهرست HUDCommand (بدون هیچ وابستگی به pygame)"""
    hearts = max(0, int(status["health"]) // 10)
    commands = []
    x = 10 + icon_size
    for i in range(hearts):
        y = i * 12 + icon_size
        commands.append(HUDCommand(CMD_ICON, ICON_HEALTH, x, y,
                                   icon_size, icon_size, 1.0))
    return commands


def to_c_array(commands):
    """(آرایه‌ی ctypes, تعداد) برای پاس دادن به تابع C++"""
    arr = (HUDCommand * max(1, len(commands)))(*commands)
    return arr, len(commands)


class PygameHUDRenderer:
    def __init__(self, display):
        self.display = display
        self._icons = {}

    def _icon(self, icon_id, w, h):
        key = (icon_id, int(w), int(h))
        if key not in self._icons:
            img = pyg.image.load(ICON_FILES[icon_id]).convert_alpha()
            self._icons[key] = pyg.transform.scale(img, (int(w), int(h)))
        return self._icons[key]

    def draw(self, commands):
        for c in commands:
            if c.kind == CMD_ICON:
                self.display.blit(self._icon(c.icon, c.w, c.h),
                                  (int(c.x), int(c.y)))


class HealthBar:
    """همان رابط قبلی (display, API / update / draw) تا main.py عوض نشود."""

    def __init__(self, display, API):
        self.objsize = 10
        self.renderer = PygameHUDRenderer(display)
        self.commands = build_commands(API, self.objsize)

    def update(self, API):
        self.commands = build_commands(API, self.objsize)

    def draw(self):
        self.renderer.draw(self.commands)

    def c_commands(self):
        return to_c_array(self.commands)

"""
hud.py  -  HUD جدا از pygame.

ایده: HUD فقط «فهرست دستورهای رسم» می‌سازد (داده‌ی خالص، با layout ثابت).
  - بک‌اند pygame (همین فایل) آن فهرست را می‌کشد.
  - بک‌اند C++/SDL3 همان آرایه را از طریق ctypes می‌گیرد (hud_abi.h).
پس HUD وقتی رندر عوض شود، دست نمی‌خورد.
"""
import ctypes
import pygame as pyg

# --- انواع دستور / آیکون‌ها (باید با hud_abi.h یکی باشد) ---
CMD_ICON = 1

ICON_HEALTH = 1
ICON_FILES = {ICON_HEALTH: "assets/health.png"}


class HUDCommand(ctypes.Structure):
    """layout ثابت، ۲۸ بایت. معادل struct HUDCommand در C++."""
    _fields_ = [
        ("kind", ctypes.c_int32),
        ("icon", ctypes.c_int32),
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("w", ctypes.c_float),
        ("h", ctypes.c_float),
        ("value", ctypes.c_float),
    ]


def build_commands(status, icon_size=10):
    """status = NPC.getStatus() → فهرست HUDCommand (بدون هیچ وابستگی به pygame)"""
    hearts = max(0, int(status["health"]) // 10)
    commands = []
    x = 10 + icon_size
    for i in range(hearts):
        y = i * 12 + icon_size
        commands.append(HUDCommand(CMD_ICON, ICON_HEALTH, x, y,
                                   icon_size, icon_size, 1.0))
    return commands


def to_c_array(commands):
    """(آرایه‌ی ctypes, تعداد) برای پاس دادن به تابع C++"""
    arr = (HUDCommand * max(1, len(commands)))(*commands)
    return arr, len(commands)


class PygameHUDRenderer:
    def __init__(self, display):
        self.display = display
        self._icons = {}

    def _icon(self, icon_id, w, h):
        key = (icon_id, int(w), int(h))
        if key not in self._icons:
            img = pyg.image.load(ICON_FILES[icon_id]).convert_alpha()
            self._icons[key] = pyg.transform.scale(img, (int(w), int(h)))
        return self._icons[key]

    def draw(self, commands):
        for c in commands:
            if c.kind == CMD_ICON:
                self.display.blit(self._icon(c.icon, c.w, c.h),
                                  (int(c.x), int(c.y)))


class HealthBar:
    """همان رابط قبلی (display, API / update / draw) تا main.py عوض نشود."""

    def __init__(self, display, API):
        self.objsize = 10
        self.renderer = PygameHUDRenderer(display)
        self.commands = build_commands(API, self.objsize)

    def update(self, API):
        self.commands = build_commands(API, self.objsize)

    def draw(self):
        self.renderer.draw(self.commands)

    def c_commands(self):
        return to_c_array(self.commands)
