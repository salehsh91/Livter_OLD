cmake_minimum_required(VERSION 3.22)
project(LivterNative LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# SDL3 Android requirements: compile SDL3 itself with the Android NDK.
include(FetchContent)

set(SDL_SHARED ON CACHE BOOL "" FORCE)
set(SDL_STATIC OFF CACHE BOOL "" FORCE)
set(SDL_TEST_LIBRARY OFF CACHE BOOL "" FORCE)
set(SDL_TESTS OFF CACHE BOOL "" FORCE)
set(SDL_EXAMPLES OFF CACHE BOOL "" FORCE)

FetchContent_Declare(
    SDL3
    GIT_REPOSITORY https://github.com/libsdl-org/SDL.git
    GIT_TAG release-3.4.14
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(SDL3)

set(SDLIMAGE_VENDORED ON CACHE BOOL "" FORCE)
set(SDLIMAGE_SHARED ON CACHE BOOL "" FORCE)
set(SDLIMAGE_STATIC OFF CACHE BOOL "" FORCE)
set(SDLIMAGE_SAMPLES OFF CACHE BOOL "" FORCE)
set(SDLIMAGE_TESTS OFF CACHE BOOL "" FORCE)

FetchContent_Declare(
    SDL3_image
    GIT_REPOSITORY https://github.com/libsdl-org/SDL_image.git
    GIT_TAG release-3.4.8
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(SDL3_image)

# This builds the current C++ bridge as an Android shared library.
# It does NOT by itself launch the Python game loop; see PORTING_NOTES.md.
add_library(livter_native SHARED cmain_android.cpp)

target_link_libraries(livter_native
    PRIVATE
        SDL3::SDL3
        SDL3_image::SDL3_image
        android
        log
)

target_compile_definitions(livter_native PRIVATE SDL_MAIN_HANDLED)
