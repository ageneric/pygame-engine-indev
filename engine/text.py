import pygame
from typing import Union

pygame.font.init()
FONT_DEFAULT = pygame.font.SysFont('Calibri', 16)

COLOR_DEFAULT = (191, 131, 191)
BACKGROUND_DEFAULT = (20, 20, 24)
BOX_PADDING = 5

_sprite_cache = {}

def draw(surface, message: str, position: (int, int), color=COLOR_DEFAULT, font=FONT_DEFAULT,
         text_sprite=None, static=False, justify: Union[bool, tuple, list] = False) -> pygame.Rect:
    """Draws text to the surface at the (x, y) position specified.
    Justify - set to True/False to centre in both/neither axes,
        or pick separately for the (x, y) axes, i.e. set to
        (True, False) to centre horizontally and not vertically.
    Static - set to True to cache the text sprite (for faster drawing).
    """
    if text_sprite is None:  # render a new surface with text if None supplied
        text_sprite = render(message, font, color, static)

    x, y = position  # unpack position so x, y can be translated independently
    if justify:
        text_rect = text_sprite.get_rect()
        if justify is True or justify[0] is True:
            x -= text_rect.width / 2
        if justify is True or justify[1] is True:
            y -= text_rect.height / 2

    return surface.blit(text_sprite, (x, y))

def render(message: str, font=FONT_DEFAULT, color=COLOR_DEFAULT, save_sprite=True):
    """Render text, using the sprite cache if possible. Return the surface.
    Adds to sprite cache when called directly or rendering static text.
    """
    text_sprite = _sprite_cache.get((message, font, *color))

    if text_sprite is None:
        text_sprite = font.render(message, True, color)
        if save_sprite:
            _sprite_cache[(message, font, *color)] = text_sprite

    return text_sprite

def box(surface, message: str, position: (int, int), width=None, height=None, middle=False,
        box_color=BACKGROUND_DEFAULT, color=COLOR_DEFAULT, font=FONT_DEFAULT) -> pygame.Rect:
    """Blits a text box to the surface at the (x, y) position specified.
    The width and height, if omitted, fit the text's size. The text sprite
    is also cached if either omitted. Set middle = True to centre text.
    """
    if width is None or height is None:
        text_sprite = render(message, font, color, save_sprite=True)
        if width is None:
            width = text_sprite.get_rect().width + 2*BOX_PADDING
        if height is None:
            height = text_sprite.get_rect().height + 2*BOX_PADDING

    box_rect = pygame.Rect(position, (width, height))
    pygame.draw.rect(surface, box_color, box_rect)

    if message:
        if middle:
            draw(surface, message, box_rect.center, color, font, justify=True)
        else:
            draw(surface, message, (position[0] + BOX_PADDING, box_rect.centery), color,
                 font, justify=(False, True))

    return box_rect
