from blockitem import Block

class Chunk:
    def __init__(self, chunk_x, chunk_y, chunk_size, block_size,
                 world_offset_x, world_offset_y):
        self.chunk_x = int(chunk_x)
        self.chunk_y = int(chunk_y)
        self.chunk_size = int(chunk_size)
        self.block_size = int(block_size)
        self.world_x = world_offset_x + self.chunk_x * self.chunk_size * self.block_size
        self.world_y = world_offset_y + self.chunk_y * self.chunk_size * self.block_size
        self.blocks = {}
        self.is_loaded = False

    def generate(self, noise_function):
        if self.is_loaded:
            return
        for ly in range(self.chunk_size):
            for lx in range(self.chunk_size):
                gx = self.chunk_x * self.chunk_size + lx
                gy = self.chunk_y * self.chunk_size + ly
                block_name, _ = noise_function(gx, gy)
                self.blocks[(lx, ly)] = Block.getblock_status(name=block_name)
        self.is_loaded = True

    def set_blocks(self, blocks_dict):
        self.blocks = dict(blocks_dict)
        self.is_loaded = True

    def get_block(self, local_x, local_y):
        return self.blocks.get((local_x, local_y), Block.getblock_status(name="air"))
