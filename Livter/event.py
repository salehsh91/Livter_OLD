import pygame as pyg

def eventManager(ev, world):
    """Legacy pygame event adapter; the active SDL3 loop does not call this."""
    if ev.type != pyg.KEYDOWN:
        return
    manager = getattr(world, "blockManager", None)
    if manager is None:
        return
    if ev.key == pyg.K_w:
        manager.move(0, 5)
    elif ev.key == pyg.K_s:
        manager.move(0, -5)
    elif ev.key == pyg.K_d:
        manager.move(-5, 0)
    elif ev.key == pyg.K_a:
        manager.move(5, 0)
