import random
from src.config.settings import MIN_ROOMS, MAX_ROOMS, TILE_SIZE, EXIT_ENEMY_MULTIPLIER, NUM_FLOORS
from src.model.level.room import (
    Room, RoomType, DoorPosition, OPPOSITE_DOOR,
)
from src.model.enemy import WormEnemy, BossHeart

_DIRECTIONS = [
    (0, -1, DoorPosition.NORTH, DoorPosition.SOUTH),
    (0, 1, DoorPosition.SOUTH, DoorPosition.NORTH),
    (-1, 0, DoorPosition.WEST, DoorPosition.EAST),
    (1, 0, DoorPosition.EAST, DoorPosition.WEST),
]


def generate_floor_layout(floor_number=1):
    target = random.randint(MIN_ROOMS, MAX_ROOMS)
    rooms = {}
    start = (0, 0)
    rooms[start] = Room(0, 0)

    queue = [start]
    expansion_order = [start]
    parent_of = {}

    while queue and len(rooms) < target:
        current = queue.pop(0)
        dirs = _DIRECTIONS[:]
        random.shuffle(dirs)
        r = random.random()
        if r < 0.55:
            max_place = 1
        elif r < 0.85:
            max_place = 2
        else:
            max_place = 3
        placed = 0

        for dx, dy, door_out, door_in in dirs:
            if placed >= max_place:
                break
            new_pos = (current[0] + dx, current[1] + dy)
            if new_pos in rooms:
                continue
            if len(rooms) >= target:
                break

            nx, ny = new_pos
            new_room = Room(new_pos[0], new_pos[1])
            new_room.doors[door_in] = current
            rooms[current].doors[door_out] = new_pos
            rooms[new_pos] = new_room
            parent_of[new_pos] = current
            expansion_order.append(new_pos)

            for ndx, ndy, ndoor_out, ndoor_in in _DIRECTIONS:
                adj = (nx + ndx, ny + ndy)
                if adj in rooms and adj != current:
                    if ndoor_out not in rooms[new_pos].doors:
                        rooms[new_pos].doors[ndoor_out] = adj
                        rooms[adj].doors[ndoor_in] = new_pos

            queue.append(new_pos)
            placed += 1

    is_final = (floor_number == NUM_FLOORS)
    main_path_end = expansion_order[-1]
    main_path = [main_path_end]
    while main_path[-1] in parent_of:
        main_path.append(parent_of[main_path[-1]])
    main_path = set(main_path)
    _assign_types(rooms, expansion_order, is_final, main_path)
    _ensure_start_connections(rooms)
    _add_cycles(rooms, max_cycles=random.randint(1, min(5, len(rooms))))
    _ensure_dead_ends(rooms, expansion_order, main_path)
    _strip_extra_doors(rooms)
    _rebuild_tiles(rooms)
    _populate_spawns(rooms, is_final, floor_number)

    return rooms


def _assign_types(rooms, expansion_order, is_final, main_path=None):
    if not expansion_order:
        return
    if main_path is None:
        main_path = set()

    rooms[expansion_order[0]].room_type = RoomType.START
    rooms[expansion_order[0]].cleared = True

    if len(expansion_order) > 1:
        last_pos = expansion_order[-1]
        rooms[last_pos].room_type = RoomType.BOSS if is_final else RoomType.EXIT

    has_challenge = False
    for pos in expansion_order[1:-1]:
        room = rooms[pos]
        if len(room.doors) == 1 and pos not in main_path and not has_challenge:
            room.room_type = RoomType.CHALLENGE
            has_challenge = True
        else:
            room.room_type = RoomType.COMBAT

    if not has_challenge:
        candidates = [pos for pos, r in rooms.items() if r.room_type == RoomType.COMBAT and pos not in main_path]
        if not candidates:
            candidates = [pos for pos, r in rooms.items() if r.room_type == RoomType.COMBAT]
        if candidates:
            pos = random.choice(candidates)
            rooms[pos].room_type = RoomType.CHALLENGE


