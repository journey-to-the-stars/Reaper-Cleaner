import pygame, math, sys, random
from src.config.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TILE_SIZE, SCYTHE_DAMAGE,
    FLOOR_TRANSITION_DURATION, NUM_FLOORS, HEALTH_PICKUP_HEAL,
)
from src.config.assets import init_sprites
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
        self._show_controls = False

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
            elif self.state_machine.is_in(GameState.PAUSE):
                self._update_pause()
            elif self.state_machine.is_in(GameState.DEATH):
                self._update_death()
            elif self.state_machine.is_in(GameState.BOSS_VICTORY):
                self._update_victory()
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    def _start_game(self):
        self.floor = Floor(floor_number=1)
        self.player = Player(*self.floor.current_room.center)
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.pickups = pygame.sprite.Group()
        self.hud = HUD(self.player)
        self._spawn_current_room()
        self._transition_timer = 0.0
        self.state_machine.change_to(GameState.PLAY)

    def _advance_floor(self):
        self.floor = Floor(floor_number=self.floor.floor_number + 1)
        self.player.rect.center = self.floor.current_room.center
        self.enemies.empty()
        self.projectiles.empty()
        self.pickups.empty()
        self._spawn_current_room()

    def _spawn_current_room(self):
        room = self.floor.current_room
        if room.cleared:
            return
        for wx, wy, sc in room.enemy_spawns:
            e = sc(wx, wy)
            self.enemies.add(e)
            room.spawned_enemies.append(e)

    def _check_room_clear(self):
        room = self.floor.current_room
        if room.cleared or not room.spawned_enemies:
            return
        if all(not e.alive for e in room.spawned_enemies):
            room.cleared = True
            self._spawn_pickups(room)
            if room.room_type == RoomType.BOSS:
                self.state_machine.change_to(GameState.BOSS_VICTORY)

    def _spawn_pickups(self, room):
        if room.room_type not in (RoomType.COMBAT, RoomType.EXIT, RoomType.BOSS):
            return
        if room.room_type == RoomType.COMBAT:
            for _ in range(random.randint(1, 3)):
                x = random.randint(2 * TILE_SIZE, (ROOM_COLS - 2) * TILE_SIZE)
                y = random.randint(2 * TILE_SIZE, (ROOM_ROWS - 2) * TILE_SIZE)
                self.pickups.add(Pickup(x, y, PickupType.HEALTH))
        if room.room_type == RoomType.EXIT:
            cx = ROOM_COLS // 2 * TILE_SIZE + TILE_SIZE // 2
            cy = ROOM_ROWS // 2 * TILE_SIZE + TILE_SIZE // 2
            self.pickups.add(Pickup(cx - 32, cy, PickupType.GRIMOIRE_UPGRADE))
            self.pickups.add(Pickup(cx + 32, cy, PickupType.HEALTH))

    def _check_door_transition(self):
        room = self.floor.current_room
        if room.room_type == RoomType.BOSS:
            return
        if room.room_type in (RoomType.COMBAT, RoomType.EXIT) and not room.cleared:
            return
        for door_pos, target_pos in room.doors.items():
            dr = room.get_door_rect(door_pos)
            if dr and self.player.rect.colliderect(dr):
                if room.room_type == RoomType.EXIT and room.cleared:
                    self._start_floor_transition()
                    return
                entered_from = OPPOSITE_DOOR[door_pos]
                self.floor.enter_room(door_pos)
                self.player.rect.center = self.floor.get_spawn_position(entered_from)
                self.enemies.empty()
                self.projectiles.empty()
                self.pickups.empty()
                self._spawn_current_room()
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
        if self._transition_timer > 0:
            self._transition_timer -= dt
            self._draw_play()
            if self._transition_timer <= 0:
                self._advance_floor()
                self._transition_timer = 0.0
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
        self.player.update(dt, self.input_handler, room.get_wall_rects())
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
        if not self.player.alive:
            self.state_machine.change_to(GameState.DEATH)
            return
        self._draw_play()

    def _draw_play(self):
        self.renderer.draw_room(self.floor.current_room)
        self.renderer.draw_sprites(self.enemies)
        self.renderer.draw_sprites(self.projectiles)
        self.renderer.draw_sprites(self.pickups)
        self.renderer.draw_sprite(self.player)
        self.renderer.draw_wall_overlay()
        self.minimap.draw(self.screen, self.floor)
        self.renderer.draw_hud(self.hud)
        self.debug_overlay.draw(self.screen, self.camera, floor=self.floor, enemies=self.enemies.sprites())
        self.cursor.draw(self.screen)
        if self._transition_timer > 0:
            o = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            o.set_alpha(200)
            o.fill((0, 0, 0))
            self.screen.blit(o, (0, 0))
            t = self.font_floor.render(self._transition_text, True, (255, 255, 255))
            self.screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

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

    def _update_death(self):
        if self.input_handler.scythe_pressed or self.input_handler.is_pause_pressed():
            self.state_machine.change_to(GameState.MENU)
        t = self.font_large.render("Похоже, тебе чистить только ковры", True, (255, 100, 100))
        self.renderer.draw_overlay_text(t)

    def _update_victory(self):
        if self.input_handler.scythe_pressed or self.input_handler.is_pause_pressed():
            self.state_machine.change_to(GameState.MENU)
        t = self.font_large.render("Молодец, стажёр!", True, (100, 255, 100))
        self.renderer.draw_overlay_text(t)

    def _check_scythe_hits(self):
        if not self.player.scythe_active:
            return
        for e in self.enemies.sprites():
            if self.player.is_scythe_hitting(e.rect.center):
                e.take_damage(SCYTHE_DAMAGE)

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
                    self.player.grimoir_projectiles += 1
                p.kill()
