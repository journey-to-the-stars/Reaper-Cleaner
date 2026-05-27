import heapq
import math
from src.model.level.tile import TileType


def astar(start, goal, grid):
    if not grid:
        return []
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    if not (0 <= start[0] < cols and 0 <= start[1] < rows
            and 0 <= goal[0] < cols and 0 <= goal[1] < rows):
        return []

    open_set = []
    heapq.heappush(open_set, (0, 0, start))
    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, _, current = heapq.heappop(open_set)
        if current == goal:
            path = _reconstruct_path(came_from, current)
            return _smooth_path(path, grid)

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0),
                        (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            neighbor = (current[0] + dx, current[1] + dy)
            if not (0 <= neighbor[0] < cols and 0 <= neighbor[1] < rows):
                continue
            if grid[neighbor[1]][neighbor[0]] == TileType.WALL:
                continue

            step_cost = 1.414 if dx != 0 and dy != 0 else 1.0
            tentative_g = g_score[current] + step_cost
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + _heuristic(neighbor, goal)
                heapq.heappush(open_set, (f, tentative_g, neighbor))

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
    if len(path) <= 2:
        return path

    smoothed = [path[0]]
    i = 0
    while i < len(path) - 1:
        j = len(path) - 1
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