def _add_cycles(rooms, max_cycles=2):
    candidates = []

    for pos, r in rooms.items():
        if r.room_type != RoomType.COMBAT:
            continue
        x, y = pos
        for dx, dy, door_out, door_in in _DIRECTIONS:
            neighbor = (x + dx, y + dy)
            if neighbor in rooms and rooms[neighbor].room_type == RoomType.COMBAT:
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

    for door_pos, target in list(rooms[start].doors.items()):
        if target in rooms and rooms[target].room_type in (RoomType.EXIT, RoomType.BOSS):
            del rooms[start].doors[door_pos]
            rooms[target].doors.pop(OPPOSITE_DOOR[door_pos], None)
    for dx, dy, door_out, door_in in _DIRECTIONS:
        npos = (start[0] + dx, start[1] + dy)
        if npos in rooms and door_out not in rooms[start].doors:
            if rooms[npos].room_type in (RoomType.EXIT, RoomType.BOSS):
                continue
            rooms[start].doors[door_out] = npos
            rooms[npos].doors[door_in] = start


def _ensure_dead_ends(rooms, expansion_order, main_path=None):
    if main_path is None:
        main_path = set()
    last_pos = expansion_order[-1]
    for pos, r in rooms.items():
        if pos == expansion_order[0] or pos == last_pos:
            continue
        if len(r.doors) <= 1 and pos not in main_path:
            return

    candidates = []
    for pos, r in rooms.items():
        if pos == expansion_order[0] or pos == last_pos:
            continue
        if pos in main_path:
            continue
        if r.room_type != RoomType.COMBAT:
            continue
        if len(r.doors) < 3:
            continue
        for door_pos, target in list(r.doors.items()):
            if target in rooms and len(rooms[target].doors) > 1:
                candidates.append((pos, door_pos, target))

    random.shuffle(candidates)
    for pos, door_pos, target in candidates:
        del rooms[pos].doors[door_pos]
        del rooms[target].doors[OPPOSITE_DOOR[door_pos]]
        return


def _strip_extra_doors(rooms):
    for pos, room in rooms.items():
        if room.room_type in (RoomType.EXIT, RoomType.BOSS, RoomType.CHALLENGE):
            if len(room.doors) > 1:
                keep = next(iter(room.doors))
                for door_pos, target in list(room.doors.items()):
                    if door_pos == keep:
                        continue
                    del room.doors[door_pos]
                    rooms[target].doors.pop(OPPOSITE_DOOR[door_pos], None)


def _rebuild_tiles(rooms):
    for room in rooms.values():
        room.tiles = room._build_tiles()


def _offset_spawns(spawns, extra):
    for _ in range(extra):
        if spawns:
            wx, wy, sc = random.choice(spawns)
            spawns.append((wx + random.randint(-4, 4), wy + random.randint(-4, 4), sc))
    return spawns


def _populate_spawns(rooms, is_final, floor_number=1):
    extra = floor_number - 1
    for pos, room in rooms.items():
        if room.room_type == RoomType.BOSS:
            room.room_width = 39
            room.room_height = 24
            room.tiles = room._build_tiles()
            cx = room.room_width // 2 * TILE_SIZE + TILE_SIZE // 2
            cy = room.room_height // 2 * TILE_SIZE + TILE_SIZE // 2
            room.enemy_spawns = [(cx, cy, BossHeart)]
        elif room.room_type == RoomType.COMBAT:
            room.generate_enemy_spawns()
            spawns = [(wx, wy, WormEnemy) for (wx, wy) in room.enemy_spawns]
            room.enemy_spawns = _offset_spawns(spawns, extra)
        elif room.room_type == RoomType.EXIT:
            room.generate_enemy_spawns()
            spawns = [(wx, wy, WormEnemy) for (wx, wy) in room.enemy_spawns]
            count = int(EXIT_ENEMY_MULTIPLIER) + (1 if random.random() < EXIT_ENEMY_MULTIPLIER % 1 else 0)
            spawns = spawns * count
            room.enemy_spawns = _offset_spawns(spawns, extra)
        elif room.room_type == RoomType.CHALLENGE:
            room.generate_enemy_spawns()
            if not room.enemy_spawns:
                cx = room.room_width // 2 * TILE_SIZE + TILE_SIZE // 2
                cy = room.room_height // 2 * TILE_SIZE + TILE_SIZE // 2
                room.enemy_spawns = [(cx - 16, cy, WormEnemy), (cx + 16, cy, WormEnemy)]
            elif len(room.enemy_spawns[0]) == 2:
                room.enemy_spawns = [(wx, wy, WormEnemy) for (wx, wy) in room.enemy_spawns]
            base = [(wx, wy, sc) for (wx, wy, sc) in room.enemy_spawns]
            room.waves = []
            for w in range(3):
                wave = base * (w + 1)
                random.shuffle(wave)
                room.waves.append(wave)
