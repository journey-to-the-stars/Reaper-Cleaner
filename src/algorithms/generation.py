import random
from src.config.settings import MIN_ROOMS, MAX_ROOMS, ROOM_COLS, ROOM_ROWS, TILE_SIZE, EXIT_ENEMY_MULTIPLIER, NUM_FLOORS
from src.model.level.room import (
    Room, RoomType, DoorPosition, OPPOSITE_DOOR,
)
from src.model.enemy import WormEnemy, BossHeart


def generate_floor_layout(floor_number=1):
    target = random.randint(MIN_ROOMS, MAX_ROOMS)
    rooms = {}
    start = (0, 0)
    rooms[start] = Room(0, 0)

    directions = [
        (0, -1, DoorPosition.NORTH, DoorPosition.SOUTH),
        (0, 1, DoorPosition.SOUTH, DoorPosition.NORTH),
        (-1, 0, DoorPosition.WEST, DoorPosition.EAST),
        (1, 0, DoorPosition.EAST, DoorPosition.WEST),
    ]

    stack = [start]
    visited = {start}
    expansion_order = [start]

    while stack and len(rooms) < target:
        current = stack[-1]
        random.shuffle(directions)
        expanded = False

        for dx, dy, door_out, door_in in directions:
            new_pos = (current[0] + dx, current[1] + dy)
            if new_pos not in visited:
                visited.add(new_pos)
                new_room = Room(new_pos[0], new_pos[1])
                new_room.doors[door_in] = current
                rooms[current].doors[door_out] = new_pos
                rooms[new_pos] = new_room
                expansion_order.append(new_pos)
                stack.append(new_pos)
                expanded = True
                break

        if not expanded:
            stack.pop()

    is_final = (floor_number == NUM_FLOORS)
    _assign_types(rooms, expansion_order, is_final)
    _add_cycles(rooms, max_cycles=random.randint(1, min(5, len(rooms))))
    _ensure_start_connections(rooms)
    _ensure_dead_ends(rooms, expansion_order, is_final)
    _rebuild_tiles(rooms)
    _populate_spawns(rooms, is_final)

    return rooms


def _assign_types(rooms, expansion_order, is_final):
    if not expansion_order:
        return

    rooms[expansion_order[0]].room_type = RoomType.START
    rooms[expansion_order[0]].cleared = True

    if len(expansion_order) > 1:
        last_pos = expansion_order[-1]
        rooms[last_pos].room_type = RoomType.BOSS if is_final else RoomType.EXIT

    has_challenge = False
    for pos in expansion_order[1:-1]:
        room = rooms[pos]
        if not has_challenge and len(room.doors) <= 2 and random.random() < 0.25:
            room.room_type = RoomType.CHALLENGE
            has_challenge = True
        elif len(room.doors) == 1 and not has_challenge and random.random() < 0.3:
            room.room_type = RoomType.TREASURE
        elif len(room.doors) == 1 and random.random() < 0.3:
            room.room_type = RoomType.TREASURE
        else:
            room.room_type = RoomType.COMBAT


def _add_cycles(rooms, max_cycles=2):
    all_positions = list(rooms.keys())
    candidates = []

    for pos in all_positions:
        x, y = pos
        for dx, dy, door_out, door_in in [
            (0, -1, DoorPosition.NORTH, DoorPosition.SOUTH),
            (0, 1, DoorPosition.SOUTH, DoorPosition.NORTH),
            (-1, 0, DoorPosition.WEST, DoorPosition.EAST),
            (1, 0, DoorPosition.EAST, DoorPosition.WEST),
        ]:
            neighbor = (x + dx, y + dy)
            if neighbor in rooms:
                if door_out not in rooms[pos].doors:
                    candidates.append((pos, neighbor, door_out, door_in))

    random.shuffle(candidates)
    cycles_added = 0

    for pos, neighbor, door_out, door_in in candidates:
        if cycles_added >= max_cycles:
            break
        rooms[pos].doors[door_out] = neighbor
        rooms[neighbor].doors[door_in] = pos
        cycles_added += 1


def _ensure_start_connections(rooms, start=(0, 0)):
    if start not in rooms:
        return
    for dx, dy, door_out, door_in in [
        (0, -1, DoorPosition.NORTH, DoorPosition.SOUTH),
        (0, 1, DoorPosition.SOUTH, DoorPosition.NORTH),
        (-1, 0, DoorPosition.WEST, DoorPosition.EAST),
        (1, 0, DoorPosition.EAST, DoorPosition.WEST),
    ]:
        npos = (start[0] + dx, start[1] + dy)
        if npos in rooms and door_out not in rooms[start].doors:
            rooms[start].doors[door_out] = npos
            rooms[npos].doors[door_in] = start


def _ensure_dead_ends(rooms, expansion_order, is_final):
    for pos in expansion_order:
        if pos == expansion_order[0]:
            continue
        if is_final and pos == expansion_order[-1]:
            continue
        if not is_final and pos == expansion_order[-1]:
            continue
        room = rooms[pos]
        if len(room.doors) <= 1:
            return

    for pos in reversed(expansion_order[1:-1]):
        room = rooms[pos]
        if len(room.doors) <= 2:
            continue
        removable = []
        for door_pos, target in list(room.doors.items()):
            if target in rooms and rooms[target].doors.get(OPPOSITE_DOOR[door_pos]) == pos:
                removable.append((door_pos, target))
        for door_pos, target in removable:
            if target in rooms and len(rooms[target].doors) > 1 and rooms[target].room_type != RoomType.EXIT:
                del rooms[target].doors[OPPOSITE_DOOR[door_pos]]
                del rooms[pos].doors[door_pos]
                break
        break


def _rebuild_tiles(rooms):
    for room in rooms.values():
        room.tiles = room._build_tiles()


def _populate_spawns(rooms, is_final):
    for pos, room in rooms.items():
        if room.room_type == RoomType.BOSS:
            cx = ROOM_COLS // 2 * TILE_SIZE + TILE_SIZE // 2
            cy = ROOM_ROWS // 2 * TILE_SIZE + TILE_SIZE // 2
            room.enemy_spawns = [(cx, cy, BossHeart)]
        elif room.room_type == RoomType.COMBAT:
            room.generate_enemy_spawns()
            room.enemy_spawns = [
                (wx, wy, WormEnemy) for (wx, wy) in room.enemy_spawns
            ]
        elif room.room_type == RoomType.EXIT:
            room.generate_enemy_spawns()
            spawns = [(wx, wy, WormEnemy) for (wx, wy) in room.enemy_spawns]
            count = int(EXIT_ENEMY_MULTIPLIER) + (1 if random.random() < EXIT_ENEMY_MULTIPLIER % 1 else 0)
            room.enemy_spawns = spawns * count
        elif room.room_type == RoomType.CHALLENGE:
            room.generate_enemy_spawns()
            base = [(wx, wy, WormEnemy) for (wx, wy) in room.enemy_spawns]
            room.waves = []
            for w in range(3):
                extra = w
                wave = base * (w + 1)
                random.shuffle(wave)
                room.waves.append(wave)
