import pygame
from src.config.settings import (
    HP_BAR_WIDTH, HP_BAR_HEIGHT, GRIMOIR_CHARGE_TIME, DARK_GRAY, RED, WHITE,
    GRIMOIR_INDICATOR_SIZE, PURPLE, GOLD, PLAYER_HP,
)


class HUD:
    def __init__(self, player):
        self.player = player
        self.font = pygame.font.Font(None, 24)

    def draw(self, screen):
        self._draw_hp_bar(screen)
        self._draw_grimoir_indicator(screen)

    def _draw_hp_bar(self, screen):
        bar_x = 20
        bar_y = 20
        scale = self.player.max_hp / PLAYER_HP
        bar_w = int(HP_BAR_WIDTH * scale)
        pygame.draw.rect(screen, DARK_GRAY, (bar_x, bar_y, bar_w, HP_BAR_HEIGHT))
        if self.player.hp > 0:
            fill_width = int((self.player.hp / self.player.max_hp) * bar_w)
            pygame.draw.rect(screen, RED, (bar_x, bar_y, fill_width, HP_BAR_HEIGHT))

    def _draw_grimoir_indicator(self, screen):
        x = 20
        y = 50
        charge_ratio = min(self.player.grimoir_charge / GRIMOIR_CHARGE_TIME, 1.0)

        pygame.draw.rect(screen, DARK_GRAY, (x, y, GRIMOIR_INDICATOR_SIZE, GRIMOIR_INDICATOR_SIZE))
        if self.player.grimoir_charging:
            fill_height = int(charge_ratio * GRIMOIR_INDICATOR_SIZE)
            color = PURPLE if charge_ratio < 1.0 else GOLD
            pygame.draw.rect(
                screen, color,
                (x, y + GRIMOIR_INDICATOR_SIZE - fill_height, GRIMOIR_INDICATOR_SIZE, fill_height),
            )

        label = self.font.render("G", True, WHITE)
        screen.blit(label, (x + 8, y + 6))
