from enum import IntEnum


class TileType(IntEnum):
    VOID = 0
    FLOOR = 1
    WALL = 2
    CORRIDOR = 3
    DOOR = 4
    SLIME = 5
