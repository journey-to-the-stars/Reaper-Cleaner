import pygame
import math
from src.config.settings import GRIMOIR_PROJECTILE_SPEED, GRIMOIR_HOMING_SPEED, BOSS_PROJECTILE_SPEED, BOSS_PROJECTILE_DAMAGE
from src.config.assets import SPRITES
from src.algorithms.knn import knn


class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, speed, damage, homing=False, color=(255, 100, 100)):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.math.Vector2(x, y)
        self.angle = angle
        self.speed = speed
        self.damage = damage
        self.homing = homing
        self.homing_speed = GRIMOIR_HOMING_SPEED
        self.homing_timer = 999 if homing else 0.0
        self.lifetime = 3.0
        self.target = None

    def update(self, dt, enemies):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
            return

        if self.homing and enemies and self.homing_timer > 0:
            self.homing_timer -= dt
            if not self.target or not self.target.alive:
                nearest = knn(self.pos, enemies, 1)
                self.target = nearest[0] if nearest else None

            if self.target and self.target.alive:
                diff = pygame.math.Vector2(self.target.rect.center) - self.pos
                if diff.length_squared() < 1:
                    return
                desired = diff.normalize()
                current = pygame.math.Vector2(math.cos(self.angle), math.sin(self.angle))
                dot = current.dot(desired)
                dot = max(-1, min(1, dot))
                angle_diff = math.degrees(math.acos(dot))
                cross = current.x * desired.y - current.y * desired.x
                max_turn = self.homing_speed * dt
                turn = min(angle_diff, max_turn)
                if cross < 0:
                    self.angle -= math.radians(turn)
                else:
                    self.angle += math.radians(turn)

        self.pos.x += math.cos(self.angle) * self.speed * dt
        self.pos.y += math.sin(self.angle) * self.speed * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))


class GrimoirFlame(Projectile):
    def __init__(self, x, y, angle):
        super().__init__(x, y, angle, GRIMOIR_PROJECTILE_SPEED, 20, homing=True, color=(255, 50, 50))
        spr = SPRITES.get("balefire(grimoire_projectile)")
        if spr:
            self.image = pygame.transform.scale(spr, (16, 16))
            self.rect = self.image.get_rect(center=(int(x), int(y)))


class BloodClot(Projectile):
    def __init__(self, x, y, angle):
        super().__init__(x, y, angle, BOSS_PROJECTILE_SPEED, 12, homing=False, color=(120, 0, 0))


class BossProjectile(Projectile):
    def __init__(self, x, y, angle, speed, damage):
        super().__init__(x, y, angle, speed, damage, homing=False)
        spr = SPRITES.get("boss_projectile_lust")
        self.image = pygame.transform.scale(spr, (16, 16)) if spr else pygame.Surface((16, 16))
        if not spr:
            self.image.fill((220, 40, 220))
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        self.lifetime = 4.0
