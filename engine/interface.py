import pygame
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP, KEYDOWN, KEYUP
from math import sqrt

from .base_node import SpriteNode, NodeProperties
import engine.text as text

MOUSE_EVENTS = (MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP)
KEYBOARD_EVENTS = (KEYDOWN, KEYUP)
MOUSE_AND_KEYBOARD_EVENTS = MOUSE_EVENTS + KEYBOARD_EVENTS

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
    """Saturate or desaturate a single rgb value by the given multiplier, where
    0: grayscale, 0-1: desaturated, 1: identical, >1: further saturated;
    negative values result in the complementary color."""
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
        self.dict = {'color': COLOR_DEFAULT, 'background': BACKGROUND_DEFAULT,
                     'font': text.FONT_DEFAULT}
        self.dict.update(kwargs)

    def __repr__(self) -> str:
        return str(self.dict)

    @classmethod
    def from_kwargs(cls, kwargs):
        if kwargs.get('style', False):
            style = kwargs.pop('style')
            if not kwargs:
                return style
            else:
                style_copy = cls(**style.dict)
                style_copy.dict.update(kwargs)
                return style_copy
        else:
            return cls(**kwargs)

    def get(self, name: str, default=NO_VALUE):
        if name in self.dict:
            return self.dict[name]
        elif name.count('_') == 1:
            base_name, modifier = name.split('_', 1)
            color = self.get(base_name)
            if isinstance(color, pygame.Color) or type(color) == tuple:
                if modifier == 'hovered' and base_name != 'color':
                    color = modify_color(color, -5)
                elif modifier == 'selected' and base_name != 'color':
                    color = modify_color(color, 5)
                elif modifier == 'blocked':
                    color = modify_color(saturate_color(color, -10), 0.25)
            return color
        if default != NO_VALUE:
            return default
        raise KeyError(f'Not a key and not a modifier of a key: {name} in {self.dict}')

    def get_by_state(self, base_name, state):
        return self.get(base_name + State.modifier[state])

class State:
    idle, hovered, selected, stopped = range(4)
    modifier = '', '_hovered', '_selected', '_stopped'


class Button(SpriteNode):
    """A button. The keyword arguments color and background change the appearance.
    The argument callback is a function taking no parameters. It is called on click.
    To add parameters to the callback or take additional styles,
    it is recommended to inherit from this class.
    """
    event_handler = MOUSE_EVENTS

    def __init__(self, node_props, group, message='', callback=None, **kwargs):
        super().__init__(node_props, group)
        self.style = Style.from_kwargs(kwargs)

        self.callback = callback
        self.message = message

        self.state = State.idle
        self.pre_render_text()

    def pre_render_text(self):
        return text.render(self.message, color=self.style.get('color'), save_sprite=True)

    def event(self, event):
        """Pass each pygame mouse event to the button,
        so it can update (i.e. if hovered or clicked).
        For speed, only call if `event.type in MOUSE_EVENTS`.
        """
        if self.state == State.stopped or not self._visible:
            return
        last_state = self.state
        mouse_over = self.rect.collidepoint(event.pos)
        # Only react to a click on mouse-up (helps avoid an accidental click).
        if self.state == State.selected and event.type == MOUSEBUTTONUP:
            if mouse_over and self.callback:
                self.on_click()
            self.state = State.idle

        if mouse_over:
            if event.type == MOUSEBUTTONDOWN:
                self.state = State.selected
            elif self.state == State.idle:
                self.state = State.hovered
        elif self.state == State.hovered:
            self.state = State.idle

        if last_state != self.state:
            self.dirty = 1

    def on_click(self):
        self.callback()

    def draw(self):
        super().draw()
        if self._visible and self.dirty > 0:
            if self.style.get('image', False):
                self.image.blit(self.style.get('image'), (0, 0))
            else:
                self.image.fill(self.style.get_by_state('background', self.state))

            if self.message:
                position = (self.transform.width / 2, self.transform.height / 2)
                color = self.style.get_by_state('color', self.state)
                text.draw(self.image, self.message, position,
                          font=self.style.get('font', text.FONT_DEFAULT), color=color, justify=True)

