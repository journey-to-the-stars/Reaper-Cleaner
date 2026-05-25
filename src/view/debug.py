import pygame
from src.config.settings import TILE_SIZE, ROOM_COLS, ROOM_ROWS, GREEN, BLUE, YELLOW, CYAN, RED
from src.model.level.room import RoomType


class DebugOverlay:
    def __init__(self):
        self.visible = False
        self.font = pygame.font.Font(None, 20)

    def draw(self, screen, camera, floor=None, enemies=None):
        if not self.visible:
            return

        ox, oy = camera.offset_x, camera.offset_y
        room = floor.current_room if floor else None

        if room:
            pygame.draw.rect(
                screen, GREEN,
                (ox, oy, ROOM_COLS * TILE_SIZE, ROOM_ROWS * TILE_SIZE), 2,
            )

            y = oy + 4
            for door_pos in room.doors:
                door_rect = room.get_door_rect(door_pos)
                if door_rect:
                    sr = door_rect.move(ox, oy)
                    pygame.draw.rect(screen, CYAN, sr, 2)

            label = self.font.render(
                f"({room.grid_x},{room.grid_y}) {room.room_type.name} cleared={room.cleared}",
                True, YELLOW,
            )
            screen.blit(label, (ox + 4, oy + 4))

        if floor:
            mini_x = 10
            mini_y = 10
            mini_size = 14
            gap = 2

            for (gx, gy), r in floor.rooms.items():
                color = (80, 80, 80)
                if r.room_type == RoomType.START:
                    color = GREEN
                elif r.room_type == RoomType.COMBAT:
                    color = (150, 50, 50)
                elif r.room_type == RoomType.BOSS:
                    color = RED
                elif r.room_type == RoomType.TREASURE:
                    color = YELLOW

                if (gx, gy) == floor.current_pos:
                    pygame.draw.rect(screen, (255, 255, 255),
                                     (mini_x + gx * (mini_size + gap) - 1,
                                      mini_y + gy * (mini_size + gap) - 1,
                                      mini_size + 2, mini_size + 2), 2)

                pygame.draw.rect(screen, color,
                                 (mini_x + gx * (mini_size + gap),
                                  mini_y + gy * (mini_size + gap),
                                  mini_size, mini_size))

        if enemies:
            for enemy in enemies:
                if hasattr(enemy, 'path') and enemy.path:
                    for point in enemy.path:
                        px = point[0] * TILE_SIZE + TILE_SIZE // 2 + ox
                        py = point[1] * TILE_SIZE + TILE_SIZE // 2 + oy
                        pygame.draw.circle(screen, BLUE, (px, py), 3)
