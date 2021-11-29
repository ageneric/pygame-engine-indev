import pygame as pg
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
import legacy_text

MOUSE_EVENTS = (MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP)
COLOR_DEFAULT = (191, 131, 191)
BACKGROUND_DEFAULT = (15, 15, 15)

def modify_color_component(color_component, saturation):
    """Lighten or darken an rgb value by the saturation percentage."""
    color_component = round(color_component * (1 + saturation/100))
    # Ensure value is between 0 - 255.
    color_component = min(color_component, 255)
    color_component = max(color_component, 0)
    return color_component

def modify_color(color, saturation):
    """Lighten or darken an (r, g, b) colour by the saturation percentage."""
    return tuple(modify_color_component(r_g_b, saturation) for r_g_b in color)

def specify_color(style, try_key, fallback_key, saturation=0.0):
    """A customisable color that may be specified in style;
    if not found, use the fallback color."""
    color = style.get(try_key)
    if color is None:  # Default if color cannot be found.
        color = modify_color(style[fallback_key], saturation)
    return color

class Button():
    idle, hover, press, disabled = range(4)

    def __init__(self, rect, message, callback=None, **kwargs):
        super().__init__()
        self.rect = pg.Rect(rect)
        self.callback = callback
        self.message = message

        self.style = {
            'color': COLOR_DEFAULT,
            'background': BACKGROUND_DEFAULT
        }
        self.style.update(kwargs)

        self.visible = True  # True when visible. Button ignores input while invisible.
        self.state = Button.idle
        self.pre_render_text()

    def pre_render_text(self):
        return legacy_text.render(self.message, color=self.style['color'], save_sprite=True)

    def mouse_event(self, event):
        """Pass each pygame mouse event to the button,
        so it can update (i.e. if hovered or clicked).
        For speed, only call if `event.type in MOUSE_EVENTS`.
        """
        if self.state == Button.disabled or not self.visible:
            return

        mouse_over = self.rect.collidepoint(event.pos)
        # Only react to a click on mouse-up (helps avoid an accidental click).
        if event.type == MOUSEBUTTONUP and self.state == Button.press:
            if mouse_over and self.callback:
                self.on_click()
            self.state = Button.idle

        if mouse_over:
            if event.type == MOUSEBUTTONDOWN:
                self.state = Button.press
            elif self.state == Button.idle:
                self.state = Button.hover
        elif self.state == Button.hover:
            self.state = Button.idle

    def on_click(self):
        self.callback()

    def update(self):
        pass

    def draw(self, screen):
        if self.visible:
            box_color = self.background_color()
            color = self.accent_color()

            legacy_text.box(screen, self.message, self.rect.topleft,
                            self.rect.width, self.rect.height, True, box_color, color=color)

    def background_color(self):
        if self.state == Button.hover:
            return modify_color(self.style['background'], -14.4)
        elif self.state == Button.press:
            return modify_color(self.style['background'], 14.4)
        elif self.state == Button.disabled:
            return specify_color(self.style, 'background_disabled', 'background', -28.8)
        return self.style['background']

    def accent_color(self):
        if self.state == Button.disabled:
            return specify_color(self.style, 'color_disabled', 'color', -20)
        return self.style['color']

class Toggle(Button):
    def __init__(self, rect, message, callback=None, checked=False, **kwargs):
        super().__init__(rect, message, callback, **kwargs)
        self.checked = checked  # Boolean toggle value.

    def on_click(self):
        self.checked = not self.checked  # Flip the toggle value.
        self.callback()

    def background_color(self):
        if self.checked:
            return specify_color(self.style, 'background_toggle', 'background', -20)
        else:
            return super().background_color()

    def accent_color(self):
        if self.checked:
            return specify_color(self.style, 'color_toggle', 'color')
        else:
            return super().accent_color()

class TransformNode(pg.sprite.Sprite):
    def __init__(self, rect, groups: pg.sprite.AbstractGroup):
        pg.sprite.Sprite.__init__(self, groups)
        self.rect = rect



