
#include <iostream>
#include <string>
#include <cstdint>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <algorithm>
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

EntityData* entities;

// --------------------------------------------------
// Export macro for Python / ctypes
// --------------------------------------------------

#define API extern "C" __declspec(dllexport)

// --------------------------------------------------
// Global data
// --------------------------------------------------

static std::unordered_map<std::string, SDL_Texture*> textures;

static SDL_Window* WINdow = nullptr;
static SDL_Renderer* RENderer = nullptr;

static bool running = true;

// Keys freshly pressed during the current frame
static std::unordered_set<SDL_Keycode> pressed_this_frame;

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

    SDL_Log("SDL initialized successfully.");
    return 0;
}

// --------------------------------------------------
// Process events
// Call render() once per frame.
// --------------------------------------------------

static int RenderInternal(SDL_Renderer* renderer) {
    SDL_Event ev;

    pressed_this_frame.clear();

    while (SDL_PollEvent(&ev)) {
        if (ev.type == SDL_EVENT_QUIT) {
            running = false;
        }

        if (ev.type == SDL_EVENT_KEY_DOWN && !ev.key.repeat) {
            pressed_this_frame.insert(ev.key.key);
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
    } else {
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
    int name = textures.size();
    if (!renderer || !path) {
        SDL_Log("LoadImage: renderer or path is null.");
        return false;
    }

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
    int name = textures.size();
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

    if (it == textures.end() || !it->second) {
        SDL_Log("Texture ID %d not found", texture_name);
        return false;
    }

    SDL_FRect dst = { x, y, w, h };

    if (!SDL_RenderTexture(renderer, it->second, nullptr, &dst)) {
        SDL_Log("SDL_RenderTexture failed: %s", SDL_GetError());
        return false;
    }

    return true;
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
//
// hold_scancodes: SDL_Scancode values
// press_keycodes: SDL_Keycode values
//
// Example output: H:W+D;P:Space
// H = held keys
// P = keys newly pressed this frame
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
    const int* press_keycodes,
    int press_count,
    char* output,
    int output_capacity
) {
    if (!output || output_capacity <= 0)
        return;

    output[0] = '\0';

    int keyboard_count = 0;
    const bool* keyboard = SDL_GetKeyboardState(&keyboard_count);

    std::string held;
    std::string pressed;

    if (keyboard && hold_scancodes && hold_count > 0) {
        for (int i = 0; i < hold_count; ++i) {
            const int scancode = hold_scancodes[i];

            if (scancode < 0 || scancode >= keyboard_count)
                continue;

            if (!keyboard[scancode])
                continue;

            // Use the scancode name so the held-key label
            // stays stable and does not depend on modifiers.
            append_text(
                held,
                SDL_GetScancodeName(
                    static_cast<SDL_Scancode>(scancode)
                )
            );
        }
    }

    if (press_keycodes && press_count > 0) {
        for (int i = 0; i < press_count; ++i) {
            const SDL_Keycode key =
                static_cast<SDL_Keycode>(press_keycodes[i]);

            if (pressed_this_frame.find(key) ==
                pressed_this_frame.end()) {
                continue;
            }

            append_text(pressed, SDL_GetKeyName(key));
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
// Present implementation
// --------------------------------------------------

static void present_internal() {
    if (!RENderer)
        return;

    if (!SDL_RenderPresent(RENderer)) {
        SDL_Log("SDL_RenderPresent failed: %s", SDL_GetError());
    }

    SDL_Delay(16);
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

    SDL_Quit();
    return 0;
}

// --------------------------------------------------
// Exported C API for Python / ctypes
// All exported names have C linkage.
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
    const int* press_keycodes,
    int press_count,
    char* output,
    int output_capacity
) {
    KeycontInternal(
        hold_scancodes,
        hold_count,
        press_keycodes,
        press_count,
        output,
        output_capacity
    );
}
API EntityData* CreateEntities(int count){return new EntityData[count];}