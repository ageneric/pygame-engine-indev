import pygame

class TileSpriteSheet:
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert_alpha()
        except pygame.error as e:
            raise SystemExit(f'{e}: {filename}')

    def load_image(self, rect: pygame.Rect, tile_size=1):
        """Cuts out a rectangle from the loaded sprite sheet."""
        rect = pygame.Rect([dimension * tile_size for dimension in rect])
        image = pygame.Surface(rect.size).convert()
        image.blit(self.sheet, (0, 0), rect)
        image.set_colorkey((0, 0, 0))
        return image

def tint_surface(surface, tint_color):
    surface.fill(tint_color, special_flags=pygame.BLEND_MULT)
