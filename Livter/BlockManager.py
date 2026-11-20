import ctypes
import time

import conster
from mynoise import OpenSimplex
from worldchunk import Chunk
from cppfuncs import pr

class BlocksWorld:
    CHUNK_SIZE = 16

    def __init__(self, seed):
        self.seed = int(seed)
        self.w = conster.W_WORLD
        self.h = conster.H_WORLD
        self.num_chunks_x = (self.w + self.CHUNK_SIZE - 1) // self.CHUNK_SIZE
        self.num_chunks_y = (self.h + self.CHUNK_SIZE - 1) // self.CHUNK_SIZE
        self.bw = conster.BLOCK_SIZE
        self.bh = conster.BLOCK_SIZE
        self.bx = 0.0
        self.by = 0.0

        self.real_world_width = self.num_chunks_x * self.CHUNK_SIZE * self.bw
        self.real_world_height = self.num_chunks_y * self.CHUNK_SIZE * self.bh
        self.base_x = conster.WIDTH / 2 - self.real_world_width / 2
        self.base_y = conster.HEIGHT / 2 - self.real_world_height / 2

        self.margin_chunks = 2
        self.Chunks = {}
        self.RealChunks = {}
        self.elevation_noise = OpenSimplex(seed=self.seed)
        self.river_noise = OpenSimplex(seed=self.seed + 2000)
        self.last_chunk_load_time = 0.0
        self.background_loader_index = 0
        self._render_blocks = None
        self._render_coords = None

    def get_noise_val(self, x, y, gen, scale):
        return (gen.noise2(x / scale, y / scale) + 1.0) / 2.0

    def determine_block_type(self, x, y):
        elev = self.get_noise_val(x, y, self.elevation_noise, 150.0)
        river = abs(self.river_noise.noise2(x / 80.0, y / 80.0))
        if river < 0.08 or elev < 0.35:
            return "water", 0
        if elev < 0.40:
            return "sand", 0
        if elev > 0.65:
            return "stone", 0
        return "grass", 0

    def _chunk_ranges(self, margin=None):
        cw = self.CHUNK_SIZE * self.bw
        ch = self.CHUNK_SIZE * self.bh
        margin = self.margin_chunks if margin is None else max(0, int(margin))
        sx = int((-self.base_x - self.bx) // cw) - margin
        ex = int((conster.WIDTH - self.base_x - self.bx) // cw) + margin + 1
        sy = int((-self.base_y - self.by) // ch) - margin
        ey = int((conster.HEIGHT - self.base_y - self.by) // ch) + margin + 1
        return sx, ex, sy, ey

    def get_real_visible_chunks(self):
        sx, ex, sy, ey = self._chunk_ranges()
        return [
            (cx, cy)
            for cx in range(sx, ex)
            for cy in range(sy, ey)
            if 0 <= cx < self.num_chunks_x and 0 <= cy < self.num_chunks_y
        ]

    def get_visible_chunks(self, margin=None):
        """Return chunks intersecting the camera area plus a preload margin."""
        sx, ex, sy, ey = self._chunk_ranges(margin)
        return [
            (cx, cy)
            for cx in range(sx, ex)
            for cy in range(sy, ey)
        ]

    def load_chunk(self, key, blocks1=None, fake=False):
        if key in self.Chunks and self.Chunks[key].is_loaded:
            return self.Chunks[key]
        cx, cy = key
        chunk = Chunk(cx, cy, self.CHUNK_SIZE, self.bw, self.base_x, self.base_y)
        if fake:
            chunk.set_blocks(blocks1 or {})
        else:
            chunk.generate(self.determine_block_type)
        self.Chunks[key] = chunk
        return chunk

    def create(self):
        # Load every real chunk. The configured world is small enough for this
        # initial synchronous pass and it prevents visible holes at startup.
        for cx in range(self.num_chunks_x):
            for cy in range(self.num_chunks_y):
                self.load_chunk((cx, cy))
        self.RealChunks = {
            key: chunk for key, chunk in self.Chunks.items()
        }
        for direction in (
            "up", "down", "left", "right",
            "up_left", "up_right", "down_left", "down_right",
        ):
            self.faketoreal(direction)

    def getAlgoritm(self, direction, bx, by):
        s = self.CHUNK_SIZE
        if direction in ("up", "down"):
            return bx, s - by - 1
        if direction in ("left", "right"):
            return s - bx - 1, by
        if direction in ("up_left", "up_right", "down_left", "down_right"):
            return s - bx - 1, s - by - 1
        return bx, by

    def faketoreal(self, direction):
        for (cx, cy), source in list(self.RealChunks.items()):
            if direction == "up":
                target = (cx, -cy - 1)
            elif direction == "down":
                target = (cx, self.num_chunks_y * 2 - cy - 1)
            elif direction == "left":
                target = (-cx - 1, cy)
            elif direction == "right":
                target = (self.num_chunks_x * 2 - cx - 1, cy)
            elif direction == "up_left":
                target = (-cx - 1, -cy - 1)
            elif direction == "up_right":
                target = (self.num_chunks_x * 2 - cx - 1, -cy - 1)
            elif direction == "down_left":
                target = (-cx - 1, self.num_chunks_y * 2 - cy - 1)
            elif direction == "down_right":
                target = (
                    self.num_chunks_x * 2 - cx - 1,
                    self.num_chunks_y * 2 - cy - 1,
                )
            else:
                continue
            if target in self.Chunks:
                continue
            mirrored = {
                self.getAlgoritm(direction, lx, ly): block
                for (lx, ly), block in source.blocks.items()
            }
            self.load_chunk(target, mirrored, fake=True)

    def update_background_loading(self):
        """Load missing nearby chunks; distant chunks are never sent to the renderer."""
        now = time.monotonic()
        if now - self.last_chunk_load_time < 0.02:
            return
        self.last_chunk_load_time = now

        # Chunks actually intersecting the screen are loaded immediately so
        # they can never disappear while the camera is moving.
        on_screen = self.get_visible_chunks(margin=0)
        for key in on_screen:
            if key not in self.Chunks:
                self.load_chunk(key)

        # Preload the surrounding margin incrementally. Those chunks are not
        # rendered until they enter the camera area.
        missing = [key for key in self.get_visible_chunks() if key not in self.Chunks]
        if not missing:
            return

        center_x = -self.base_x - self.bx + conster.WIDTH / 2
        center_y = -self.base_y - self.by + conster.HEIGHT / 2
        chunk_w = self.CHUNK_SIZE * self.bw
        chunk_h = self.CHUNK_SIZE * self.bh
        missing.sort(key=lambda key: (
            (key[0] * chunk_w + chunk_w / 2 - center_x) ** 2
            + (key[1] * chunk_h + chunk_h / 2 - center_y) ** 2
        ))
        for key in missing[:4]:
            self.load_chunk(key)

    def move(self, dx, dy):
        # Camera movement is in pixels, not multiplied a second time by speed.
        self.bx += float(dx)
        self.by += float(dy)

    def getblock(self, world_x, world_y, w, h):
        result = {}
        left = int((world_x - self.base_x) // self.bw)
        top = int((world_y - self.base_y) // self.bh)
        right = int((world_x + max(0, w - 1) - self.base_x) // self.bw)
        bottom = int((world_y + max(0, h - 1) - self.base_y) // self.bh)
        chunk_pixels = self.CHUNK_SIZE * self.bw
        for gy in range(top, bottom + 1):
            for gx in range(left, right + 1):
                cx, lx = divmod(gx, self.CHUNK_SIZE)
                cy, ly = divmod(gy, self.CHUNK_SIZE)
                chunk = self.Chunks.get((cx, cy))
                if chunk is None:
                    continue
                block = chunk.get_block(lx, ly)
                result[((cx, cy), ly * self.CHUNK_SIZE + lx)] = block
        return result

    def render_cpp(self):
        visible = [
            self.Chunks[key]
            for key in self.get_visible_chunks()
            if key in self.Chunks and self.Chunks[key].is_loaded
        ]
        if not visible:
            return
        per_chunk = self.CHUNK_SIZE * self.CHUNK_SIZE
        block_array = (ctypes.c_int32 * (len(visible) * per_chunk))()
        coord_array = (ctypes.c_int32 * (len(visible) * 2))()
        for ci, chunk in enumerate(visible):
            coord_array[ci * 2] = chunk.chunk_x
            coord_array[ci * 2 + 1] = chunk.chunk_y
            base = ci * per_chunk
            for ly in range(self.CHUNK_SIZE):
                for lx in range(self.CHUNK_SIZE):
                    block = chunk.blocks.get((lx, ly))
                    block_array[base + ly * self.CHUNK_SIZE + lx] = (
                        block.id if block is not None else 0
                    )
        pr(
            block_array, coord_array, len(visible),
            self.CHUNK_SIZE, self.bw,
            self.bx, self.by, self.base_x, self.base_y,
        )
