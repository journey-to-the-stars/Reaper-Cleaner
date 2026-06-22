import math
from src.model.level.tile import TileType


def get_f(entry):
    return entry[0]


def astar(start, goal, grid):
    if not grid:
        return []
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    if not (0 <= start[0] < cols and 0 <= start[1] < rows
            and 0 <= goal[0] < cols and 0 <= goal[1] < rows):
        return []
    if grid[goal[1]][goal[0]] == TileType.WALL:
        return []

    counter = 0
    open_set = [(0, counter, start)]
    came_from = {}
    g_score = {start: 0}
    closed_set = set()

    while open_set:
        open_set.sort(key=get_f)
        _, _, current = open_set.pop(0)

        if current in closed_set:
            continue
        if current == goal:
            return _smooth_path(_reconstruct_path(came_from, current), grid)

        closed_set.add(current)

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0),
                       (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            neighbor = (current[0] + dx, current[1] + dy)
            if not (0 <= neighbor[0] < cols and 0 <= neighbor[1] < rows):
                continue
            if neighbor in closed_set:
                continue
            if grid[neighbor[1]][neighbor[0]] == TileType.WALL:
                continue
            if dx != 0 and dy != 0:
                if grid[current[1] + dy][current[0]] == TileType.WALL and grid[current[1]][current[0] + dx] == TileType.WALL:
                    continue

            if dx != 0 and dy != 0:
                step_cost = 1.414
            else:
                step_cost = 1.0

            tentative_g = g_score[current] + step_cost
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + _heuristic(neighbor, goal)
                counter += 1
                open_set.append((f, counter, neighbor))

    return []


def _heuristic(a, b):
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return dx + dy + (1.414 - 2) * min(dx, dy)


def _reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def _smooth_path(path, grid):
    if len(path) <= 3:
        return path

    smoothed = [path[0]]
    i = 0
    while i < len(path) - 1:
        max_j = min(i + 3, len(path) - 1)
        j = max_j
        while j > i + 1:
            if _has_line_of_sight(path[i], path[j], grid):
                break
            j -= 1
        i = j
        smoothed.append(path[i])

    return smoothed


def _has_line_of_sight(a, b, grid):
    x0, y0 = a
    x1, y1 = b
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy

    while True:
        if not (0 <= x0 < len(grid[0]) and 0 <= y0 < len(grid)):
            return False
        if grid[y0][x0] == TileType.WALL:
            return False
        if x0 == x1 and y0 == y1:
            return True
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
