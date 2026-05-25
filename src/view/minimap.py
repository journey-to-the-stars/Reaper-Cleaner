import pygame
from src.config.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from src.model.level.room import RoomType


class Minimap:
    def __init__(self):
        self.cell_size = 14
        self.gap = 2
        self.margin = 10

    def draw(self, screen, floor):
        if not floor or not floor.rooms:
            return

        min_x = min(p[0] for p in floor.rooms)
        max_x = max(p[0] for p in floor.rooms)
        min_y = min(p[1] for p in floor.rooms)
        max_y = max(p[1] for p in floor.rooms)

        cols = max_x - min_x + 1
        rows = max_y - min_y + 1
        cs = self.cell_size
        gap = self.gap

        map_w = cols * (cs + gap) - gap + self.margin * 2
        map_h = rows * (cs + gap) - gap + self.margin * 2

        surf = pygame.Surface((map_w, map_h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 160))

        for (gx, gy), room in floor.rooms.items():
            if (gx, gy) not in floor.visited_rooms:
                continue

            color = (80, 80, 80)
            if room.room_type == RoomType.START:
                color = (80, 200, 80)
            elif room.room_type == RoomType.COMBAT:
                color = (180, 60, 60)
            elif room.room_type == RoomType.BOSS:
                color = (220, 40, 40)
            elif room.room_type == RoomType.TREASURE:
                color = (200, 180, 40)
            elif room.room_type == RoomType.EXIT:
                color = (60, 140, 220)

            rx = self.margin + (gx - min_x) * (cs + gap)
            ry = self.margin + (gy - min_y) * (cs + gap)

            if (gx, gy) == floor.current_pos:
                pygame.draw.rect(surf, (255, 255, 255),
                                 (rx - 1, ry - 1, cs + 2, cs + 2), 2)

            pygame.draw.rect(surf, color, (rx, ry, cs, cs))

        screen.blit(surf, (SCREEN_WIDTH - map_w - 10, 10))
