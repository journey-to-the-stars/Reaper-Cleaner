import pygame
from src.config.settings import RED, WHITE


class Cursor:
    def __init__(self):
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        center = (12, 12)
        pygame.draw.circle(self.image, RED, center, 10, 2)
        pygame.draw.line(self.image, WHITE, (12, 2), (12, 22), 2)
        pygame.draw.line(self.image, WHITE, (2, 12), (22, 12), 2)

    def draw(self, screen):
        mx, my = pygame.mouse.get_pos()
        screen.blit(self.image, (mx - 12, my - 12))
