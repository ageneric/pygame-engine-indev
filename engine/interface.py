import pygame
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP, Rect
from math import sqrt

from .base_node import SpriteNode, NodeProperties, Transform
import engine.text as text

MOUSE_EVENTS = (MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP)

COLOR_DEFAULT = (191, 131, 191)
BACKGROUND_DEFAULT = (20, 20, 24)
NO_VALUE = object()

def modify_color_component(color_component, brightness):
    """Lighten or darken a single rgb value by the perceived brightness percentage."""
    color_component = round(max(sqrt(color_component) + brightness/6.25, 0)**2)
    color_component = min(max(color_component, 0), 255)  # clamp value between 0 and 255
    return color_component

def modify_color(color, brightness: float):
    """Lighten or darken an (r, g, b) colour by the perceived brightness percentage."""
    return tuple(modify_color_component(r_g_b, brightness) for r_g_b in color)

def saturate_color_component(color_component, mean, saturation):
    """Saturate or desaturate a single rgb value by the given multiplier. See saturate_color()."""
    color_component = round(mean * (1 - saturation) + color_component * saturation)
    color_component = min(max(color_component, 0), 255)  # clamp value between 0 and 255
    return color_component

def saturate_color(color, saturation: float):
    """Saturate or desaturate an (r, g, b) colour by the given multiplier, where
    0: grayscale, 0-1: desaturated, 1: identical, >1: further saturated;
    negative values result in the complementary color.
    """
    mean = sum(r_g_b for r_g_b in color) / 3
    return tuple(saturate_color_component(r_g_b, mean, saturation) for r_g_b in color)

class Style:
    def __init__(self, **kwargs):
        self.dict = {'color': COLOR_DEFAULT, 'background': BACKGROUND_DEFAULT}
        self.dict.update(kwargs)

    # def __repr__(self):
    #     return str(self.__dict__)

    @classmethod
    def from_kwargs(cls, kwargs):
        if kwargs.get("style", False):
            return kwargs.get("style")
        else:
            return cls(**kwargs)

    def get(self, name: str, default=NO_VALUE):
        if name in self.dict:
            return self.dict[name]
        elif name.count("_") == 1:
            base_name, modifier = name.split("_", 1)
            if modifier == "highlighted":
                return modify_color(self.get(base_name), -5)
            elif modifier == "selected":
                return modify_color(self.get(base_name), 5)
            elif modifier == "disabled":
                return saturate_color(modify_color(self.get(base_name), -10), 0.25)
        if default != NO_VALUE:
            return default
        raise KeyError(f"Not a key and not a modifier of a key: {name} in {self.dict}")


class Button(SpriteNode):
    """A button. The keyword arguments color and background change the appearance.
    The argument callback is a function taking no parameters. It is called on click.
    To add parameters to the callback, it is recommended to inherit from this class.
    """
    idle, hover, press, disabled = range(4)

    def __init__(self, node_props, group, message="", callback=None, **kwargs):
        self.style = Style.from_kwargs(kwargs)
        super().__init__(node_props, group, image=kwargs.get("image", None),
                         fill_color=self.style.get("background"))

        self.callback = callback
        self.message = message

        self.state = Button.idle
        self.pre_render_text()

        self.background_colors_d = {
            Button.hover: 'background_highlighted',
            Button.press: 'background_selected',
            Button.disabled: 'background_disabled'
        }
        self.colors_d = {
            Button.disabled: 'color_disabled'
        }

    def pre_render_text(self):
        return text.render(self.message, color=self.style.get('color'), save_sprite=True)

    def mouse_event(self, event):
        """Pass each pygame mouse event to the button,
        so it can update (i.e. if hovered or clicked).
        For speed, only call if `event.type in MOUSE_EVENTS`.
        """
        if self.state == Button.disabled or not self._visible:
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
        super().draw(surface)
        if self._visible and self.dirty > 0:
            if self.style.get("image", False):
                self.image.blit(self.style.get("image"), (0, 0))
                color = self.style.get(self.colors_d.get(self.state, "color"))
                text.draw(self.image, self.message, (self.transform.width / 2, self.transform.height / 2),
                          color=color, justify=True)
            else:
                box_color = self.style.get(self.background_colors_d.get(self.state, "background"))
                color = self.style.get(self.colors_d.get(self.state, "color"))

                text.box(self.image, self.message, (0, 0),
                         self.rect.width, self.rect.height, True, box_color, color=color)


