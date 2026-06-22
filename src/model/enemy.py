import pygame, math, random
from src.config.settings import (
    ENEMY_DETECTION_RANGE, ENEMY_CHASE_SPEED_MULT,
    WORM_SPEED, WORM_HP, WORM_DAMAGE,
    BOSS_HP, BOSS_PROJECTILE_SPEED, BOSS_PROJECTILE_DAMAGE,
    BOSS_PHASE1_COOLDOWN, BOSS_PHASE2_COOLDOWN, BOSS_PHASE3_COOLDOWN, BOSS_PHASE4_COOLDOWN,
    BOSS_AIMED_COUNT, BOSS_MIXED_RADIAL, BOSS_MIXED_AIMED,
    TILE_SIZE, ROOM_COLS, ROOM_ROWS,
    BOSS_WALL_PROJECTILE_SPEED,
)
from src.algorithms.astar import astar
from src.model.level.tile import TileType
from src.model.projectile import BossProjectile
from src.config.assets import SPRITES


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, base_speed, hp, damage, size):
        super().__init__()
        self.hp = hp
        self.max_hp = hp
        self.speed = base_speed * random.uniform(0.85, 1.15)
        self.damage = damage
        self.base_image = pygame.Surface((size, size))
        self.base_image.fill((255, 0, 0))
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.hit_timer = 0.0
        self.path = []
        self.path_index = 0
        self.path_recalc_timer = 0.0
        self._last_player_tile = None
        self.velocity = pygame.math.Vector2(0, 0)
        self.state = "idle"
        self.detection_range = ENEMY_DETECTION_RANGE * TILE_SIZE
        self.chase_speed_mult = ENEMY_CHASE_SPEED_MULT
        self.patrol_target = None
        self.patrol_timer = random.uniform(1.0, 3.0)

    def update(self, dt, player, grid):
        if self.hit_timer > 0:
            self.hit_timer -= dt
            if self.hit_timer <= 0:
                self.image = self.base_image.copy()
        dist = math.hypot(player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery)
        self.state = "chase" if dist < self.detection_range else "idle"
        (self._chase if self.state == "chase" else self._patrol)(dt, player, grid)
        self.rect.centerx = max(TILE_SIZE, min(self.rect.centerx, (ROOM_COLS - 1) * TILE_SIZE))
        self.rect.centery = max(TILE_SIZE, min(self.rect.centery, (ROOM_ROWS - 1) * TILE_SIZE))

    def _chase(self, dt, player, grid):
        path_valid = self.path and self.path_index < len(self.path)
        if not path_valid:
            cur = (int(self.rect.centerx // TILE_SIZE), int(self.rect.centery // TILE_SIZE))
            goal = (int(player.rect.centerx // TILE_SIZE), int(player.rect.centery // TILE_SIZE))
            if cur != goal:
                self.path = astar(cur, goal, grid)
                self.path_index = 0
            else:
                dx = player.rect.centerx - self.rect.centerx
                dy = player.rect.centery - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist > 1:
                    speed = self.speed * self.chase_speed_mult
                    self.rect.centerx += (dx / dist) * speed * dt
                    self.rect.centery += (dy / dist) * speed * dt
                return
        self._follow_path(dt)

    def _patrol(self, dt, player, grid):
        self.patrol_timer -= dt
        if self.patrol_timer <= 0 or self.patrol_target is None:
            self.patrol_timer = random.uniform(1.5, 4.0)
            cur = (int(self.rect.centerx // TILE_SIZE), int(self.rect.centery // TILE_SIZE))
            for _ in range(10):
                tx, ty = random.randint(1, ROOM_COLS - 2), random.randint(1, ROOM_ROWS - 2)
                if grid and grid[ty][tx] != TileType.WALL:
                    break
            else:
                return
            self.patrol_target = (tx, ty)
            if cur != self.patrol_target:
                self.path = astar(cur, self.patrol_target, grid)
                self.path_index = 0
        self._follow_path(dt)

    def _follow_path(self, dt):
        speed = self.speed * (self.chase_speed_mult if self.state == "chase" else 1.0)
        if not self.path or self.path_index >= len(self.path):
            self.velocity = pygame.math.Vector2(0, 0)
            return False
        tx = self.path[self.path_index][0] * TILE_SIZE + TILE_SIZE // 2
        ty = self.path[self.path_index][1] * TILE_SIZE + TILE_SIZE // 2
        dx, dy = tx - self.rect.centerx, ty - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist < 4:
            self.path_index += 1
            return self.path_index < len(self.path)
        if dist < 1:
            return True
        self.rect.centerx += (dx / dist) * speed * dt
        self.rect.centery += (dy / dist) * speed * dt
        return True

    def apply_separation(self, others, dt):
        fx, fy = 0.0, 0.0
        for o in others:
            if o is self:
                continue
            dx = self.rect.centerx - o.rect.centerx
            dy = self.rect.centery - o.rect.centery
            d = math.hypot(dx, dy)
            if 0 < d < 2.5 * TILE_SIZE:
                s = (2.5 * TILE_SIZE - d) / (2.5 * TILE_SIZE)
                fx += (dx / d) * s
                fy += (dy / d) * s
        self.rect.centerx += fx * 90 * dt
        self.rect.centery += fy * 90 * dt

    def take_damage(self, amount):
        self.hp -= amount
        self.hit_timer = 0.1
        self.image = self.base_image.copy()
        red = pygame.Surface(self.image.get_size())
        red.fill((255, 0, 0))
        self.image.blit(red, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        if self.hp <= 0:
            self.kill()

    @property
    def alive(self):
        return self.hp > 0

    @property
    def center(self):
        return pygame.math.Vector2(self.rect.center)


class WormEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, WORM_SPEED, WORM_HP, WORM_DAMAGE, 28)
        spr = SPRITES.get("enemy_lust")
        if spr:
            self.base_image = pygame.transform.scale(spr, (28, 28))
        else:
            self.base_image = pygame.Surface((28, 28))
            self.base_image.fill((180, 60, 180))
        self.image = self.base_image.copy()
        self.attack_cooldown = 0.0

    def update(self, dt, player, grid):
        super().update(dt, player, grid)
        self.attack_cooldown -= dt
        if self.attack_cooldown <= 0 and self.rect.colliderect(player.rect.inflate(10, 10)):
            player.take_damage(self.damage)
            self.attack_cooldown = 1.0


class BossHeart(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 0, BOSS_HP, 0, 64)
        spr = SPRITES.get("boss")
        if spr:
            self.base_image = spr.copy()
        else:
            self.base_image = pygame.Surface((64, 64))
            self.base_image.fill((180, 20, 20))
        self.image = self.base_image.copy()
        self.attack_timer = 0.0
        self._spiral_angle = 0.0

    def update(self, dt, player, grid):
        pass

    def update_attack(self, dt, player, projectiles_group):
        self.attack_timer -= dt
        if self.attack_timer > 0:
            return
        hp_ratio = self.hp / self.max_hp
        phase = 1 if hp_ratio > 0.7 else (2 if hp_ratio > 0.4 else (3 if hp_ratio > 0.15 else 4))
        cd = [BOSS_PHASE1_COOLDOWN, BOSS_PHASE2_COOLDOWN, BOSS_PHASE3_COOLDOWN, BOSS_PHASE4_COOLDOWN][phase - 1]
        self.attack_timer = cd
        r = random.random()
        if phase == 1:
            if r < 0.4:
                self._burst(projectiles_group, 6, None)
            elif r < 0.7:
                self._burst(projectiles_group, None, player)
            else:
                self._burst_cross(projectiles_group, 6, player)
        elif phase == 2:
            if r < 0.25:
                self._burst(projectiles_group, 10, None)
            elif r < 0.5:
                self._burst(projectiles_group, None, player)
            elif r < 0.75:
                self._burst(projectiles_group, 12, None, spiral=True)
            else:
                self._burst_mixed(projectiles_group, player)
        elif phase == 3:
            if r < 0.2:
                self._burst(projectiles_group, 16, None)
            elif r < 0.35:
                self._burst(projectiles_group, None, player)
            elif r < 0.5:
                self._burst(projectiles_group, 20, None, spiral=True)
            elif r < 0.7:
                self._burst_cross(projectiles_group, 12, player)
            elif r < 0.85:
                self._burst_wall_h(projectiles_group, player)
            else:
                self._burst_mixed(projectiles_group, player)
        else:
            if r < 0.15:
                self._burst(projectiles_group, 20, None)
            elif r < 0.3:
                self._burst(projectiles_group, 24, None, spiral=True)
            elif r < 0.45:
                self._burst_cross(projectiles_group, 16, player)
            elif r < 0.6:
                self._burst_mixed(projectiles_group, player)
            elif r < 0.8:
                self._burst_wall_h(projectiles_group, player)
            else:
                self._burst_wall_v(projectiles_group, player)

    def _burst(self, g, radial_count=None, player=None, spiral=False):
        cx, cy = self.rect.centerx, self.rect.centery
        if spiral:
            self._spiral_angle = (self._spiral_angle + 25) % 360
            step = 360.0 / radial_count
            for i in range(radial_count):
                a = math.radians(self._spiral_angle + i * step)
                g.add(BossProjectile(cx, cy, a, BOSS_PROJECTILE_SPEED, BOSS_PROJECTILE_DAMAGE))
        elif radial_count:
            step = 360.0 / radial_count
            for i in range(radial_count):
                g.add(BossProjectile(cx, cy, math.radians(i * step), BOSS_PROJECTILE_SPEED, BOSS_PROJECTILE_DAMAGE))
        else:
            base = math.atan2(player.rect.centery - cy, player.rect.centerx - cx)
            for _ in range(BOSS_AIMED_COUNT):
                a = base + math.radians(random.uniform(-15, 15))
                g.add(BossProjectile(cx, cy, a, BOSS_PROJECTILE_SPEED, BOSS_PROJECTILE_DAMAGE))

    def _burst_cross(self, g, count, player):
        cx, cy = self.rect.centerx, self.rect.centery
        base = math.atan2(player.rect.centery - cy, player.rect.centerx - cx)
        for i in range(count):
            a = base + math.radians(45 + i * 90 / count)
            g.add(BossProjectile(cx, cy, a, BOSS_PROJECTILE_SPEED, BOSS_PROJECTILE_DAMAGE))

    def _burst_mixed(self, g, player):
        cx, cy = self.rect.centerx, self.rect.centery
        step = 360.0 / BOSS_MIXED_RADIAL
        for i in range(BOSS_MIXED_RADIAL):
            g.add(BossProjectile(cx, cy, math.radians(i * step), BOSS_PROJECTILE_SPEED, BOSS_PROJECTILE_DAMAGE))
        base = math.atan2(player.rect.centery - cy, player.rect.centerx - cx)
        for _ in range(BOSS_MIXED_AIMED):
            a = base + math.radians(random.uniform(-10, 10))
            g.add(BossProjectile(cx, cy, a, BOSS_PROJECTILE_SPEED, BOSS_PROJECTILE_DAMAGE))

    def _burst_wall_h(self, g, player):
        w = getattr(self, 'room_width', ROOM_COLS)
        h = getattr(self, 'room_height', ROOM_ROWS)
        step = TILE_SIZE * 4
        count = (w - 4) * TILE_SIZE // step
        from_bottom = random.random() < 0.5
        cy = (h - 1) * TILE_SIZE if from_bottom else 0
        angle = 270 if from_bottom else 90
        for i in range(count):
            x = (4 + i * step // TILE_SIZE) * TILE_SIZE
            g.add(BossProjectile(x, cy, math.radians(angle), BOSS_WALL_PROJECTILE_SPEED, BOSS_PROJECTILE_DAMAGE))

    def _burst_wall_v(self, g, player):
        w = getattr(self, 'room_width', ROOM_COLS)
        h = getattr(self, 'room_height', ROOM_ROWS)
        step = TILE_SIZE * 4
        count = (h - 4) * TILE_SIZE // step
        from_right = random.random() < 0.5
        cx = (w - 1) * TILE_SIZE if from_right else 0
        angle = 180 if from_right else 0
        for i in range(count):
            y = (4 + i * step // TILE_SIZE) * TILE_SIZE
            g.add(BossProjectile(cx, y, math.radians(angle), BOSS_WALL_PROJECTILE_SPEED, BOSS_PROJECTILE_DAMAGE))
