#include <iostream>
#include <string>
#include <cstdint>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstring>

#include <SDL3/SDL.h>
#include <SDL3_image/SDL_image.h>

struct EntityData {
    int kind;
    int active;
    int id;

    float world_x;
    float world_y;
    float world_z;

    int texture;

    float width;
    float height;
    float length;

    float bx;
    float by;

    float display_alpha;
};

EntityData* entities = nullptr;
static int entity_count = 0;

#if defined(_WIN32)
#define API extern "C" __declspec(dllexport)
#else
#define API extern "C" __attribute__((visibility("default")))
#endif

// --------------------------------------------------
// Global data
// --------------------------------------------------

static std::unordered_map<std::string, SDL_Texture*> textures;

static SDL_Window* WINdow = nullptr;
static SDL_Renderer* RENderer = nullptr;

static bool running = true;

// Keys currently held and keys newly pressed during the current frame.
static std::unordered_set<SDL_Scancode> held_scancodes;
static std::unordered_set<SDL_Scancode> pressed_this_frame;

// HUD state is owned and rendered entirely by C++.
static int hud_health = 100;
static int hud_hunger = 0;
static float hud_camera_angle = 0.0f;
static int hud_slot_textures[64] = {};
static int hud_slot_counts[64] = {};
static int hud_slot_active[64] = {};
static int hud_slot_present[64] = {};
static int hud_slot_count = 0;
static bool hud_inventory_open = true;
static int hud_selected_slot = 0;

// FPS is measured from calls to present(), i.e. rendered game frames.
static int hud_fps = 0;
static Uint64 fps_last_counter = 0;
static Uint64 fps_frame_count = 0;
static Uint64 fps_frequency = 0;

// --------------------------------------------------
// Renderer / Window
// --------------------------------------------------

static SDL_Renderer* GetRendererInternal() {
    return RENderer;
}

static SDL_Window* GetWindowInternal() {
    return WINdow;
}

// --------------------------------------------------
// Frame
// --------------------------------------------------

static void frame(SDL_Renderer* renderer) {
    if (!renderer)
        return;

    SDL_SetRenderDrawColor(renderer, 25, 30, 40, 255);
    SDL_RenderClear(renderer);
}

// --------------------------------------------------
// Initialize SDL
// --------------------------------------------------

static int INIT() {
    if (!SDL_Init(SDL_INIT_VIDEO)) {
        SDL_Log("SDL_Init failed: %s", SDL_GetError());
        return 1;
    }

    WINdow = SDL_CreateWindow(
        "Livter",
        1280,
        720,
        SDL_WINDOW_RESIZABLE
    );

    if (!WINdow) {
        SDL_Log("SDL_CreateWindow failed: %s", SDL_GetError());
        SDL_Quit();
        return 1;
    }

    RENderer = SDL_CreateRenderer(WINdow, nullptr);

    if (!RENderer) {
        SDL_Log("SDL_CreateRenderer failed: %s", SDL_GetError());
        SDL_DestroyWindow(WINdow);
        WINdow = nullptr;
        SDL_Quit();
        return 1;
    }

    running = true;

    hud_fps = 0;
    fps_last_counter = 0;
    fps_frame_count = 0;
    fps_frequency = SDL_GetPerformanceFrequency();

    SDL_Log("SDL initialized successfully.");
    return 0;
}

// --------------------------------------------------
// Process events
// Call render() once per frame.
// --------------------------------------------------