class Toggle(Button):
    def __init__(self, node_props, group, message='', callback=None, checked=False, **kwargs):
        super().__init__(node_props, group, message, callback, **kwargs)
        self.checked = checked

    def on_click(self):
        self.checked = not self.checked
        self.callback(self.checked)


class TextEntry(SpriteNode):
    """A single line rectangular box that can be typed in.
    The keyword arguments color and background change the appearance.
    The arguments enter_callback(text) and edit_callback(text) are functions
    called when editing is completed and when the text changes, respectively.
    To add more parameters to the callback or take additional styles,
    it is recommended to inherit from this class.
    Set allow_characters = '1234' or ['1', '2'] to only allow those characters.
    """
    event_handler = MOUSE_AND_KEYBOARD_EVENTS

    def __init__(self, node_props, group, default_text='', enter_callback=None,
                 edit_callback=None, allow_characters=None, **kwargs):
        super().__init__(node_props, group)
        self.style = Style.from_kwargs(kwargs)

        self.enter_callback = enter_callback
        self.edit_callback = edit_callback

        self.state = State.idle
        self.text = default_text
        self.allow_characters = allow_characters

    def on_enter(self):
        if self.enter_callback is not None:
            self.enter_callback(self.text)
        self.state = State.idle

    def on_edit(self):
        if self.edit_callback is not None:
            self.edit_callback(self.text)

    def event(self, event):
        if self.state == State.stopped or not self._visible:
            return

        last_state = self.state
        last_text = self.text

        if event.type in MOUSE_EVENTS:
            mouse_over = self.rect.collidepoint(event.pos)

            if mouse_over:
                if event.type == MOUSEBUTTONDOWN:
                    self.state = State.selected
                elif self.state == State.idle:
                    self.state = State.hovered
            elif self.state == State.hovered or event.type == MOUSEBUTTONDOWN:
                self.state = State.idle

        elif self.state == State.selected and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_TAB):
                self.on_enter()
            elif event.mod & pygame.KMOD_CTRL:
                if event.key == pygame.K_BACKSPACE:
                    self.text = ''
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if pygame.version.vernum[0] >= 2:
                    key = event.unicode
                else:
                    key = chr(event.key) if 0x20 <= event.key <= 0x7e else ''
                if key and (self.allow_characters is None or key in self.allow_characters):
                    self.text += key

        if last_state != self.state or last_text != self.text:
            self.dirty = 1
        if last_text != self.text:
            self.on_edit()

    def draw(self):
        super().draw()
        if self._visible and self.dirty > 0:
            background = self.style.get_by_state('background', self.state)
            self.image.fill(background)
            if self.state == State.selected:
                draw_message = self.text + '|'
            else:
                draw_message = self.text
            text.draw(self.image, draw_message, (4, self.transform.height / 2),
                      font=self.style.get('font'),
                      color=self.style.get('color'), justify=(False, True))


