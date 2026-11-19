Livter patch — only changed files

Changed files:
- hud.py: restores the prior HUD elements: health, hunger, 12 inventory slots, and the player's facing/camera-direction marker. It uses the existing SDL3 DrawObj renderer, not Pygame.
- world.py: creates/updates the HUD and draws it after world entities but before present().
- texture.py: loads the original assets/health.png and assets/hungry.png for the HUD when present; keeps the existing solid-color textures as fallback.
- BlockManager.py: calculates nearby chunk coordinates without clipping them to the old finite coordinate range; loads any missing on-screen chunks immediately and preloads up to four nearby margin chunks per update. Only the camera-near set is passed to C++ for rendering.

Validation: Python syntax compilation and a mocked chunk-selection/loading test. The SDL3 DLL and live game loop were not executable here, so visual runtime behavior still needs testing on Windows.
