import conster

class Camera:
    def __init__(self, source, width=None, height=None):
        self.source = source
        self.width = conster.WIDTH if width is None else width
        self.height = conster.HEIGHT if height is None else height

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
            sx + w < -margin or sx > self.width + margin
            or sy + h < -margin or sy > self.height + margin
        )
