import pygame
import os

BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets")
SPRITES = {}


def load_image(*path_parts, scale=None, colorkey=None):
    full_path = os.path.join(BASE_PATH, *path_parts)
    image = pygame.image.load(full_path).convert_alpha()
    if scale:
        image = pygame.transform.scale(image, scale)
    if colorkey is not None:
        image.set_colorkey(colorkey)
    return image


def load_font(*path_parts, size=24):
    full_path = os.path.join(BASE_PATH, *path_parts)
    return pygame.font.Font(full_path, size)


def init_sprites():
    sprites_path = os.path.join(BASE_PATH, "sprites")
    if not os.path.isdir(sprites_path):
        return

    for file in sorted(os.listdir(sprites_path)):
        if not file.endswith(".png"):
            continue
        name = os.path.splitext(file)[0]
        full = os.path.join(sprites_path, file)
        surf = pygame.image.load(full)
        if pygame.display.get_surface():
            surf = surf.convert_alpha()
        SPRITES[name] = surf