static void handle_hud_click(float mx, float my) {
    if (!WINdow) return;

    int width = 0, height = 0;
    SDL_GetWindowSize(WINdow, &width, &height);

    // Same rectangle as pygame.Rect(WIDTH - 140, 10, 130, 45).
    const SDL_FRect button = {
        static_cast<float>(width - 140), 10.0f, 130.0f, 45.0f
    };

    if (mx >= button.x && mx < button.x + button.w &&
        my >= button.y && my < button.y + button.h) {
        hud_inventory_open = !hud_inventory_open;
        return;
    }

    if (!hud_inventory_open) return;

    constexpr int slot_size = 50;
    constexpr int gap = 10;
    constexpr int columns = 6;
    const int rows = (hud_slot_count + columns - 1) / columns;
    const int grid_height = rows * (slot_size + gap);
    const int grid_width = columns * (slot_size + gap);

    // Exact Python expression:
    // y = HEIGHT - int(h / columns) * gap - gap
    const int x = width - grid_width - 20;
    const int y = height - (grid_height / columns) * gap - gap;

    for (int i = 0; i < hud_slot_count; ++i) {
        if (!hud_slot_present[i])
            continue; // Python click_slot() ignores empty inventory IDs.

        const int col = i % columns;
        const int row = i / columns;
        const float sx = static_cast<float>(x + col * (slot_size + gap));
        const float sy = static_cast<float>(y + row * (slot_size + gap));

        if (mx >= sx && mx < sx + slot_size &&
            my >= sy && my < sy + slot_size) {
            hud_selected_slot = i + 1;
            for (int j = 0; j < hud_slot_count; ++j)
                hud_slot_active[j] = (j == i && hud_slot_present[j]) ? 1 : 0;
            return;
        }
    }
}

static int RenderInternal(SDL_Renderer* renderer) {
    SDL_Event ev;

    pressed_this_frame.clear();

    while (SDL_PollEvent(&ev)) {

        if (ev.type == SDL_EVENT_QUIT) {
            running = false;
        }

        if (ev.type == SDL_EVENT_MOUSE_BUTTON_DOWN) {
            if (ev.button.button == SDL_BUTTON_LEFT)
                handle_hud_click(ev.button.x, ev.button.y);
        }
        else if (ev.type == SDL_EVENT_KEY_DOWN) {
            held_scancodes.insert(ev.key.scancode);
            if (!ev.key.repeat)
                pressed_this_frame.insert(ev.key.scancode);
        }
        else if (ev.type == SDL_EVENT_KEY_UP) {
            held_scancodes.erase(ev.key.scancode);
        }
        else if (ev.type == SDL_EVENT_WINDOW_FOCUS_LOST) {
            // Prevent stuck keys if the window loses focus while a key is down.
            held_scancodes.clear();
        }
    }

    if (!running)
        return 0;

    frame(renderer);
    return 1;
}

// --------------------------------------------------
// Create solid-color texture
// --------------------------------------------------

static SDL_Texture* create_color_texture(
    SDL_Renderer* renderer,
    Uint8 r,
    Uint8 g,
    Uint8 b,
    Uint8 a
) {
    if (!renderer)
        return nullptr;

    SDL_Surface* surface = SDL_CreateSurface(
        1,
        1,
        SDL_PIXELFORMAT_RGBA32
    );

    if (!surface) {
        SDL_Log("SDL_CreateSurface failed: %s", SDL_GetError());
        return nullptr;
    }

    Uint32 color = SDL_MapSurfaceRGBA(surface, r, g, b, a);
    SDL_FillSurfaceRect(surface, nullptr, color);

    SDL_Texture* texture =
        SDL_CreateTextureFromSurface(renderer, surface);

    SDL_DestroySurface(surface);

    if (!texture) {
        SDL_Log(
            "SDL_CreateTextureFromSurface failed: %s",
            SDL_GetError()
        );
    }

    return texture;
}

// --------------------------------------------------
// Store / replace texture
// --------------------------------------------------

static void store_texture(int name, SDL_Texture* texture) {
    if (!texture)
        return;

    std::string key = std::to_string(name);
    auto it = textures.find(key);

    if (it != textures.end()) {
        if (it->second)
            SDL_DestroyTexture(it->second);

        it->second = texture;
    }
    else {
        textures.emplace(key, texture);
    }
}

// --------------------------------------------------
// Load image texture
// --------------------------------------------------

static int LoadImageInternal(
    SDL_Renderer* renderer,
    const char* path
) {
    if (!renderer || !path) {
        SDL_Log("LoadImage: renderer or path is null.");
        return -1;
    }

    int name = static_cast<int>(textures.size());

    SDL_Texture* texture = IMG_LoadTexture(renderer, path);

    if (!texture) {
        SDL_Log(
            "Failed to load texture '%s': %s",
            path,
            SDL_GetError()
        );
        return -1;
    }

    store_texture(name, texture);

    SDL_Log("Loaded texture ID %d from %s", name, path);
    return name;
}

