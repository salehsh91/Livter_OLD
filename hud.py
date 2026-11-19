import ctypes
import conster
from cppfuncs import HUDSetData, HUDDraw, HUDGetSelectedSlot, HUDGetInventoryOpen


class HUD:
    """Python data bridge; SDL3/C++ owns all HUD drawing and mouse handling."""
    def __init__(self, inventory=None):
        self.inventory = inventory
        self.maxslots = getattr(inventory, "slotnum", 12)
        self.linesizedir = int(getattr(conster, "camdirline", 50))

    @staticmethod
    def _item_texture(item):
        if item is None:
            return -1
        if isinstance(item, dict):
            value = item.get("texture", -1)
        else:
            value = getattr(item, "texture", -1)
        try:
            return int(value)
        except (TypeError, ValueError):
            return -1

    def draw(self, player):
        if player is None:
            return

        status = player.getStatus()
        health = max(0, min(100, int(status.get("health", 0))))
        hungry = max(0, min(100, int(status.get("hungry", 0))))

        angle = float(getattr(player, "cameradir", 0.0))

        slots = self.inventory.getinvertory() if self.inventory else {}
        count = min(self.maxslots, 64)
        textures = (ctypes.c_int * 64)(*([-1] * 64))
        counts = (ctypes.c_int * 64)(*([0] * 64))
        active = (ctypes.c_int * 64)(*([0] * 64))

        for slot_id, data in slots.items():
            index = int(slot_id) - 1
            if index < 0 or index >= count:
                continue
            item, amount = data[0], data[1]
            textures[index] = self._item_texture(item)
            counts[index] = max(0, int(amount))
            active[index] = int(bool(data[2])) if len(data) > 2 else 0

        selected = HUDGetSelectedSlot()
        if selected and self.inventory:
            for key, data in list(slots.items()):
                self.inventory.slots[key] = (data[0], data[1], key == selected)

        HUDSetData(health, hungry, angle, textures, counts, active, count)
        HUDDraw(self.linesizedir)

    @property
    def inventory_open(self):
        return bool(HUDGetInventoryOpen())