class Grid(SpriteNode):
    """A container for equally spaced tiles that draws them onto a buffer.
    The default grid ignores the position/size attributes on each tile, if any,
    instead drawing them in a vertical or horizontal (if horizontal=True) grid.
    The argument initial_nodes_gen specifies the initial tiles as a list of
    (class, *args, {**kwargs}) -> class(*args, **kwargs). Each item is one tile.
    If tiles have draw() or update() methods, they will be called only if
    initial tiles of its type are supplied. Alternatively, set the properties
    self.use_draw_method or self.use_update_method = True by subclassing Grid.
    The keyword arguments spacing and background change the appearance.
    """
    is_origin = 0

    def __init__(self, node_props, group, initial_nodes_gen=None, horizontal=False, spacing=20, **kwargs):
        super().__init__(node_props, group)
        self.style = Style.from_kwargs(kwargs)
        self.spacing = spacing
        self.scroll_pixels = 0

        self.horizontal = horizontal
        if initial_nodes_gen is not None:
            self.populate_grid(initial_nodes_gen)
            # Check the first node for methods and assume they are all identical
            t_node = self.nodes[0]
            self.use_update_method = hasattr(t_node, 'update') and callable(t_node.update)
            self.use_draw_method = hasattr(t_node, 'draw') and callable(t_node.draw)
        else:
            self.use_update_method = self.use_draw_method = False

    def populate_grid(self, initial_nodes_gen):
        for (inst_class, *args, kwargs) in initial_nodes_gen:
            self.nodes.append(inst_class(*args, **kwargs))

    def update(self):
        if self.use_update_method:
            for tile in self.nodes:
                tile.update()

    def draw(self):
        if self._visible and self.dirty > 0:
            if self.use_draw_method:
                for tile in self.nodes:
                    tile.draw()

            self.image.fill(self.style.get('background'))
            for tile, position in zip(self.nodes, self.tile_positions()):
                if hasattr(tile, 'image'):
                    self.image.blit(tile.image, position)

    def tile_rects(self):
        tile_rect = self.forward_to_rect(-self.scroll_pixels)
        move_x, move_y = self.forward_to_position(self.spacing)
        while True:
            yield tile_rect
            tile_rect.move_ip(move_x, move_y)

    def tile_positions(self):
        position = list(self.forward_to_position(-self.scroll_pixels))
        index_x_or_y = not self.horizontal
        while True:
            yield position
            position[index_x_or_y] += self.spacing

    def forward_to_position(self, forward_pixels=0):
        if self.horizontal:
            return forward_pixels, 0
        else:
            return 0, forward_pixels

    def index_to_position(self, index):
        return self.forward_to_position(index * self.spacing)

    def forward_to_rect(self, forward_pixels=0):
        if self.horizontal:
            return pygame.Rect(forward_pixels, 0, self.spacing, self.transform.height)
        else:
            return pygame.Rect(0, forward_pixels, self.transform.width, self.spacing)

    def index_to_rect(self, index):
        return self.forward_to_rect(index * self.spacing)

    def position_to_index(self, position_x_y: (float, float)) -> int:
        return position_x_y[not self.horizontal] // self.spacing

    def add_child(self, child):
        self.nodes.append(child)
        self.dirty = 1

    def remove_at_index(self, index):
        self.dirty = 1
        return self.nodes.pop(index)

    # These methods differ from the base methods - do not cascade to children
    def cascade_move_rect(self, dx, dy):
        self.rect.move_ip(dx, dy)

    def cascade_set_visible(self, set_visible):
        self.visible = set_visible and self.enabled

# TODO: consider that SpriteGrid is not very useful in its current state
# A layout that considers each item's height, however, could be useful
class SpriteGrid(Grid):
    """A container for equally spaced SpriteNodes that draws them onto a buffer.
    By default, the update() and draw() methods are called. To avoid this, set
    self.use_update_method and self.use_draw_method = False by subclassing SpriteGrid.
    The argument initial_nodes_gen specifies the initial sprites as a list of
    (class, *args, {**kwargs}) -> class(node_props, grid_group, *args, **kwargs).
    Each item is one tile and the group is a Group rather than LayeredDirty.
    """
    def __init__(self, node_props, group, initial_nodes_gen=None, horizontal=False, **kwargs):
        self.grid_group = pygame.sprite.Group()
        super().__init__(node_props, group, initial_nodes_gen, horizontal, **kwargs)
        self.use_update_method = self.use_draw_method = True

    def populate_grid(self, initial_nodes_gen):
        for (inst_class, *args, kwargs), rect in zip(initial_nodes_gen, self.tile_rects()):
            node_props = NodeProperties(self, *rect)
            inst_class(node_props, self.grid_group, *args, **kwargs)

    def draw(self):
        if self._visible and self.dirty > 0:
            if self.use_draw_method:
                for tile in self.nodes:
                    tile.draw()

            self.image.fill(self.style.get('background'))
            for tile, correct_rect in zip(self.nodes, self.tile_rects()):
                if tile.transform.rect() != correct_rect:
                    tile.transform.position = correct_rect.topleft
                    tile.transform.size = correct_rect.size
            self.grid_group.draw(self.image)

    def add_child(self, child):
        SpriteNode.add_child(self, child)
        self.dirty = 1

    # Undo the overrides in Grid - do cascade transform changes to children
    def cascade_move_rect(self, dx, dy):
        SpriteNode.cascade_move_rect(self, dx, dy)

    def cascade_set_visible(self, set_visible):
        SpriteNode.cascade_set_visible(self, set_visible)