// --------------------------------------------------
// Create and store color texture
// --------------------------------------------------

static int loadtexture(
    SDL_Renderer* renderer,
    Uint8 r,
    Uint8 g,
    Uint8 b,
    Uint8 a
) {
    if (!renderer)
        return -1;

    int name = static_cast<int>(textures.size());

    SDL_Texture* texture =
        create_color_texture(renderer, r, g, b, a);

    if (!texture) {
        SDL_Log("Could not create texture ID %d", name);
        return -1;
    }

    store_texture(name, texture);
    return name;
}

// --------------------------------------------------
// Draw one textured rectangle
// --------------------------------------------------

static bool DrawObj(
    SDL_Renderer* renderer,
    float x,
    float y,
    float w,
    float h,
    int texture_name
) {
    if (!renderer)
        return false;

    auto it = textures.find(std::to_string(texture_name));

    if (it == textures.end() || !it->second)
        return false;

    SDL_FRect dst = { x, y, w, h };

    if (!SDL_RenderTexture(renderer, it->second, nullptr, &dst)) {
        SDL_Log("SDL_RenderTexture failed: %s", SDL_GetError());
        return false;
    }

    return true;
}

// --------------------------------------------------
// HUD drawing (SDL3 only)
// --------------------------------------------------
static void hud_fill(SDL_Renderer* renderer, float x, float y,
                     float w, float h, Uint8 r, Uint8 g, Uint8 b, Uint8 a=255) {
    if (!renderer || w <= 0 || h <= 0) return;
    SDL_SetRenderDrawColor(renderer, r, g, b, a);
    SDL_FRect rect = {x, y, w, h};
    SDL_RenderFillRect(renderer, &rect);
}

static void hud_text(SDL_Renderer* renderer, const std::string& value,
                     float x, float y, int scale=2) {
    // Compact 3x5 bitmap font for the Inventory label and stack counts.
    static const std::unordered_map<char, std::array<const char*, 5>> glyphs = {
        {'I', {"111", "010", "010", "010", "111"}},
        {'N', {"101", "111", "111", "111", "101"}},
        {'F', {"111", "100", "110", "100", "100"}},
        {'P', {"110", "101", "110", "100", "100"}},
        {'S', {"111", "100", "111", "001", "111"}},
        {':', {"000", "010", "000", "010", "000"}},
        {'V', {"101", "101", "101", "101", "010"}},
        {'E', {"111", "100", "110", "100", "111"}},
        {'T', {"111", "010", "010", "010", "010"}},
        {'O', {"111", "101", "101", "101", "111"}},
        {'R', {"110", "101", "110", "101", "101"}},
        {'Y', {"101", "101", "010", "010", "010"}},
        {'0', {"111", "101", "101", "101", "111"}},
        {'1', {"010", "110", "010", "010", "111"}},
        {'2', {"111", "001", "111", "100", "111"}},
        {'3', {"111", "001", "111", "001", "111"}},
        {'4', {"101", "101", "111", "001", "001"}},
        {'5', {"111", "100", "111", "001", "111"}},
        {'6', {"111", "100", "111", "101", "111"}},
        {'7', {"111", "001", "010", "010", "010"}},
        {'8', {"111", "101", "111", "101", "111"}},
        {'9', {"111", "101", "111", "001", "111"}}
    };
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    float cursor = x;
    for (char ch : value) {
        auto it = glyphs.find(static_cast<char>(std::toupper(static_cast<unsigned char>(ch))));
        if (it == glyphs.end()) { cursor += 4 * scale; continue; }
        for (int row = 0; row < 5; ++row)
            for (int col = 0; col < 3; ++col)
                if (it->second[row][col] == '1') {
                    SDL_FRect pixel = {cursor + col * scale, y + row * scale,
                                       static_cast<float>(scale), static_cast<float>(scale)};
                    SDL_RenderFillRect(renderer, &pixel);
                }
        cursor += 4 * scale;
    }
}

