# Livter — corrected SDL3 source snapshot

This source snapshot uses Python for world simulation and SDL3/C++ for window,
terrain, object and NPC rendering.

## Run on Windows

1. Keep `cppmain.dll`, `SDL3.dll`, and `SDL3_image.dll` beside the Python files.
2. Use the same 64-bit Python architecture as the DLL.
3. Run `python main.py` from this folder.

The current source no longer requires the `assets/` directory for basic terrain
and NPC rendering: `Texture.init()` creates solid-color SDL textures as a
safe fallback. Image assets can be added later without changing the block IDs.

## Important C++ note

`cmain.cpp` now exports an optional `RenderEntities()` function. If the DLL
does not export it, `cppfuncs.py` automatically falls back to drawing visible
NPCs with `drawobj`. Rebuild `cppmain.dll` from the updated `cmain.cpp` to use
the C++ entity-array renderer. The `EntityData` structure in `cppfuncs.py`
matches the C++ structure field-for-field.

## Architecture

- `main.py`: SDL initialization and game loop.
- `cppfuncs.py`: ctypes declarations and C ABI.
- `BlockManager.py` / `worldchunk.py`: seeded terrain and mirrored chunks.
- `npc.py`: NPC simulation and shared C++ entity-array synchronization.
- `object.py`: world objects.
- `texture.py` / `blockitem.py`: stable numeric texture/block IDs.
- `world.py`: connects simulation and rendering.

`World.txt`, `npc.txt`, and the Pygame HUD/button code are retained as legacy
reference files; they are not part of the active SDL3 game loop.

## Platform limitation

`buildozer.spec` is a legacy Pygame/SDL2 Android configuration. It does not
build this Windows `cppmain.dll` SDL3 backend for Android. Android packaging
needs a separate native SDL3 build and is not claimed to be fixed by this
snapshot.
