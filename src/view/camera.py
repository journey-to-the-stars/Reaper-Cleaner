from src.config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, ROOM_COLS, ROOM_ROWS, TILE_SIZE


class Camera:
    def __init__(self):
        self.offset_x = (SCREEN_WIDTH - ROOM_COLS * TILE_SIZE) // 2
        self.offset_y = (SCREEN_HEIGHT - ROOM_ROWS * TILE_SIZE) // 2

    def apply(self, entity):
        if hasattr(entity, 'rect'):
            return entity.rect.move(self.offset_x, self.offset_y)
        return entity

    def apply_rect(self, rect):
        return rect.move(self.offset_x, self.offset_y)

    def world_to_screen(self, x, y):
        return (x + self.offset_x, y + self.offset_y)

    def screen_to_world(self, x, y):
        return (x - self.offset_x, y - self.offset_y)