static void DrawHUDInternal(SDL_Renderer* renderer, int width, int height,
                            int direction_length) {
    if (!renderer) return;

    // Match Python: range(max(0, health // 10)); no artificial 10-icon cap.
    const int health_icons = std::max(0, static_cast<int>(std::floor(hud_health / 10.0f)));
    const int hunger_icons = std::max(0, static_cast<int>(std::floor(hud_hunger / 10.0f)));

    for (int i = 0; i < health_icons; ++i) {
        const float y = 10.0f + static_cast<float>(i) * 12.0f;
        DrawObj(renderer, 20.0f, y, 10.0f, 10.0f, 8);
    }
    for (int i = 0; i < hunger_icons; ++i) {
        const float y = 10.0f + static_cast<float>(i) * 12.0f;
        DrawObj(renderer, 40.0f, y, 10.0f, 10.0f, 9);
    }

    // FPS counter (updated in present_internal).
    hud_text(renderer, "FPS:" + std::to_string(hud_fps), 70.0f, 10.0f, 2);

    if (hud_inventory_open) {
        constexpr int slot_size = 50;
        constexpr int gap = 10;
        constexpr int columns = 6;
        const int rows = (hud_slot_count + columns - 1) / columns;
        const int grid_width = columns * (slot_size + gap);
        const int grid_height = rows * (slot_size + gap);
        const float x = static_cast<float>(width - grid_width - 20);
        // Exact Python expression: HEIGHT - int(h / columns) * gap - gap.
        const float y = static_cast<float>(height - (grid_height / columns) * gap - gap);

        hud_fill(renderer, x, y, static_cast<float>(grid_width),
                 static_cast<float>(grid_height), 50, 50, 50);

        // Python iterates inventory.items(), so empty IDs have no slot drawn.
        for (int i = 0; i < hud_slot_count; ++i) {
            if (!hud_slot_present[i])
                continue;

            const int col = i % columns;
            const int row = i / columns;
            const float sx = x + static_cast<float>(col * (slot_size + gap));
            const float sy = y + static_cast<float>(row * (slot_size + gap));

            if (hud_slot_active[i] || hud_selected_slot == i + 1)
                hud_fill(renderer, sx, sy, 50.0f, 50.0f, 255, 255, 0);

            hud_fill(renderer, sx + 2.0f, sy + 2.0f, 46.0f, 46.0f, 80, 80, 80);

            if (hud_slot_textures[i] >= 0) {
                DrawObj(renderer, sx + 5.0f, sy + 5.0f,
                        40.0f, 40.0f, hud_slot_textures[i]);
            }

            if (hud_slot_counts[i] > 1) {
                // Same top-left position used by pygame: (slot_x + 35, slot_y + 32).
                hud_text(renderer, std::to_string(hud_slot_counts[i]),
                         sx + 35.0f, sy + 32.0f, 2);
            }
        }
    }

    // Draw the toggle button after the inventory, matching HUD.draw() order.
    // Exact Python rectangle and color: (70, 70, 70).
    const float button_x = static_cast<float>(width - 140);
    hud_fill(renderer, button_x, 10.0f, 130.0f, 45.0f, 70, 70, 70);
    hud_text(renderer, "Inventory", button_x + 29.0f, 26.0f, 2);

    // Same angle convention, center, length and white 2px direction line.
    const float cx = width / 2.0f;
    const float cy = height / 2.0f;
    const float radians = hud_camera_angle * 0.01745329251994329577f;
    const float ex = cx + std::sin(radians) * direction_length;
    const float ey = cy - std::cos(radians) * direction_length;

    // Build a 2px-wide quad, matching pygame.draw.line(..., width=2).
    float dx = ex - cx;
    float dy = ey - cy;
    const float length = std::sqrt(dx * dx + dy * dy);
    if (length > 0.0f) {
        const float px = -dy / length;
        const float py = dx / length;
        const SDL_FColor white = {1.0f, 1.0f, 1.0f, 1.0f};
        SDL_Vertex vertices[4] = {
            {{cx + px, cy + py}, white, {0.0f, 0.0f}},
            {{ex + px, ey + py}, white, {0.0f, 0.0f}},
            {{ex - px, ey - py}, white, {0.0f, 0.0f}},
            {{cx - px, cy - py}, white, {0.0f, 0.0f}}
        };
        const int indices[6] = {0, 1, 2, 0, 2, 3};
        SDL_RenderGeometry(renderer, nullptr, vertices, 4, indices, 6);
    }
}