class TextEntry(SpriteNode):
    """A single line rectangular box that can be typed in.
    Set allow_characters = '1234' or ['1', '2'] to only allow those characters."""
    idle, hover, selected, disabled = range(4)

    def __init__(self, node_props, group, default_text="", enter_callback=None,
                 allow_characters=None, **kwargs):
        self.style = Style.from_kwargs(kwargs)
        super().__init__(node_props, group, fill_color=self.style.get("background"))

        self.enter_callback = enter_callback

        self.state = TextEntry.idle
        self.text = default_text
        self.allow_characters = allow_characters

    def on_enter(self):
        self.enter_callback(self.text)
        self.state = TextEntry.idle

    def on_change(self):
        pass

    def events(self, pygame_events):
        if self.state == TextEntry.disabled or not self._visible:
            return

        last_state = self.state
        last_text = self.text

        for event in pygame_events:
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
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif self.allow_characters is None or event.unicode in self.allow_characters:
                    self.text += event.unicode

        if last_state != self.state or last_text != self.text:
            self.dirty = 1
        if last_text != self.text:
            self.on_change()

    def draw(self, surface):
        super().draw(surface)
        if self._visible and self.dirty > 0:
            if self.state == TextEntry.hover:
                self.image.fill(self.style.get("background_highlighted"))
            else:
                self.image.fill(self.style.get("background"))

            if self.state == TextEntry.selected:
                text_to_draw = self.text + '|'
            else:
                text_to_draw = self.text
            text.draw(self.image, text_to_draw, (4, self.transform.height / 2),
                      justify=(False, True))


class Grid(SpriteNode):
    """A container for equally spaced items that draws them onto a buffer.
    The default grid ignores the position attributes on each tile and instead
    spaces them in order. For optimised use."""
    def __init__(self, node_props, group, initial_nodes_gen=None, horizontal=False, **kwargs):
        self.style = Style.from_kwargs(kwargs)
        super().__init__(node_props, group, fill_color=self.style.get("background"))

        self.horizontal = horizontal
        if initial_nodes_gen is not None:
            self.generate_grid(initial_nodes_gen)
            # Check the first node for methods and assume they are all identical
            t_node = self.nodes[0]
            self.call_draw_method = hasattr(t_node, 'draw') and callable(t_node.draw)
            self.call_update_method = hasattr(t_node, 'update') and callable(t_node.update)
        else:
            # Assume the next nodes will have a draw and update method
            self.call_draw_method = self.call_update_method = True

    def generate_grid(self, initial_nodes_gen):
        for i, (inst_class, *args, kwargs) in enumerate(initial_nodes_gen):
            self.nodes.append(inst_class(*args, **kwargs))

    def update(self):
        if self.call_update_method:
            for tile in self.nodes:
                tile.update()

    def draw(self, surface):
        if self.call_draw_method:
            for tile in self.nodes:
                tile.draw()

        if self._visible and self.dirty > 0:
            self.image.fill(self.style.get("background"))
            for i, tile in enumerate(self.nodes):
                if hasattr(tile, 'image'):
                    tile.image.blit(self.image, self.index_to_position(i))

    def index_to_position(self, index):
        spacing = self.style.get('spacing', 20)
        if self.horizontal:
            return index*spacing, 0, spacing, self.transform.height
        else:
            return 0, index*spacing, self.transform.width, spacing

    def position_to_index(self, position_x_y: (float, float)) -> int:
        spacing = self.style.get('spacing', 20)
        if self.horizontal:
            return position_x_y[0] // spacing
        else:
            return position_x_y[1] // spacing

    def add_child(self, child):
        super().add_child(child)
        self.dirty = 1

    def remove_child(self, child):
        super().remove_child(child)
        self.dirty = 1

class SpriteGrid(Grid):
    """A container for equally spaced UI items that draws them onto a buffer."""
    def __init__(self, node_props, group, initial_nodes_gen=None, horizontal=False, **kwargs):
        super().__init__(node_props, group, initial_nodes_gen, horizontal, **kwargs)
        self.grid_group = pygame.sprite.Group()
        self.grid_group.add(self.nodes)

    def generate_grid(self, initial_nodes_gen):
        for i, (inst_class, *args, kwargs) in enumerate(initial_nodes_gen):
            node_props = NodeProperties(self, *self.index_to_position(i))
            inst_class(node_props, *args, **kwargs)

    def draw(self, surface):
        if self.call_draw_method:
            for tile in self.nodes:
                tile.draw(surface)

        if self._visible and self.dirty > 0:
            self.image.fill(self.style.get("background"))
            wr = self.world_rect()
            for i, tile in enumerate(self.nodes):
                correct_rect = Rect(*self.index_to_position(i)).move(-wr.x, -wr.y)
                if tile.transform.rect() != correct_rect:
                    tile.transform.position = correct_rect.topleft
                    tile.transform.size = correct_rect.size
                    tile.dirty = True
            self.grid_group.draw(self.image)

        if self._visible and self.dirty > 0:
            for i, tile in enumerate(self.nodes):
                if hasattr(tile, 'image'):
                    self.image.blit(tile.image, self.index_to_position(i))
