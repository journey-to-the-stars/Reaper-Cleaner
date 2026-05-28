from enum import Enum, auto
import pygame


class PickupType(Enum):
    HEALTH = auto()
    GRIMOIRE_UPGRADE = auto()


class Pickup(pygame.sprite.Sprite):
    def __init__(self, x, y, ptype):
        super().__init__()
        self.ptype = ptype
        self.image = pygame.Surface((16, 16))
        if ptype == PickupType.HEALTH:
            self.image.fill((200, 40, 40))
        else:
            self.image.fill((40, 100, 220))
        self.rect = self.image.get_rect(center=(x, y))