// --------------------------------------------------
// Batched chunk rendering
// --------------------------------------------------

static void Pr(
    const int32_t* blocks,
    const int32_t* chunk_coords,
    int chunk_count,
    int chunk_size,
    int block_size,
    float camera_x,
    float camera_y,
    float world_offset_x,
    float world_offset_y
) {
    if (!RENderer || !WINdow || !blocks || !chunk_coords)
        return;

    if (chunk_count <= 0 || chunk_size <= 0 || block_size <= 0)
        return;

    const int blocks_per_chunk = chunk_size * chunk_size;

    int screen_w = 0;
    int screen_h = 0;

    SDL_GetWindowSize(WINdow, &screen_w, &screen_h);

    if (screen_w <= 0 || screen_h <= 0)
        return;

    struct TextureBatch {
        SDL_Texture* texture = nullptr;
        std::vector<SDL_Vertex> vertices;
        std::vector<int> indices;
    };

    std::unordered_map<int32_t, TextureBatch> batches;

    for (int c = 0; c < chunk_count; ++c) {

        const int chunk_x = chunk_coords[c * 2];
        const int chunk_y = chunk_coords[c * 2 + 1];

        const float origin_x =
            world_offset_x
            + static_cast<float>(chunk_x) * chunk_size * block_size
            + camera_x;

        const float origin_y =
            world_offset_y
            + static_cast<float>(chunk_y) * chunk_size * block_size
            + camera_y;

        const float chunk_w =
            static_cast<float>(chunk_size) * block_size;

        const float chunk_h = chunk_w;

        if (origin_x + chunk_w <= 0 ||
            origin_x >= screen_w ||
            origin_y + chunk_h <= 0 ||
            origin_y >= screen_h) {
            continue;
        }

        const int chunk_base = c * blocks_per_chunk;

        for (int i = 0; i < blocks_per_chunk; ++i) {

            const int32_t block_id = blocks[chunk_base + i];

            if (block_id == 0)
                continue;

            auto tex_it = textures.find(std::to_string(block_id));

            if (tex_it == textures.end() || !tex_it->second)
                continue;

            const float x =
                origin_x + static_cast<float>(i % chunk_size) * block_size;

            const float y =
                origin_y + static_cast<float>(i / chunk_size) * block_size;

            const float w = static_cast<float>(block_size);
            const float h = static_cast<float>(block_size);

            if (x + w <= 0 || x >= screen_w ||
                y + h <= 0 || y >= screen_h) {
                continue;
            }

            auto& batch = batches[block_id];
            batch.texture = tex_it->second;

            const int base = static_cast<int>(batch.vertices.size());

            const SDL_FColor color = { 1, 1, 1, 1 };

            batch.vertices.push_back({
                { x, y },
                color,
                { 0, 0 }
            });

            batch.vertices.push_back({
                { x + w, y },
                color,
                { 1, 0 }
            });

            batch.vertices.push_back({
                { x + w, y + h },
                color,
                { 1, 1 }
            });

            batch.vertices.push_back({
                { x, y + h },
                color,
                { 0, 1 }
            });

            batch.indices.push_back(base);
            batch.indices.push_back(base + 1);
            batch.indices.push_back(base + 2);

            batch.indices.push_back(base);
            batch.indices.push_back(base + 2);
            batch.indices.push_back(base + 3);
        }
    }

    for (auto& entry : batches) {

        const int32_t block_id = entry.first;
        auto& batch = entry.second;

        if (batch.vertices.empty() || !batch.texture)
            continue;

        if (!SDL_RenderGeometry(
            RENderer,
            batch.texture,
            batch.vertices.data(),
            static_cast<int>(batch.vertices.size()),
            batch.indices.data(),
            static_cast<int>(batch.indices.size())
        )) {
            SDL_Log(
                "SDL_RenderGeometry failed for block ID %d: %s",
                block_id,
                SDL_GetError()
            );
        }
    }
}

