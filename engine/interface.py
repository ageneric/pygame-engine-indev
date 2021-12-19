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
        if self.state == Button.press and event.type == MOUSEBUTTONUP:
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
                text.draw(self.image, self.message, (self.transform.width / 2, self.transform.height / 2),
                          color=color, justify=True)
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
    idle, hover, selected, disabled = range(4)

    def __init__(self, node_props, default_text="", enter_callback=None, group=None, **kwargs):
        fill_color = kwargs.get("background", BACKGROUND_DEFAULT)
        super(TextEntry, self).__init__(node_props, group, fill_color=fill_color)

        self.enter_callback = enter_callback

        self.state = TextEntry.idle
        self.text = default_text

    def on_enter(self):
        self.enter_callback(self.text)
        self.state = TextEntry.idle

    def events(self, pygame_events):
        if self.state == TextEntry.disabled or not self.visible:
            return

        for event in pygame_events:
            last_state = self.state

            if event.type in MOUSE_EVENTS:
                mouse_over = self.rect.collidepoint(event.pos)

                if mouse_over:
                    if event.type == MOUSEBUTTONDOWN:
                        self.state = TextEntry.selected
                    elif self.state == TextEntry.idle:
                        self.state = TextEntry.hover
                elif self.state == TextEntry.hover or event.type == MOUSEBUTTONDOWN:
                    self.state = TextEntry.idle

            elif self.state == TextEntry.selected and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if self.enter_callback:
                        self.on_enter()
                elif event.key == pygame.K_ESCAPE or event.key == pygame.K_TAB:
                    self.state = TextEntry.idle
                elif event.mod & pygame.KMOD_CTRL:
                    if event.key == pygame.K_BACKSPACE:
                        self.text = ''
                        self.dirty = 1
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                    self.dirty = 1
                else:
                    self.text += event.unicode
                    self.dirty = 1

            if last_state != self.state:
                self.dirty = 1

    def draw(self, surface):
        super().draw(surface)
        if self.visible and self.dirty:
            if self.state == TextEntry.hover:
                self.image.fill(modify_color(BACKGROUND_DEFAULT, -15))  # todo: use actual
            else:
                self.image.fill(BACKGROUND_DEFAULT)  # todo: use actual

            if self.state == TextEntry.selected:
                text_to_draw = self.text + '|'
            else:
                text_to_draw = self.text
            text.draw(self.image, text_to_draw, (4, self.transform.height / 2),
                      justify=(False, True))

class Grid(SpriteNode):
    """A container for equally spaced UI items that draws them onto a buffer."""
    def __init__(self, node_props, group=None, **kwargs):
        fill_color = kwargs.get("background", BACKGROUND_DEFAULT)
        super(Grid, self).__init__(node_props, group, fill_color=fill_color)
