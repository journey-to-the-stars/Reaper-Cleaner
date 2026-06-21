import pygame, math, sys, random
from src.config.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TILE_SIZE,
    FLOOR_TRANSITION_DURATION, NUM_FLOORS, HEALTH_PICKUP_HEAL,
    ROOM_COLS, ROOM_ROWS,
)
from src.config.assets import init_sprites, SPRITES
from src.model.game_state import GameState
from src.model.player import Player
from src.model.enemy import WormEnemy, BossHeart
from src.model.projectile import GrimoirFlame, BloodClot, BossProjectile
from src.model.pickup import Pickup, PickupType
from src.model.level.floor import Floor
from src.model.level.room import RoomType, DoorPosition, OPPOSITE_DOOR
from src.view.renderer import Renderer
from src.view.camera import Camera
from src.view.hud import HUD
from src.view.menu import Menu
from src.view.pause import PauseScreen
from src.view.controls import ControlsScreen
from src.view.cursor import Cursor
from src.view.dialogue import DialogueBox
from src.view.debug import DebugOverlay
from src.view.minimap import Minimap
from src.controller.input_handler import InputHandler
from src.controller.state_machine import StateMachine


class GameController:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        init_sprites()
        pygame.display.set_caption("Reaper-Cleaner")
        pygame.mouse.set_visible(False)
        self.clock = pygame.time.Clock()
        self.running = True
        self.input_handler = InputHandler()
        self.state_machine = StateMachine()
        self.camera = Camera()
        self.renderer = Renderer(self.screen, self.camera)
        self.debug_overlay = DebugOverlay()
        self.menu = Menu()
        self.pause_screen = PauseScreen()
        self.controls_screen = ControlsScreen()
        self.cursor = Cursor()
        self.dialogue = DialogueBox()
        self.minimap = Minimap()
        self.player = None
        self.floor = None
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.pickups = pygame.sprite.Group()
        self.hud = None
        self.font_large = pygame.font.Font(None, 48)
        self.font_floor = pygame.font.Font(None, 72)
        self._transition_timer = 0.0
        self._transition_text = ""
        self._room_transition_timer = 0.0
        self._death_fade_timer = 0.0
        self._victory_fade_timer = 0.0
        self._show_controls = False
        self.exit_portal = None

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            events = pygame.event.get()
            self.input_handler.handle_events(events)
            for e in events:
                if e.type == pygame.QUIT:
                    self.running = False
            if self.state_machine.is_in(GameState.MENU):
                self._update_menu()
            elif self.state_machine.is_in(GameState.PLAY):
                self._update_play(dt)
            elif self.state_machine.is_in(GameState.DIALOGUE):
                self._update_dialogue(dt)
            elif self.state_machine.is_in(GameState.PAUSE):
                self._update_pause()
            elif self.state_machine.is_in(GameState.DEATH):
                self._update_death(dt)
            elif self.state_machine.is_in(GameState.BOSS_VICTORY):
                self._update_victory(dt)
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    def _start_game(self):
        self.floor = Floor(floor_number=1)
        self._update_camera_for_room()
        self.player = Player(*self.floor.current_room.center)
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.pickups = pygame.sprite.Group()
        self.hud = HUD(self.player)
        self._spawn_current_room()
        self._transition_timer = 0.0
        self._room_transition_timer = 0.0
        self.exit_portal = None
        room = self.floor.current_room
        for p in room.spawned_pickups:
            if not p.collected:
                self.pickups.add(p)
        self.dialogue.push(
            "Старший Жнец",
            "Слышь, стажёр. Появилась работёнка — "
            "бесы совсем обнаглели, "
            "прутся из всех щелей.\n"
            "Возьми косу, гримуар "
            "и прочисти этажи.",
            choices=["Взял косу, босс.", "Ага."],
            on_choice=self._apply_intro_buff,
        )
        self.state_machine.change_to(GameState.DIALOGUE)
        self.state_machine.previous_state = GameState.PLAY

    def _advance_floor(self):
        prev_floor = self.floor.floor_number
        self.floor = Floor(floor_number=prev_floor + 1)
        self._update_camera_for_room()
        self.player.rect.center = self.floor.current_room.center
        self.enemies.empty()
        self.projectiles.empty()
        self.pickups.empty()
        self._room_transition_timer = 0.0
        self.exit_portal = None
        self.player.hit_enemies.clear()
        room = self.floor.current_room
        for p in room.spawned_pickups:
            if not p.collected:
                self.pickups.add(p)
        if self.floor.is_final:
            self.dialogue.push(
                "Старший Жнец",
                f"Этаж {prev_floor} пройден!\n"
                "Впереди босс. Возьми что-нибудь, "
                "чтобы было не так страшно, салага!",
                choices=["Усилить косу (урон + радиус)", "Гримуар: +1 снаряд"],
                on_choice=self._apply_floor_buff,
            )
        else:
            self.dialogue.push(
                "Старший Жнец",
                "Этаж пройден! Выбери награду, стажёр:",
                choices=["Усилить косу (урон + радиус)", "Гримуар: +1 снаряд"],
                on_choice=self._apply_floor_buff,
            )
        self._spawn_current_room()

    def _spawn_current_room(self):
        room = self.floor.current_room
        if room.cleared:
            return
        floor = self.floor.floor_number
        room.spawned_enemies.clear()
        if room.room_type == RoomType.CHALLENGE:
            room.current_wave = 0
            if room.waves and room.waves[0]:
                for wx, wy, sc in room.waves[room.current_wave]:
                    e = sc(wx, wy)
                    if random.random() < 0.05 + floor * 0.02:
                        e = self._make_miniboss(e)
                    self.enemies.add(e)
                    room.spawned_enemies.append(e)
            else:
                room.room_type = RoomType.COMBAT
                room.waves = []
            return
        for wx, wy, sc in room.enemy_spawns:
            e = sc(wx, wy)
            if sc is BossHeart:
                e.room_width = room.room_width
                e.room_height = room.room_height
            is_exit = room.room_type == RoomType.EXIT
            chance = (0.10 + floor * 0.03) if is_exit else (0.05 + floor * 0.02)
            if sc is not BossHeart and random.random() < chance:
                e = self._make_miniboss(e)
            self.enemies.add(e)
            room.spawned_enemies.append(e)

    def _make_miniboss(self, enemy):
        enemy.hp *= 2
        enemy.max_hp = enemy.hp
        enemy.speed *= 1.15
        enemy.damage *= 1.5
        enemy.image = pygame.transform.scale(enemy.image, (48, 48))
        enemy.rect = enemy.image.get_rect(center=enemy.rect.center)
        dark = pygame.Surface((48, 48))
        dark.fill((80, 80, 80))
        enemy.image.blit(dark, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        enemy.base_image = enemy.image.copy()
        return enemy

    def _check_room_clear(self):
        room = self.floor.current_room
        if room.cleared or not room.spawned_enemies:
            return
        if all(not e.alive for e in room.spawned_enemies):
            if room.room_type == RoomType.CHALLENGE:
                room.current_wave += 1
                if room.current_wave < len(room.waves):
                    room.spawned_enemies.clear()
                    for wx, wy, sc in room.waves[room.current_wave]:
                        e = sc(wx, wy)
                        self.enemies.add(e)
                        room.spawned_enemies.append(e)
                    return
            room.cleared = True
            self._spawn_pickups(room)
            if room.room_type == RoomType.BOSS:
                self._victory_fade_timer = 0.5

    def _spawn_pickups(self, room):
        if room.room_type not in (RoomType.COMBAT, RoomType.EXIT, RoomType.BOSS, RoomType.CHALLENGE):
            return
        if room.room_type == RoomType.COMBAT:
            existing = [p.rect for p in room.spawned_pickups]
            for _ in range(random.randint(1, 2)):
                for attempt in range(20):
                    x = random.randint(2 * TILE_SIZE, (room.room_width - 2) * TILE_SIZE)
                    y = random.randint(2 * TILE_SIZE, (room.room_height - 2) * TILE_SIZE)
                    r = pygame.Rect(x - 8, y - 8, 16, 16)
                    if not any(r.colliderect(e) for e in existing):
                        break
                p = Pickup(x, y, PickupType.HEALTH)
                self.pickups.add(p)
                room.spawned_pickups.append(p)
                existing.append(p.rect)
        if room.room_type == RoomType.EXIT:
            cx = room.room_width // 2 * TILE_SIZE + TILE_SIZE // 2
            cy = room.room_height // 2 * TILE_SIZE + TILE_SIZE // 2
            p = Pickup(cx, cy, PickupType.HEALTH)
            self.pickups.add(p)
            room.spawned_pickups.append(p)
            ps = 48
            self.exit_portal = pygame.Rect(cx - ps // 2, cy - ps // 2, ps, ps)
        if room.room_type == RoomType.CHALLENGE:
            cx = room.room_width // 2 * TILE_SIZE + TILE_SIZE // 2
            cy = room.room_height // 2 * TILE_SIZE + TILE_SIZE // 2
            p = Pickup(cx, cy, PickupType.CHALLENGE_REWARD)
            self.pickups.add(p)
            room.spawned_pickups.append(p)

    def _update_camera_for_room(self):
        room = self.floor.current_room
        self.camera.set_room(room.room_width, room.room_height)

    def _check_door_transition(self):
        if self._room_transition_timer > 0:
            return
        room = self.floor.current_room
        if room.room_type == RoomType.BOSS:
            return
        if room.room_type in (RoomType.COMBAT, RoomType.EXIT, RoomType.CHALLENGE) and not room.cleared:
            return
        for door_pos, target_pos in room.doors.items():
            dr = room.get_door_rect(door_pos)
            if dr and self.player.rect.colliderect(dr):
                entered_from = OPPOSITE_DOOR[door_pos]
                self.floor.enter_room(door_pos)
                self._update_camera_for_room()
                self.player.rect.center = self.floor.get_spawn_position(entered_from)
                self.enemies.empty()
                self.projectiles.empty()
                self.pickups.empty()
                self._spawn_current_room()
                new_room = self.floor.current_room
                for p in new_room.spawned_pickups:
                    if not p.collected:
                        self.pickups.add(p)
                self._room_transition_timer = 0.3
                return

    def _start_floor_transition(self):
        self._transition_timer = FLOOR_TRANSITION_DURATION
        self._transition_text = f"Этаж {self.floor.floor_number + 1}"

    def _update_menu(self):
        if self._show_controls:
            if self.input_handler.scythe_pressed:
                self._show_controls = False
            self.controls_screen.draw(self.screen)
            self.cursor.draw(self.screen)
            return
        if self.input_handler.scythe_pressed:
            r = self.menu.handle_click(self.input_handler.mouse_pos)
            if r == "play":
                self._start_game()
            elif r == "controls":
                self._show_controls = True
            elif r == "quit":
                self.running = False
        self.renderer.draw_menu(self.menu)
        self.cursor.draw(self.screen)

    def _update_play(self, dt):
        FADE_DURATION = 0.5
        if self._death_fade_timer > 0:
            self._death_fade_timer -= dt
            self._draw_play()
            alpha = 255 * (1 - self._death_fade_timer / FADE_DURATION)
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(int(alpha))
            self.screen.blit(overlay, (0, 0))
            if self._death_fade_timer <= 0:
                self._death_fade_timer = 0.0
                self.dialogue.push(
                    "Старший Жнец",
                    "Ты... серьёзно? Ну как так можно, стажёр?\n"
                    "Косу тебе доверили, гримуар выдали...\n"
                    "Эх, тебе только ковры чистить.\n"
                    "Ладно, давай сначала.",
                    choices=["Продолжить"],
                    on_choice=lambda _: self.state_machine.change_to(GameState.MENU)
                )
                self.state_machine.change_to(GameState.DEATH)
            return
        if self._victory_fade_timer > 0:
            self._victory_fade_timer -= dt
            self._draw_play()
            alpha = 255 * (1 - self._victory_fade_timer / FADE_DURATION)
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(int(alpha))
            self.screen.blit(overlay, (0, 0))
            if self._victory_fade_timer <= 0:
                self._victory_fade_timer = 0.0
                self.dialogue.push(
                    "Старший Жнец",
                    "О, а ты молодец, стажёр! Не ожидал, если честно.\n"
                    "Докладываю: бесовское засилье подавлено.\n"
                    "Возвращайся пока в Чистилище, отдыхай.\n"
                    "Как будут дела — я свистну.",
                    choices=["Продолжить"],
                    on_choice=lambda _: self.state_machine.change_to(GameState.MENU)
                )
                self.state_machine.change_to(GameState.BOSS_VICTORY)
            return
        if self._transition_timer > 0:
            self._transition_timer -= dt
            self._draw_play()
            if self._transition_timer <= 0:
                self._advance_floor()
                self._transition_timer = 0.0
            return
        if self._room_transition_timer > 0:
            self._room_transition_timer -= dt
            self._draw_play()
            return
        if self.dialogue.is_busy:
            self.state_machine.change_to(GameState.DIALOGUE)
            return
        if self.input_handler.is_pause_pressed():
            self.state_machine.change_to(GameState.PAUSE)
            return
        if self.input_handler.is_debug_pressed():
            self.debug_overlay.visible = not self.debug_overlay.visible
        mx, my = self.input_handler.get_mouse_world_pos(self.camera)
        self.player.angle = math.degrees(math.atan2(my - self.player.rect.centery, mx - self.player.rect.centerx))
        room = self.floor.current_room
        self.floor.visited_rooms.add(self.floor.current_pos)
        wall_rects = room.get_wall_rects()
        if not room.cleared:
            for dp in room.doors:
                dr = room.get_door_rect(dp)
                if dr:
                    wall_rects.append(dr)
        self.player.update(dt, self.input_handler, wall_rects)
        self.enemies.update(dt, self.player, room.tiles_to_grid())
        for e in self.enemies.sprites():
            e.apply_separation(self.enemies.sprites(), dt)
        self.projectiles.update(dt, self.enemies)
        if room.room_type == RoomType.BOSS:
            for e in self.enemies.sprites():
                if isinstance(e, BossHeart):
                    e.update_attack(dt, self.player, self.projectiles)
        self._check_scythe_hits()
        self._check_grimoir_fire()
        self._check_projectile_hits()
        self._check_pickup_collisions()
        self._check_room_clear()
        self._check_door_transition()
        if room.room_type == RoomType.EXIT and room.cleared and self.exit_portal:
            if self.player.rect.colliderect(self.exit_portal):
                self._start_floor_transition()
        if not self.player.alive:
            self._death_fade_timer = 0.5
            return
        self._draw_play()

    def _draw_play(self, with_cursor=True):
        self.renderer.draw_room(self.floor.current_room)
        self.renderer.draw_sprites(self.enemies)
        self.renderer.draw_sprites(self.projectiles)
        self.renderer.draw_sprites(self.pickups)
        self.renderer.draw_sprite(self.player)
        if self.player.scythe_active:
            spr = SPRITES.get("scythe")
            if spr:
                ss = int(64 * self.player.scythe_scale)
                s = pygame.transform.scale(spr, (ss, ss))
                s = pygame.transform.rotate(s, -self.player.scythe_angle)
                off = 40 * self.player.scythe_scale
                ox = math.cos(math.radians(self.player.scythe_angle)) * off
                oy = math.sin(math.radians(self.player.scythe_angle)) * off
                pc = self.camera.apply(self.player).center
                sr = s.get_rect(center=(pc[0] + ox, pc[1] + oy))
                self.screen.blit(s, sr)
        if self.exit_portal and self.floor.current_room.room_type == RoomType.EXIT and self.floor.current_room.cleared:
            pc = self.camera.apply_rect(self.exit_portal)
            pygame.draw.circle(self.screen, (0, 200, 0), pc.center, 28)
            pygame.draw.circle(self.screen, (100, 255, 100), pc.center, 20)
            pygame.draw.circle(self.screen, (200, 255, 200), pc.center, 10)
        self.renderer.draw_wall_overlay(self.floor.current_room)
        self.minimap.draw(self.screen, self.floor)
        self.renderer.draw_hud(self.hud)
        self.debug_overlay.draw(self.screen, self.camera, floor=self.floor, enemies=self.enemies.sprites())
        if with_cursor:
            self.cursor.draw(self.screen)
        if self._transition_timer > 0:
            o = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            o.set_alpha(200)
            o.fill((0, 0, 0))
            self.screen.blit(o, (0, 0))
            t = self.font_floor.render(self._transition_text, True, (255, 255, 255))
            self.screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
        if self._room_transition_timer > 0:
            o = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            alpha = min(255, int(255 * (self._room_transition_timer / 0.3)))
            o.set_alpha(alpha)
            o.fill((0, 0, 0))
            self.screen.blit(o, (0, 0))

    def _update_dialogue(self, dt):
        self.dialogue.update(dt)
        self.dialogue.handle_input(
            self.input_handler.confirm_pressed,
            self.input_handler.scythe_pressed,
            self.input_handler.get_movement()[1],
        )
        self._draw_play(with_cursor=False)
        self.dialogue.draw(self.screen)
        if not self.dialogue.is_busy:
            self.state_machine.revert()

    def _apply_floor_buff(self, i):
        if i == 0:
            self.player.scythe_damage += 15
            self.player.scythe_range += 20
            self.player.scythe_half += 10
            self.player.scythe_scale += 0.15
            self.dialogue.push(
                "Старший Жнец",
                "Да ты любишь настоящее рубилово, сынок!\n"
                "Держи покрепче, а то кости у вас, стажёров, слабенькие.",
            )
        elif i == 1:
            self.player.grimoir_projectiles += 1
            self.dialogue.push(
                "Старший Жнец",
                "Ага, метишь в архимаги? Ну-ну,\n"
                "архимагичилка ещё не выросла.",
            )

    def _apply_challenge_reward(self, i):
        if i == 0:
            self.player.max_hp = int(self.player.max_hp * 1.2)
            self.player.hp = min(int(self.player.hp * 1.2), self.player.max_hp)
            self.dialogue.push("Награда", "Максимальное HP увеличено на 20%!")
        elif i == 1:
            self.player.scythe_cooldown_duration = max(0.1, self.player.scythe_cooldown_duration - 0.05)
            self.dialogue.push("Награда", "Скорость атаки увеличена!")
        elif i == 2:
            self.player.grimoir_charge_time = max(0.3, self.player.grimoir_charge_time - 0.08)
            self.dialogue.push("Награда", "Скорость зарядки гримуара увеличена!")

    def _apply_intro_buff(self, i):
        if i == 0:
            self.player.scythe_cooldown_duration = max(0.1, self.player.scythe_cooldown_duration - 0.05)
        elif i == 1:
            self.player.max_hp = int(self.player.max_hp * 1.2)
            self.player.hp = self.player.max_hp

    def _update_pause(self):
        if self.input_handler.scythe_pressed:
            r = self.pause_screen.handle_click(self.input_handler.mouse_pos)
            if r == "resume":
                self.state_machine.revert()
            elif r == "restart":
                self._start_game()
            elif r == "menu":
                self.state_machine.change_to(GameState.MENU)
        if self.input_handler.is_pause_pressed():
            self.state_machine.revert()
        self.renderer.draw_pause(self.pause_screen)
        self.cursor.draw(self.screen)

    def _update_death(self, dt):
        self.dialogue.update(dt)
        self.dialogue.handle_input(
            self.input_handler.confirm_pressed,
            self.input_handler.scythe_pressed,
            self.input_handler.get_movement()[1],
        )
        self.screen.fill((0, 0, 0))
        self.dialogue.draw(self.screen)

    def _update_victory(self, dt):
        self.dialogue.update(dt)
        self.dialogue.handle_input(
            self.input_handler.confirm_pressed,
            self.input_handler.scythe_pressed,
            self.input_handler.get_movement()[1],
        )
        self.screen.fill((0, 0, 0))
        self.dialogue.draw(self.screen)

    def _check_scythe_hits(self):
        if not self.player.scythe_active:
            return
        for e in self.enemies.sprites():
            if e in self.player.hit_enemies:
                continue
            if self.player.is_scythe_hitting(e.rect):
                e.take_damage(self.player.scythe_damage)
                self.player.hit_enemies.add(e)

    def _check_grimoir_fire(self):
        if not self.player.grimoir_just_fired:
            return
        self.player.grimoir_just_fired = False
        spread = 15
        n = self.player.grimoir_projectiles
        for i in range(n):
            a = self.player.angle + math.radians((i - (n - 1) / 2) * spread)
            self.projectiles.add(GrimoirFlame(self.player.rect.centerx, self.player.rect.centery, a))

    def _check_projectile_hits(self):
        for p in self.projectiles.sprites():
            if isinstance(p, (BloodClot, BossProjectile)):
                if self.player.rect.colliderect(p.rect):
                    self.player.take_damage(p.damage)
                    p.kill()
            elif isinstance(p, GrimoirFlame):
                for e in self.enemies.sprites():
                    if e.rect.colliderect(p.rect):
                        e.take_damage(p.damage)
                        p.kill()
                        break

    def _check_pickup_collisions(self):
        for p in list(self.pickups):
            if self.player.rect.colliderect(p.rect):
                if p.ptype == PickupType.HEALTH:
                    self.player.heal(HEALTH_PICKUP_HEAL)
                elif p.ptype == PickupType.GRIMOIRE_UPGRADE:
                    n = self.player.grimoir_projectiles
                    self.dialogue.push(
                        "Гримуар",
                        "Древняя сила наполняет страницы...\n"
                        f"Увеличить количество снарядов? ({n} \u2192 {n + 1})",
                        choices=["Да", "Нет"],
                        on_choice=lambda i: setattr(self.player, 'grimoir_projectiles', self.player.grimoir_projectiles + 1) if i == 0 else None,
                    )
                elif p.ptype == PickupType.CHALLENGE_REWARD:
                    self.dialogue.push(
                        "Испытание пройдено",
                        "Выбери награду:",
                        choices=["+20% макс. HP", "Скорость атаки", "+0.08c зарядка"],
                        on_choice=self._apply_challenge_reward,
                    )
                p.collected = True
                p.kill()
