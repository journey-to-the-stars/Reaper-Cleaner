import pygame
from src.config.settings import (
    PLAYER_SPEED, PLAYER_HP, PLAYER_SIZE,
    SCYTHE_COOLDOWN, SCYTHE_DURATION, SCYTHE_RANGE, SCYTHE_DAMAGE, SCYTHE_ARC,
    GRIMOIR_CHARGE_TIME, GRIMOIR_COOLDOWN, GRIMOIR_PROJECTILES,
)
from src.config.assets import SPRITES


def _scale_sprite(name):
    surf = SPRITES.get(name)
    if surf is None:
        s = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
        s.fill((200, 200, 200))
        return s
    return pygame.transform.scale(surf, (PLAYER_SIZE, PLAYER_SIZE))


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.sprites = {
            "back": _scale_sprite("reaper_from_behind"),
            "front": _scale_sprite("reaper_with_grimoire(prob)"),
            "stock": _scale_sprite("stock_reaper"),
        }
        self._facing = "back"
        self.image = self.sprites["back"].copy()
        self.rect = self.image.get_rect(center=(x, y))

        self.hp = PLAYER_HP
        self.max_hp = PLAYER_HP
        self.speed = PLAYER_SPEED
        self.velocity = pygame.math.Vector2(0, 0)
        self.angle = 0.0

        self.scythe_cooldown = 0.0
        self.scythe_cooldown_duration = SCYTHE_COOLDOWN
        self.scythe_active = False
        self.scythe_timer = 0.0
        self.scythe_angle = 0.0
        self.scythe_start_angle = 0.0

        self.grimoir_charge = 0.0
        self.grimoir_charging = False
        self.grimoir_cooldown = 0.0
        self.grimoir_just_fired = False
        self.grimoir_charge_time = GRIMOIR_CHARGE_TIME
        self.grimoir_projectiles = GRIMOIR_PROJECTILES
        self.scythe_damage = SCYTHE_DAMAGE
        self.scythe_range = SCYTHE_RANGE
        self.scythe_half = 50
        self.scythe_scale = 1.0
        self.hit_enemies = set()

        self.i_frames = 0.0
        self.i_frame_duration = 0.5

    def update(self, dt, input_handler, walls):
        dx, dy = input_handler.get_movement()
        self._handle_movement(dt, dx, dy, walls)
        self._update_sprite(dx, dy)
        self._handle_weapons(dt, input_handler)

        if self.i_frames > 0:
            self.i_frames -= dt

    def _update_sprite(self, dx, dy):
        if dy < 0:
            self._facing = "back"
            self.image = self.sprites["back"].copy()
        elif dy > 0:
            self._facing = "front"
            self.image = self.sprites["front"].copy()
        elif dx < 0:
            self._facing = "left"
            self.image = pygame.transform.flip(self.sprites["stock"], True, False)
        elif dx > 0:
            self._facing = "right"
            self.image = self.sprites["stock"].copy()
        else:
            return

        self.rect = self.image.get_rect(center=self.rect.center)

    def _handle_movement(self, dt, dx, dy, walls):
        self.velocity = pygame.math.Vector2(dx, dy)
        if self.velocity.length() > 0:
            self.velocity.normalize_ip()
        self.velocity *= self.speed * dt

        self.rect.x += self.velocity.x
        self._collide(walls, 'x')
        self.rect.y += self.velocity.y
        self._collide(walls, 'y')

    def _collide(self, walls, axis):
        for wall in walls:
            if self.rect.colliderect(wall):
                if axis == 'x':
                    if self.velocity.x > 0:
                        self.rect.right = wall.left
                    elif self.velocity.x < 0:
                        self.rect.left = wall.right
                else:
                    if self.velocity.y > 0:
                        self.rect.bottom = wall.top
                    elif self.velocity.y < 0:
                        self.rect.top = wall.bottom

    def _handle_weapons(self, dt, input_handler):
        if self.scythe_cooldown > 0:
            self.scythe_cooldown -= dt
        if self.scythe_active:
            self.scythe_timer -= dt
            t = 1.0 - (self.scythe_timer / SCYTHE_DURATION)
            t = t * t * (3 - 2 * t)
            self.scythe_angle = self.scythe_start_angle + SCYTHE_ARC * t
            if self.scythe_timer <= 0:
                self.scythe_active = False

        if self.grimoir_cooldown > 0:
            self.grimoir_cooldown -= dt

        if input_handler.is_scythe_pressed() and self.scythe_cooldown <= 0 and not self.scythe_active:
            self.scythe_active = True
            self.scythe_timer = SCYTHE_DURATION
            self.scythe_cooldown = self.scythe_cooldown_duration
            self.scythe_start_angle = self.angle - SCYTHE_ARC / 2
            self.hit_enemies.clear()

        if input_handler.is_grimoir_held():
            if not self.grimoir_charging and self.grimoir_cooldown <= 0:
                self.grimoir_charging = True
                self.grimoir_charge = 0.0
            if self.grimoir_charging:
                self.grimoir_charge += dt
        else:
            if self.grimoir_charging:
                if self.grimoir_charge >= self.grimoir_charge_time:
                    self.grimoir_just_fired = True
                    self.grimoir_cooldown = GRIMOIR_COOLDOWN
                self.grimoir_charging = False
                self.grimoir_charge = 0.0

    def take_damage(self, amount):
        if self.i_frames > 0:
            return
        self.hp -= amount
        self.i_frames = self.i_frame_duration
        if self.hp < 0:
            self.hp = 0

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def is_scythe_hitting(self, target):
        if not self.scythe_active:
            return False
        if isinstance(target, pygame.Rect):
            points = [target.topleft, target.topright, target.bottomleft, target.bottomright, target.center]
        else:
            points = [target]

        hw, hh = self.scythe_half, self.scythe_half
        center = pygame.math.Vector2(self.rect.center)
        scythe_center = center + pygame.math.Vector2(1, 0).rotate(self.scythe_angle) * 40

        for pt in points:
            local = pygame.math.Vector2(pt) - scythe_center
            local.rotate_ip(self.scythe_angle)
            if -hw <= local.x <= hw and -hh <= local.y <= hh:
                return True
        return False

    @property
    def alive(self):
        return self.hp > 0

    @property
    def center(self):
        return pygame.math.Vector2(self.rect.center)
