import pygame
from src.config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, RED, WHITE


class PauseScreen:
    def __init__(self):
        self.font = pygame.font.Font(None, 48)
        self.overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 180))
        self.resume_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, 250, 200, 60)
        self.restart_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, 340, 200, 60)
        self.menu_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, 430, 200, 60)

    def draw(self, screen):
        screen.blit(self.overlay, (0, 0))
        pygame.draw.rect(screen, RED, self.resume_button)
        pygame.draw.rect(screen, RED, self.restart_button)
        pygame.draw.rect(screen, RED, self.menu_button)

        resume_text = self.font.render("Продолжить", True, WHITE)
        restart_text = self.font.render("Начать заново", True, WHITE)
        menu_text = self.font.render("Выйти в меню", True, WHITE)
        screen.blit(resume_text, resume_text.get_rect(center=self.resume_button.center))
        screen.blit(restart_text, restart_text.get_rect(center=self.restart_button.center))
        screen.blit(menu_text, menu_text.get_rect(center=self.menu_button.center))

    def handle_click(self, pos):
        if self.resume_button.collidepoint(pos):
            return "resume"
        if self.restart_button.collidepoint(pos):
            return "restart"
        if self.menu_button.collidepoint(pos):
            return "menu"
        return None
