import unittest
from src.algorithms.generation import generate_floor_layout
from src.algorithms.astar import astar
from src.model.level.tile import TileType
from src.model.level.room import RoomType, OPPOSITE_DOOR
from src.config.settings import NUM_FLOORS


class TestAStar(unittest.TestCase):
    def test_finds_path(self):
        grid = [[TileType.FLOOR] * 5 for _ in range(5)]
        path = astar((0, 0), (4, 4), grid)
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (4, 4))


class TestFloorGeneration(unittest.TestCase):
    def test_door_consistency(self):
        rooms = generate_floor_layout(1)
        for pos, r in rooms.items():
            for door_pos, target in r.doors.items():
                self.assertIn(target, rooms)
                self.assertIn(OPPOSITE_DOOR[door_pos], rooms[target].doors)

    def test_start_not_directly_connected_to_exit(self):
        rooms = generate_floor_layout(1)
        start = rooms[(0, 0)]
        exit_rooms = [pos for pos, r in rooms.items() if r.room_type == RoomType.EXIT]
        if exit_rooms:
            exit_pos = exit_rooms[0]
            self.assertNotIn(exit_pos, list(start.doors.values()))

    def test_boss_on_final_floor(self):
        rooms = generate_floor_layout(NUM_FLOORS)
        bosses = [r for r in rooms.values() if r.room_type == RoomType.BOSS]
        self.assertEqual(len(bosses), 1)
        exits = [r for r in rooms.values() if r.room_type == RoomType.EXIT]
        self.assertEqual(len(exits), 0)
