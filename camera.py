
"""
camera.py  -  دوربین. منبع حقیقت همان bx/by در BlocksWorld است؛
این کلاس فقط تبدیل مختصات و تست دیده‌شدن را در یک جا جمع می‌کند.
"""
from conster import WIDTH, HEIGHT


class Camera:
    def __init__(self, source, width=WIDTH, height=HEIGHT):
        self.source = source      # شیئی که bx و by دارد (BlocksWorld)
        self.width = width
        self.height = height

    @property
    def x(self):
        return self.source.bx

    @property
    def y(self):
        return self.source.by

    def world_to_screen(self, wx, wy):
        return wx + self.x, wy + self.y

    def is_visible(self, wx, wy, w, h, margin=0):
        sx, sy = self.world_to_screen(wx, wy)
        return not (
            sx + w < -margin or sx > self.width + margin or
            sy + h < -margin or sy > self.height + margin
        )