// --------------------------------------------------
// Key handling
// H = held keys
// P = newly pressed keys
// --------------------------------------------------

static void append_text(
    std::string& out,
    const char* text
) {
    if (!text || !text[0])
        return;

    if (!out.empty())
        out += '+';

    out += text;
}

static void KeycontInternal(
    const int* hold_scancodes,
    int hold_count,
    const int* press_scancodes,
    int press_count,
    char* output,
    int output_capacity
) {
    if (!output || output_capacity <= 0)
        return;

    output[0] = '\0';

    std::string held;
    std::string pressed;

    // Held keys
    if (hold_scancodes && hold_count > 0) {
        for (int i = 0; i < hold_count; ++i) {
            const int value = hold_scancodes[i];
            if (value < 0 || value >= SDL_SCANCODE_COUNT)
                continue;

            const SDL_Scancode key = static_cast<SDL_Scancode>(value);
            if (held_scancodes.find(key) == held_scancodes.end())
                continue;

            append_text(held, SDL_GetScancodeName(key));
        }
    }

    // Newly pressed keys
    if (press_scancodes && press_count > 0) {

        for (int i = 0; i < press_count; ++i) {

            const int value = press_scancodes[i];

            if (value < 0 || value >= SDL_SCANCODE_COUNT)
                continue;

            const SDL_Scancode key =
                static_cast<SDL_Scancode>(value);

            if (pressed_this_frame.find(key) ==
                pressed_this_frame.end()) {
                continue;
            }

            append_text(
                pressed,
                SDL_GetScancodeName(key)
            );
        }
    }

    std::string result;

    if (!held.empty())
        result = "H:" + held;

    if (!pressed.empty()) {

        if (!result.empty())
            result += ';';

        result += "P:" + pressed;
    }

    const size_t n = std::min(
        result.size(),
        static_cast<size_t>(output_capacity - 1)
    );

    std::memcpy(output, result.data(), n);
    output[n] = '\0';
}

// --------------------------------------------------
// Present
// --------------------------------------------------

static void update_fps_counter() {
    const Uint64 now = SDL_GetPerformanceCounter();

    if (fps_frequency == 0)
        fps_frequency = SDL_GetPerformanceFrequency();

    if (fps_last_counter == 0) {
        fps_last_counter = now;
        fps_frame_count = 1;
        return;
    }

    ++fps_frame_count;

    const double elapsed =
        static_cast<double>(now - fps_last_counter) /
        static_cast<double>(fps_frequency);

    // Refresh the displayed value twice per second.
    if (elapsed >= 0.5) {
        hud_fps = static_cast<int>(
            std::lround(static_cast<double>(fps_frame_count) / elapsed)
        );

        fps_frame_count = 0;
        fps_last_counter = now;
    }
}

static void present_internal() {
    if (!RENderer)
        return;

    update_fps_counter();
    SDL_RenderPresent(RENderer);
    // SDL_Delay(1);
}

// --------------------------------------------------
// Shutdown
// --------------------------------------------------

static int quit_internal() {

    for (auto& entry : textures) {
        if (entry.second)
            SDL_DestroyTexture(entry.second);
    }

    textures.clear();

    if (RENderer) {
        SDL_DestroyRenderer(RENderer);
        RENderer = nullptr;
    }

    if (WINdow) {
        SDL_DestroyWindow(WINdow);
        WINdow = nullptr;
    }

    delete[] entities;
    entities = nullptr;
    entity_count = 0;

    SDL_Quit();

    return 0;
}

// --------------------------------------------------
// Exported C API
// --------------------------------------------------

API int Init() {
    return INIT();
}

API SDL_Window* GetWINDOW() {
    return GetWindowInternal();
}

