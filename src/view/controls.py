import pygame
from src.config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, DARK_GRAY


class ControlsScreen:
    def __init__(self):
        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 52)
        self.lines = [
            "WASD — передвижение",
            "ЛКМ — атака косой",
            "ПКМ (зажать) — зарядка гримуара",
            "ESC — пауза",
            "F1 — отладка",
        ]

    def draw(self, screen):
        screen.fill(DARK_GRAY)
        title = self.title_font.render("Управление", True, WHITE)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 120)))
        y = 220
        for line in self.lines:
            surf = self.font.render(line, True, WHITE)
            screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, y))
            y += 50
        hint = self.font.render("ЛКМ — назад", True, WHITE)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)))
