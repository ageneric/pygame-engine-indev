import pygame
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP

from .base_node import SpriteNode
import engine.text as text

MOUSE_EVENTS = (MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP)
COLOR_DEFAULT = (191, 131, 191)
BACKGROUND_DEFAULT = (20, 20, 24)

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

class Button(SpriteNode):
    """A button. The keyword arguments color and background change the appearance.
    The argument callback is a function taking no parameters. It is called on click.
    To add parameters to the callback, it is recommended to inherit from this class.
    """
    idle, hover, press, disabled = range(4)

    def __init__(self, node_props, message="", callback=None, group=None, **kwargs):
        self.background_image = kwargs.get("image", None)
        fill_color = kwargs.get("background", BACKGROUND_DEFAULT)
        super(Button, self).__init__(node_props, group, image=self.background_image,
                                     fill_color=fill_color)
        self.callback = callback
        self.message = message

        self.style = {
            'color': COLOR_DEFAULT,
            'background': (0, 0, 0)
        }
        self.style.update(kwargs)

        self.visible = True  # True when visible. Button ignores input while invisible.
        self.state = Button.idle
        self.pre_render_text()

    def pre_render_text(self):
        return text.render(self.message, color=self.style['color'], save_sprite=True)

    def mouse_event(self, event):
        """Pass each pygame mouse event to the button,
        so it can update (i.e. if hovered or clicked).
        For speed, only call if `event.type in MOUSE_EVENTS`.
        """
        if self.state == Button.disabled or not self.visible:
            return
        last_state = self.state
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

        if last_state != self.state:
            self.dirty = 1

    def on_click(self):
        self.callback()

    def draw(self, surface):
        if self.visible and self.dirty:
            if self.background_image:
                self.image.blit(self.background_image, (0, 0))
                color = self.accent_color()
                text.draw(self.image, self.message, (self.transform.width / 2, self.transform.height / 2), color=color, justify=True)
            else:
                box_color = self.background_color()
                color = self.accent_color()

                text.box(self.image, self.message, (0, 0),
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

class TextEntry(SpriteNode):
    """A single line rectangular box that can be typed in."""
    idle, selected = range(2)

    def enter(self):
        pass

class Grid(SpriteNode):
    """A container for equally spaced UI items that draws them onto a buffer."""
