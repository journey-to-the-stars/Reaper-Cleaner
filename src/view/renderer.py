import pygame
from src.config.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, ROOM_COLS, ROOM_ROWS, BLACK,
)
from src.config.assets import SPRITES
from src.model.level.tile import TileType


class Renderer:
    def __init__(self, screen, camera):
        self.screen = screen
        self.camera = camera
        self._floor = SPRITES.get("floor_lust")
        self._wall_a = SPRITES.get("wall_lust")
        self._wall_b = SPRITES.get("wall_with_star_lust") or self._wall_a

    def draw_room(self, room):
        ox, oy = self.camera.offset_x, self.camera.offset_y
        tiles = room.tiles

        for y in range(len(tiles)):
            for x in range(len(tiles[0])):
                tile = tiles[y][x]

                if tile == TileType.DOOR:
                    self.screen.fill(BLACK, (
                        x * TILE_SIZE + ox, y * TILE_SIZE + oy,
                        TILE_SIZE, TILE_SIZE,
                    ))
                    continue

                if tile == TileType.WALL:
                    sprite = self._wall_b if (hash((x, y)) & 1) else self._wall_a
                    self.screen.blit(sprite, (x * TILE_SIZE + ox, y * TILE_SIZE + oy))
                    continue

                if tile == TileType.FLOOR and self._floor:
                    self.screen.blit(self._floor, (x * TILE_SIZE + ox, y * TILE_SIZE + oy))
                    continue

                self.screen.fill(BLACK, (
                    x * TILE_SIZE + ox, y * TILE_SIZE + oy,
                    TILE_SIZE, TILE_SIZE,
                ))

    def draw_sprite(self, sprite):
        self.screen.blit(sprite.image, self.camera.apply(sprite))

    def draw_sprites(self, group):
        for sprite in group:
            self.draw_sprite(sprite)

    def draw_wall_overlay(self, room=None):
        ox, oy = self.camera.offset_x, self.camera.offset_y
        if room:
            room_w = room.room_width * TILE_SIZE
            room_h = room.room_height * TILE_SIZE
        else:
            room_w = ROOM_COLS * TILE_SIZE
            room_h = ROOM_ROWS * TILE_SIZE

        if ox > 0:
            self.screen.fill(BLACK, (0, 0, ox, SCREEN_HEIGHT))
        if oy > 0:
            self.screen.fill(BLACK, (0, 0, SCREEN_WIDTH, oy))
        if ox + room_w < SCREEN_WIDTH:
            self.screen.fill(BLACK, (ox + room_w, 0, SCREEN_WIDTH - ox - room_w, SCREEN_HEIGHT))
        if oy + room_h < SCREEN_HEIGHT:
            self.screen.fill(BLACK, (0, oy + room_h, SCREEN_WIDTH, SCREEN_HEIGHT - oy - room_h))

    def draw_hud(self, hud):
        hud.draw(self.screen)

    def draw_menu(self, menu):
        menu.draw(self.screen)

    def draw_pause(self, pause):
        pause.draw(self.screen)

    def draw_overlay_text(self, text_surface):
        self.screen.blit(text_surface, text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
