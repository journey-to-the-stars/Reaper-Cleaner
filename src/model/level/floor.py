from src.config.settings import ROOM_COLS, ROOM_ROWS, TILE_SIZE, NUM_FLOORS
from src.algorithms.generation import generate_floor_layout
from src.model.level.room import DoorPosition, OPPOSITE_DOOR


class Floor:
    def __init__(self, floor_number=1):
        self.floor_number = floor_number
        self.is_final = (floor_number == NUM_FLOORS)
        self.rooms = {}
        self.current_pos = (0, 0)
        self.visited_rooms = set()
        self._generate()

    def _generate(self):
        self.rooms = generate_floor_layout(self.floor_number)

    @property
    def current_room(self):
        return self.rooms.get(self.current_pos)

    def enter_room(self, door_pos):
        if door_pos not in self.current_room.doors:
            return False
        self.current_pos = self.current_room.doors[door_pos]
        self.visited_rooms.add(self.current_pos)
        return True

    def get_spawn_position(self, entered_from):
        cx = ROOM_COLS // 2 * TILE_SIZE + TILE_SIZE // 2
        cy = ROOM_ROWS // 2 * TILE_SIZE + TILE_SIZE // 2

        if entered_from == DoorPosition.NORTH:
            return (cx, 3 * TILE_SIZE)
        elif entered_from == DoorPosition.SOUTH:
            return (cx, (ROOM_ROWS - 4) * TILE_SIZE)
        elif entered_from == DoorPosition.WEST:
            return (3 * TILE_SIZE, cy)
        elif entered_from == DoorPosition.EAST:
            return ((ROOM_COLS - 4) * TILE_SIZE, cy)
        return (cx, cy)
