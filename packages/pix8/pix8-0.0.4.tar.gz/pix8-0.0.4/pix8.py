"""
PIX-8 Fantasy Console
Pure Python • TIC-80 inspired

Version: 0.0.4
Dependency: pygame-ce (Community Edition)

Install:
    pip install pygame-ce
"""

import sys
import json
import pathlib
import importlib.util

# pygame-ce still imports as "pygame"
import pygame

# -------------------------
# Dependency sanity check
# -------------------------

if "ce" not in pygame.version.ver:
    print(
        "WARNING: You are using legacy pygame.\n"
        "PIX-8 officially supports pygame-ce.\n"
        "Install with: pip install -U pygame-ce\n"
    )

# -------------------------
# Console constants
# -------------------------

WIDTH = 128
HEIGHT = 128
SCALE = 4
FPS = 60

__version__ = "0.0.4"

SAVE_DIR = pathlib.Path.home() / ".pix8"
SAVE_FILE = SAVE_DIR / "save.json"

PALETTE = [
    (0, 0, 0), (29, 43, 83), (126, 37, 83), (0, 135, 81),
    (171, 82, 54), (95, 87, 79), (194, 195, 199), (255, 241, 232),
    (255, 0, 77), (255, 163, 0), (255, 236, 39), (0, 228, 54),
    (41, 173, 255), (131, 118, 156), (255, 119, 168), (255, 204, 170),
]

# -------------------------
# Input abstraction
# -------------------------

BUTTONS = {
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "a": pygame.K_z,
    "b": pygame.K_x,
}

class Input:
    def __init__(self):
        self.keys = None
        self.prev = None

        self.joy = None
        if pygame.joystick.get_count():
            self.joy = pygame.joystick.Joystick(0)
            self.joy.init()

    def update(self):
        self.prev = self.keys
        self.keys = pygame.key.get_pressed()

    def btn(self, name):
        key = BUTTONS.get(name)
        return bool(key and self.keys[key])

    def btnp(self, name):
        key = BUTTONS.get(name)
        if not key or not self.prev:
            return False
        return self.keys[key] and not self.prev[key]

# -------------------------
# PIX-8 Core
# -------------------------

class Pix8:
    def __init__(self, show_gui=True):
        pygame.init()
        pygame.mixer.init()
        pygame.font.init()

        self.show_gui = show_gui
        self.window = pygame.display.set_mode(
            (WIDTH * SCALE, HEIGHT * SCALE)
        )
        pygame.display.set_caption("PIX-8")

        self.surface = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.input = Input()

        self.cart = None
        self.running = True

        self.ui_font = pygame.font.SysFont("consolas", 16)

        SAVE_DIR.mkdir(exist_ok=True)
        self.save_data = self._load_save()

    # -------- Graphics --------

    def cls(self, c=0):
        self.surface.fill(PALETTE[c])

    def pix(self, x, y, c):
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            self.surface.set_at((x, y), PALETTE[c])

    def rect(self, x, y, w, h, c):
        pygame.draw.rect(self.surface, PALETTE[c], (x, y, w, h))

    def print(self, text, x, y, c=7):
        font = pygame.font.SysFont("consolas", 8)
        img = font.render(str(text), False, PALETTE[c])
        self.surface.blit(img, (x, y))

    # -------- Sprites --------

    def load_sprites(self, path, w, h):
        img = pygame.image.load(path).convert_alpha()
        sprites = []
        for y in range(0, img.get_height(), h):
            for x in range(0, img.get_width(), w):
                s = pygame.Surface((w, h), pygame.SRCALPHA)
                s.blit(img, (0, 0), (x, y, w, h))
                sprites.append(s)
        return sprites

    def spr(self, sprite, x, y):
        self.surface.blit(sprite, (x, y))

    # -------- Sound --------

    def sfx(self, path):
        pygame.mixer.Sound(path).play()

    # -------- Save Data --------

    def save(self, key, value):
        self.save_data[key] = value
        SAVE_FILE.write_text(json.dumps(self.save_data))

    def load(self, key, default=None):
        return self.save_data.get(key, default)

    def _load_save(self):
        if SAVE_FILE.exists():
            return json.loads(SAVE_FILE.read_text())
        return {}

    # -------- Cartridge --------

    def load_cart(self, path):
        spec = importlib.util.spec_from_file_location("cart", path)
        cart = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cart)
        self.cart = cart

        if hasattr(cart, "init"):
            cart.init(self)

    # -------- Main Loop --------

    def run(self):
        while self.running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False

            self.input.update()

            if self.cart and hasattr(self.cart, "update"):
                self.cart.update(self)

            if self.cart and hasattr(self.cart, "draw"):
                self.cart.draw(self)

            scaled = pygame.transform.scale(
                self.surface, (WIDTH * SCALE, HEIGHT * SCALE)
            )
            self.window.blit(scaled, (0, 0))

            if self.show_gui:
                self._draw_gui()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

    def _draw_gui(self):
        bar = pygame.Surface((WIDTH * SCALE, 24))
        bar.fill(PALETTE[1])
        self.window.blit(bar, (0, 0))

        title = self.ui_font.render(f"PIX-8 {__version__}", True, PALETTE[7])
        fps = self.ui_font.render(
            f"{int(self.clock.get_fps())} FPS", True, PALETTE[7]
        )

        self.window.blit(title, (8, 4))
        self.window.blit(fps, (WIDTH * SCALE - 80, 4))

# -------------------------
# Example PEP-8 Cartridge
# -------------------------

def init(p):
    p.x = 60
    p.y = 60
    p.score = p.load("score", 0)

def update(p):
    if p.input.btn("left"):
        p.x -= 1
    if p.input.btn("right"):
        p.x += 1
    if p.input.btn("up"):
        p.y -= 1
    if p.input.btn("down"):
        p.y += 1

    if p.input.btnp("a"):
        p.score += 1
        p.save("score", p.score)

def draw(p):
    p.cls(0)
    p.rect(p.x, p.y, 8, 8, 8)
    p.print(f"SCORE {p.score}", 4, 116, 11)

# -------------------------
# __main__
# -------------------------

def main():
    show_gui = "--nogui" not in sys.argv
    p = Pix8(show_gui=show_gui)

    for arg in sys.argv:
        if arg.endswith(".py"):
            p.load_cart(arg)
            break
    else:
        p.cart = sys.modules[__name__]

    p.run()

if __name__ == "__main__":
    main()