API SDL_Renderer* GetRENDERER() {
    return GetRendererInternal();
}

API int render() {
    return RenderInternal(GetRendererInternal());
}

API void present() {
    present_internal();
}

API int LoadTexture(
    SDL_Renderer* renderer,
    Uint8 r,
    Uint8 g,
    Uint8 b,
    Uint8 a
) {
    return loadtexture(renderer, r, g, b, a);
}

API int LoadImageTexture(
    SDL_Renderer* renderer,
    const char* path
) {
    return LoadImageInternal(renderer, path);
}

API bool drawobj(
    SDL_Renderer* renderer,
    float x,
    float y,
    float w,
    float h,
    int texture_name
) {
    return DrawObj(renderer, x, y, w, h, texture_name);
}

API void HUDSetData(int health, int hunger, float camera_angle,
                    const int* item_textures, const int* item_counts,
                    const int* item_active, const int* item_present,
                    int slot_count) {
    hud_health = std::max(0, health);
    hud_hunger = std::max(0, hunger);
    hud_camera_angle = camera_angle;
    hud_slot_count = std::clamp(slot_count, 0, 64);

    for (int i = 0; i < 64; ++i) {
        const bool in_range = i < hud_slot_count;
        hud_slot_textures[i] = (in_range && item_textures) ? item_textures[i] : -1;
        hud_slot_counts[i] = (in_range && item_counts) ? std::max(0, item_counts[i]) : 0;
        hud_slot_active[i] = (in_range && item_active) ? item_active[i] : 0;
        hud_slot_present[i] = (in_range && item_present) ? item_present[i] : 0;
    }

    if (hud_selected_slot > hud_slot_count ||
        (hud_selected_slot > 0 && !hud_slot_present[hud_selected_slot - 1])) {
        hud_selected_slot = 0;
    }
}

API void HUDDraw(int direction_length) {
    if (!RENderer || !WINdow) return;
    int width = 0, height = 0;
    SDL_GetWindowSize(WINdow, &width, &height);
    DrawHUDInternal(RENderer, width, height, direction_length);
}

API int HUDGetSelectedSlot() { return hud_selected_slot; }
API int HUDGetInventoryOpen() { return hud_inventory_open ? 1 : 0; }

API void pr(
    const int32_t* blocks,
    const int32_t* chunk_coords,
    int chunk_count,
    int chunk_size,
    int block_size,
    float camera_x,
    float camera_y,
    float world_offset_x,
    float world_offset_y
) {
    Pr(
        blocks,
        chunk_coords,
        chunk_count,
        chunk_size,
        block_size,
        camera_x,
        camera_y,
        world_offset_x,
        world_offset_y
    );
}

API void GetWindowsize(
    int* w,
    int* h,
    SDL_Window* window
) {
    if (!w || !h)
        return;

    if (!window)
        window = GetWindowInternal();

    if (!window) {
        *w = -1;
        *h = -1;
        return;
    }

    SDL_GetWindowSize(window, w, h);
}

API int Quit() {
    return quit_internal();
}

API void keycont(
    const int* hold_scancodes,
    int hold_count,
    const int* press_scancodes,
    int press_count,
    char* output,
    int output_capacity
) {
    KeycontInternal(
        hold_scancodes,
        hold_count,
        press_scancodes,
        press_count,
        output,
        output_capacity
    );
}

API EntityData* CreateEntities(int count) {

    if (count <= 0)
        return nullptr;

    delete[] entities;

    entities = new EntityData[count]();
    entity_count = count;

    return entities;
}


// --------------------------------------------------
// Render Python-owned entity data
// --------------------------------------------------

API int RenderEntities() {
    if (!RENderer || !entities)
        return 0;

    int drawn = 0;
    for (int i = 0; i < entity_count; ++i) {
        const EntityData& e = entities[i];
        if (!e.active || e.texture < 0)
            continue;

        if (DrawObj(
            RENderer,
            e.world_x + e.bx,
            e.world_y + e.by,
            e.width,
            e.height,
            e.texture
        )) {
            ++drawn;
        }
    }
    return drawn;
}
