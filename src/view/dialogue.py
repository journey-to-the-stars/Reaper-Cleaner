import pygame
from src.config.settings import SCREEN_WIDTH, SCREEN_HEIGHT


CHAR_RATE = 40
PADDING = 20
LINE_SPACING = 28


class DialogueBox:
    def __init__(self):
        self.rect = pygame.Rect(0, int(SCREEN_HEIGHT * 0.62), SCREEN_WIDTH, int(SCREEN_HEIGHT * 0.38))
        self.queue = []
        self.active = False
        self.current = None
        self._text_display = ""
        self._char_index = 0
        self._char_timer = 0.0
        self._typing = False
        self._cursor_idx = 0
        self._choice_mode = False
        self._font_title = pygame.font.Font(None, 26)
        self._font_text = pygame.font.Font(None, 22)
        self._font_small = pygame.font.Font(None, 18)

    def push(self, title, text, choices=None, on_choice=None):
        self.queue.append({
            "title": title,
            "text": text,
            "choices": choices or [],
            "on_choice": on_choice,
        })

    def update(self, dt):
        if not self._start_next():
            return

        if self._typing:
            self._char_timer += dt
            n = int(self._char_timer * CHAR_RATE)
            if n > 0:
                self._char_timer -= n / CHAR_RATE
                self._char_index = min(self._char_index + n, len(self.current["text"]))
                self._text_display = self.current["text"][:self._char_index]
                if self._char_index >= len(self.current["text"]):
                    self._typing = False
                    self._choice_mode = bool(self.current["choices"])

    def handle_input(self, confirm_pressed, scythe_pressed, dy):
        if not self.active:
            return
        advance = confirm_pressed or scythe_pressed

        if self._typing:
            if advance:
                self._text_display = self.current["text"]
                self._char_index = len(self.current["text"])
                self._typing = False
                self._choice_mode = bool(self.current["choices"])
            return

        if self._choice_mode:
            if dy != 0:
                self._cursor_idx = max(0, min(len(self.current["choices"]) - 1, self._cursor_idx + (1 if dy > 0 else -1)))
            if advance:
                if self.current["on_choice"]:
                    self.current["on_choice"](self._cursor_idx)
                self._finish_current()
        else:
            if advance:
                self._finish_current()

    def draw(self, screen):
        if not self.active or not self.current:
            return

        pygame.draw.rect(screen, (0, 0, 0), self.rect)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)

        x = self.rect.x + PADDING
        y = self.rect.y + PADDING

        if self.current["title"]:
            s = self._font_title.render(self.current["title"], True, (255, 255, 255))
            screen.blit(s, (x, y))
            y += LINE_SPACING + 4

        for line in self._text_display.split("\n"):
            s = self._font_text.render(line, True, (255, 255, 255))
            screen.blit(s, (x, y))
            y += LINE_SPACING

        if self._choice_mode and self.current["choices"]:
            y = self.rect.bottom - PADDING - len(self.current["choices"]) * LINE_SPACING
            for i, choice in enumerate(self.current["choices"]):
                prefix = "\u25b6 " if i == self._cursor_idx else "  "
                s = self._font_text.render(f"{prefix}{choice}", True, (255, 255, 255) if i == self._cursor_idx else (180, 180, 180))
                screen.blit(s, (x + 10, y))
                y += LINE_SPACING

        elif not self._typing and not self._choice_mode:
            s = self._font_small.render("[\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u041b\u041a\u041c]", True, (120, 120, 120))
            screen.blit(s, (x, self.rect.bottom - PADDING - 22))

    def _start_next(self):
        if self.active:
            return True
        if not self.queue:
            return False
        self.current = self.queue.pop(0)
        self.active = True
        self._text_display = ""
        self._char_index = 0
        self._char_timer = 0.0
        self._typing = True
        self._cursor_idx = 0
        self._choice_mode = False
        return True

    def _finish_current(self):
        self.active = False
        self.current = None
        self._typing = False
        self._choice_mode = False

    @property
    def is_busy(self):
        return bool(self.queue) or self.active
