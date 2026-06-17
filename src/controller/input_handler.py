import pygame


class InputHandler:
    def __init__(self):
        self.keys = {}
        self.mouse_buttons = {}
        self.mouse_pos = (0, 0)
        self.scythe_pressed = False
        self.confirm_pressed = False
        self.grimoir_held = False
        self.pause_pressed = False
        self.debug_pressed = False

    def handle_events(self, events):
        self.scythe_pressed = False
        self.confirm_pressed = False
        self.pause_pressed = False
        self.debug_pressed = False

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.pause_pressed = True
                if event.key == pygame.K_F1:
                    self.debug_pressed = True
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self.confirm_pressed = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.scythe_pressed = True
        self.keys = pygame.key.get_pressed()
        self.mouse_buttons = pygame.mouse.get_pressed()
        self.mouse_pos = pygame.mouse.get_pos()
        self.grimoir_held = self.mouse_buttons[2]

    def get_movement(self):
        dx = dy = 0
        if self.keys[pygame.K_a] or self.keys[pygame.K_LEFT]:
            dx -= 1
        if self.keys[pygame.K_d] or self.keys[pygame.K_RIGHT]:
            dx += 1
        if self.keys[pygame.K_w] or self.keys[pygame.K_UP]:
            dy -= 1
        if self.keys[pygame.K_s] or self.keys[pygame.K_DOWN]:
            dy += 1
        return dx, dy

    def is_scythe_pressed(self):
        return self.scythe_pressed

    def is_grimoir_held(self):
        return self.grimoir_held

    def is_pause_pressed(self):
        return self.pause_pressed

    def is_debug_pressed(self):
        return self.debug_pressed

    def get_mouse_world_pos(self, camera):
        mx, my = self.mouse_pos
        return camera.screen_to_world(mx, my)
