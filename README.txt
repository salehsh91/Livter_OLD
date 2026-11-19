Livter - Final SDL3/C++ HUD patch

Changed files only:
- cmain.cpp
- cppfuncs.py
- hud.py
- texture.py

world.py is intentionally unchanged: the current project already creates the
12-slot inventory and calls HUD.draw(player) after rendering the world.

HUD behavior/layout copied from the supplied Pygame HUD:
- health: x=20, y=10+i*12, 10x10, texture ID 8
- hunger: x=40, y=10+i*12, 10x10, texture ID 9
- Inventory button: (WIDTH-140, 10, 130, 45), RGB(70,70,70)
- six columns, 50x50 slots, 10px gap
- panel x=WIDTH-grid_width-20
- panel y=HEIGHT-int(grid_height/6)*10-10 (the same unusual formula as Python)
- only occupied inventory IDs draw a slot; clicking empty IDs does nothing
- active slot is yellow; item texture is 40x40; count appears only when >1
- left mouse button toggles the panel and selects occupied slots
- camera direction uses the same sin/cos angle convention, center, and length

Important texture behavior:
- PNG assets are loaded from <project folder>/assets using absolute paths.
- Missing or unreadable PNG files now raise a clear error instead of silently
  creating a solid-color substitute. This avoids mistaking fallback colors
  for successfully loaded images.
- Keep the existing assets folder and its original PNGs when copying this patch.
  The uploaded Game.zip did not contain an assets folder, so the images could
  not be bundled or verified here.
- Texture IDs remain fixed: air=0, grass=1, stone=2, water=3, sand=4,
  plank=5, oak=6, leaves=7, health=8, hungry=9, npc1=10.

After copying these four files, rebuild cppmain.dll from the new cmain.cpp.
The Python declarations call the updated HUDSetData ABI, so an old DLL is
not compatible with these files.

Validation performed:
- Python py_compile passed for hud.py, cppfuncs.py, texture.py and world.py.
- Layout arithmetic checked for the 12-slot / 6-column case.
- The C++ DLL was not compiled or run in this environment because the SDL3
  and SDL3_image development headers/import libraries are not available here.
- The Pygame default font is not linked into this SDL3-only build; the HUD
  label/counts use the small built-in bitmap glyph renderer. Geometry, colors,
  coordinates, item display rules and click behavior follow the Python code.
