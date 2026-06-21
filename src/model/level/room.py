from enum import Enum, auto
import random
import pygame
from src.config.settings import (
    ROOM_COLS, ROOM_ROWS, ROOM_DOOR_WIDTH, TILE_SIZE,
    MIN_ENEMIES_PER_ROOM, MAX_ENEMIES_PER_ROOM,
)
from src.model.level.tile import TileType


class RoomType(Enum):
    START = auto()
    COMBAT = auto()
    TREASURE = auto()
    EXIT = auto()
    BOSS = auto()
    CHALLENGE = auto()


class DoorPosition(Enum):
    NORTH = auto()
    SOUTH = auto()
    EAST = auto()
    WEST = auto()


OPPOSITE_DOOR = {
    DoorPosition.NORTH: DoorPosition.SOUTH,
    DoorPosition.SOUTH: DoorPosition.NORTH,
    DoorPosition.EAST: DoorPosition.WEST,
    DoorPosition.WEST: DoorPosition.EAST,
}

class Room:
    def __init__(self, grid_x, grid_y, room_width=None, room_height=None):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.room_type = RoomType.COMBAT
        self.cleared = False
        self.doors = {}
        self.room_width = room_width if room_width is not None else ROOM_COLS
        self.room_height = room_height if room_height is not None else ROOM_ROWS
        self.tiles = self._build_tiles()
        self.enemy_spawns = []
        self.spawned_enemies = []
        self.spawned_pickups = []
        self.waves = []
        self.current_wave = 0

    def _build_tiles(self):
        w, h = self.room_width, self.room_height
        tiles = [[TileType.WALL] * w for _ in range(h)]

        for y in range(1, h - 1):
            for x in range(1, w - 1):
                tiles[y][x] = TileType.FLOOR

        half = ROOM_DOOR_WIDTH // 2
        cx = w // 2
        cy = h // 2

        for door_pos in self.doors:
            if door_pos == DoorPosition.NORTH:
                for dx in range(cx - half, cx + half + 1):
                    tiles[0][dx] = TileType.DOOR
            elif door_pos == DoorPosition.SOUTH:
                for dx in range(cx - half, cx + half + 1):
                    tiles[h - 1][dx] = TileType.DOOR
            elif door_pos == DoorPosition.EAST:
                for dy in range(cy - half, cy + half + 1):
                    tiles[dy][w - 1] = TileType.DOOR
            elif door_pos == DoorPosition.WEST:
                for dy in range(cy - half, cy + half + 1):
                    tiles[dy][0] = TileType.DOOR

        return tiles

    def _door_zones(self):
        zones = set()
        w, h = self.room_width, self.room_height
        cx, cy = w // 2, h // 2
        hw = ROOM_DOOR_WIDTH // 2 + 3
        for door_pos in self.doors:
            if door_pos == DoorPosition.NORTH:
                for dx in range(cx - hw, cx + hw + 1):
                    for dy in range(0, 8):
                        zones.add((dx, dy))
            elif door_pos == DoorPosition.SOUTH:
                for dx in range(cx - hw, cx + hw + 1):
                    for dy in range(h - 8, h):
                        zones.add((dx, dy))
            elif door_pos == DoorPosition.EAST:
                for dy in range(cy - hw, cy + hw + 1):
                    for dx in range(w - 8, w):
                        zones.add((dx, dy))
            elif door_pos == DoorPosition.WEST:
                for dy in range(cy - hw, cy + hw + 1):
                    for dx in range(0, 8):
                        zones.add((dx, dy))
        return zones

    def generate_enemy_spawns(self):
        if self.room_type not in (RoomType.COMBAT, RoomType.BOSS, RoomType.EXIT, RoomType.CHALLENGE):
            return

        zones = self._door_zones()
        quadrants = [[], [], [], []]
        w, h = self.room_width, self.room_height
        mid_x, mid_y = w // 2, h // 2

        for y in range(7, h - 7):
            for x in range(7, w - 7):
                if (x, y) in zones:
                    continue
                tx = x * TILE_SIZE + TILE_SIZE // 2
                ty = y * TILE_SIZE + TILE_SIZE // 2
                q = (0 if x < mid_x else 1) + (0 if y < mid_y else 2)
                quadrants[q].append((tx, ty))

        num = random.randint(MIN_ENEMIES_PER_ROOM, MAX_ENEMIES_PER_ROOM)
        per_quad = max(1, num // 4)
        taken = 0

        for q in quadrants:
            random.shuffle(q)
            for i in range(min(per_quad, len(q))):
                self.enemy_spawns.append(q[i])
                taken += 1

        extras = []
        for q in quadrants:
            for pos in q[per_quad:]:
                extras.append(pos)

        random.shuffle(extras)
        while taken < num and extras:
            self.enemy_spawns.append(extras.pop())
            taken += 1

    def get_door_rect(self, door_pos):
        half = ROOM_DOOR_WIDTH // 2
        w, h = self.room_width, self.room_height
        cx = w // 2
        cy = h // 2

        if door_pos == DoorPosition.NORTH:
            x = (cx - half) * TILE_SIZE
            y = 0
            dw = ROOM_DOOR_WIDTH * TILE_SIZE
            dh = TILE_SIZE
        elif door_pos == DoorPosition.SOUTH:
            x = (cx - half) * TILE_SIZE
            y = (h - 1) * TILE_SIZE
            dw = ROOM_DOOR_WIDTH * TILE_SIZE
            dh = TILE_SIZE
        elif door_pos == DoorPosition.EAST:
            x = (w - 1) * TILE_SIZE
            y = (cy - half) * TILE_SIZE
            dw = TILE_SIZE
            dh = ROOM_DOOR_WIDTH * TILE_SIZE
        elif door_pos == DoorPosition.WEST:
            x = 0
            y = (cy - half) * TILE_SIZE
            dw = TILE_SIZE
            dh = ROOM_DOOR_WIDTH * TILE_SIZE
        else:
            return None

        return pygame.Rect(x, y, dw, dh)

    def get_wall_rects(self):
        rects = []
        for y in range(self.room_height):
            for x in range(self.room_width):
                if self.tiles[y][x] in (TileType.WALL, TileType.VOID):
                    rects.append(pygame.Rect(
                        x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE,
                    ))
        return rects

    def tiles_to_grid(self):
        return [[self.tiles[y][x] for x in range(self.room_width)] for y in range(self.room_height)]

    @property
    def center(self):
        cx = self.room_width // 2 * TILE_SIZE + TILE_SIZE // 2
        cy = self.room_height // 2 * TILE_SIZE + TILE_SIZE // 2
        return (cx, cy)
