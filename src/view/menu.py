import pygame
from src.config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, RED, WHITE


class Menu:
    def __init__(self):
        self.title_font = pygame.font.Font(None, 72)
        self.button_font = pygame.font.Font(None, 40)
        self.title_text = self.title_font.render("Reaper-Cleaner", True, RED)
        cx = SCREEN_WIDTH // 2
        self.play_button = pygame.Rect(cx - 100, 300, 200, 50)
        self.controls_button = pygame.Rect(cx - 100, 370, 200, 50)
        self.quit_button = pygame.Rect(cx - 100, 440, 200, 50)

    def draw(self, screen):
        screen.fill(BLACK)
        screen.blit(self.title_text, self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 150)))
        buttons = [("Играть", self.play_button), ("Управление", self.controls_button), ("Выход", self.quit_button)]
        for text, rect in buttons:
            pygame.draw.rect(screen, RED, rect)
            surf = self.button_font.render(text, True, WHITE)
            screen.blit(surf, surf.get_rect(center=rect.center))

    def handle_click(self, pos):
        if self.play_button.collidepoint(pos):
            return "play"
        if self.controls_button.collidepoint(pos):
            return "controls"
        if self.quit_button.collidepoint(pos):
            return "quit"
        return None
