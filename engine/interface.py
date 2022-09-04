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
BACKGROUND_TRANSPARENT = (0, 0, 0, 0)

def brighten_color_component(color_component, brightness):
    """Lighten or darken a single rgb value by the perceived brightness percentage."""
    color_component = round(max(sqrt(color_component) + brightness/6.25, 0)**2)
    color_component = min(max(color_component, 0), 255)  # clamp value between 0 and 255
    return color_component

def brighten_color(color, brightness: float):
    """Lighten or darken an (r, g, b) colour by the perceived brightness percentage."""
    return tuple(brighten_color_component(r_g_b, brightness) for r_g_b in color)

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
    mean = sum(r_g_b for r_g_b in color[:3]) / 3
    return tuple(saturate_color_component(r_g_b, mean, saturation) for r_g_b in color)

class State:
    idle, hovered, selected, locked = range(4)

class Style:
    """Behaves like a dictionary, usually used to hold graphical attributes.
    Interface classes may use a Style and/or keyword arguments, for example:
      Button(..., color=(96, 96, 0), color_two=(80, 0, 0))
    May be replaced by:
      my_style = Style(color=(96, 96, 0))
      Button(..., style=my_style, color_two=(80, 0, 0))

    Every Style includes default values for 'color', 'background' and 'font'.
    Keys of the form 'base_first_second' default to 'base_first' then 'base'.
    The modifiers 'hovered', 'selected', 'locked' are special cases of this.
    """
    state_modifier = '', '_hovered', '_selected', '_locked'
    NO_VALUE = object()

    def __init__(self, **kwargs):
        self.dict = {'color': COLOR_DEFAULT, 'background': BACKGROUND_DEFAULT,
                     'font': text.FONT_DEFAULT}
        self.dict.update(kwargs)

    def __repr__(self) -> str:
        return f'Style({str(self.dict)[1:-1].replace(": ", "=")})'

    @classmethod
    def from_kwargs(cls, kwargs):
        if 'style' not in kwargs:
            return cls(**kwargs)

        style = kwargs.pop('style')
        if kwargs:
            style_copy = cls(**style.dict)
            style_copy.dict.update(kwargs)
            return style_copy
        else:
            return style

    def get(self, name: str, default=None):
        if name in self.dict:
            return self.dict[name]
        elif '_' in name:
            base_name, modifier = name.rsplit('_', 1)
            value = self.get(base_name, default)
            if isinstance(value, pygame.Color) or isinstance(value, tuple):
                value = self.modified_color(value, modifier, base_name)
            return value
        elif default is not Style.NO_VALUE:
            return default
        raise KeyError(f'Not a key and not a modifier of a key: {name} in {self.dict}')

    def __index__(self, name: str):
        return self.get(name, Style.NO_VALUE)

    def get_by_state(self, base_name: str, state: int):
        return self.get(base_name + self.state_modifier[state], Style.NO_VALUE)

    @staticmethod
    def modified_color(color, modifier, base_name):
        if modifier == 'hovered' and base_name != 'color':
            return brighten_color(color, -5)
        elif modifier == 'selected' and base_name != 'color':
            return brighten_color(color, 5)
        elif modifier == 'locked':
            return brighten_color(saturate_color(color, 0.25), -10)
        return color

class Button(SpriteNode):
    """A rectangular button. The argument callback is a function taking
    no parameters called on click.
    Takes the keyword arguments color, background and font, or a style object.
    Subclass to add parameters to the callback or customise supported styles.
    """
    event_handler = MOUSE_EVENTS

    def __init__(self, node_props, groups, message='', callback=None, **kwargs):
        self.style = Style.from_kwargs(kwargs)
        super().__init__(node_props, groups, fill_color=self.style.get('background'))

        self.callback = callback
        self.message = message

        self.state = State.idle
        self.cache_text_render()

    def cache_text_render(self):
        return text.render(self.message, self.style.get('font'),
                           self.style.get('color'), save_sprite=True)

    def event(self, event):
        """Pass each pygame mouse event to the button,
        so it can update (i.e. if hovered or clicked).
        For speed, only call if `event.type in MOUSE_EVENTS`.
        """
        if self.state == State.locked or not self._visible:
            return

        last_state = self.state
        mouse_over = self.rect.collidepoint(event.pos)
        # React to clicks (only on mouse-up events to ignore accidental clicks)
        if last_state == State.selected and event.type == MOUSEBUTTONUP and event.button == 1:
            if mouse_over:
                self.on_click()
            self.state = State.idle
        # Update state based on mouse motion and mouse down events
        if mouse_over:
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                self.state = State.selected
            elif self.state == State.idle:
                self.state = State.hovered
        elif self.state == State.hovered:
            self.state = State.idle

        if last_state != self.state:
            self.dirty = 1

    def on_click(self):
        if callable(self.callback):
            self.callback()

    def draw(self):
        super().draw()
        if self._visible and self.dirty > 0:
            self.image.fill(self.switch_style('background'))
            if self.style.get('image'):
                image_rect = self.style.get('image').get_rect()
                offset = (self.transform.height - image_rect.height) // 2
                self.image.blit(self.switch_style('image'), (self.style.get('imagex', offset), offset))
            if self.message:
                position = (self.transform.width / 2, self.transform.height / 2)
                color = self.switch_style('color')
                text.draw(self.image, self.message, position, color=color,
                          font=self.switch_style('font'), justify=True)

    def switch_style(self, base_name):
        return self.style.get_by_state(base_name, self.state)

class Toggle(Button):
    """Inherits from Button. The boolean Toggle.checked holds if the toggle is
    checked and when clicked, it is flipped and passed to the callback.
    Takes also 'checked' and 'unchecked' modifiers of the colour, background
    and image styles, for example color_checked_hovered=(80, 0, 0)."""
    def __init__(self, node_props, groups, message='', callback=None, checked=False, **kwargs):
        super().__init__(node_props, groups, message, callback, **kwargs)
        self.checked = checked

    def on_click(self):
        self.checked = not self.checked
        if callable(self.callback):
            self.callback(self.checked)

    def switch_style(self, base_name):
        checked_string = '_checked' if self.checked else '_unchecked'
        return self.style.get_by_state(base_name + checked_string, self.state)

class TextEntry(SpriteNode):
    """A single line rectangular box that can be typed in.
    The arguments enter_callback(text) and edit_callback(text) are functions
    called when editing is completed and when the text changes, respectively.
    Takes the keyword arguments color, background and font, or a style object.
    Subclass to add parameters to the callback or customise supported styles.
    Set allow_characters = '1234' or ['1', '2'] to only allow those characters.
    """
    event_handler = MOUSE_AND_KEYBOARD_EVENTS

    def __init__(self, node_props, groups, default_text='', enter_callback=None,
                 edit_callback=None, allow_characters=None, cursor='|', **kwargs):
        super().__init__(node_props, groups)
        self.style = Style.from_kwargs(kwargs)

        self.enter_callback = enter_callback
        self.edit_callback = edit_callback
        self.state = State.idle
        self.text = default_text
        self.allow_characters = allow_characters
        self.cursor_text = cursor

    def on_enter(self):
        """Called when editing is completed. Must reset state to State.idle."""
        if callable(self.enter_callback):
            self.enter_callback(self.text)
        self.state = State.idle

    def on_edit(self):
        if callable(self.edit_callback):
            self.edit_callback(self.text)

    def event(self, event):
        if self.state == State.locked or not self._visible:
            return

        last_state = self.state
        last_text = self.text
        # Update state based on mouse motion and mouse down events
        if event.type in MOUSE_EVENTS:
            if self.rect.collidepoint(event.pos):
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    self.state = State.selected
                elif last_state == State.idle:
                    self.state = State.hovered
            elif last_state == State.selected and event.type == MOUSEBUTTONUP and event.button == 1:
                self.on_enter()
            elif last_state == State.hovered:
                self.state = State.idle

        # Modify text using keyboard events
        elif last_state == State.selected and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_TAB):
                self.on_enter()
            elif event.mod & pygame.KMOD_CTRL:
                if event.key == pygame.K_BACKSPACE:
                    self.text = ''
            elif event.key == pygame.K_BACKSPACE:
                if self.text != '':
                    self.text = self.text[:-1]
            else:
                if pygame.version.vernum[0] >= 2:
                    key = event.unicode
                else:  # rudimentary support for pygame 1
                    key = chr(event.key) if 0x20 <= event.key <= 0x7e else ''
                    if key.isalpha() and event.mod & (pygame.KMOD_SHIFT | pygame.KMOD_CAPS):
                        key = chr(event.key - 0x20)  # use capitalised key
                if key and (self.allow_characters is None or key in self.allow_characters):
                    self.text += key

        if last_state != self.state or last_text != self.text:
            self.dirty = 1
        if last_text != self.text:
            self.on_edit()

    def draw(self):
        super().draw()
        if self._visible and self.dirty > 0:
            background = self.switch_style('background')
            self.image.fill(background)
            if self.state == State.selected:
                draw_message = self.text + self.cursor_text
            else:
                draw_message = self.text
            text.draw(self.image, draw_message, (text.BOX_PADDING, self.transform.height / 2),
                      color=self.switch_style('color'), font=self.style.get('font'),
                      justify=(False, True))

    def switch_style(self, base_name):
        return self.style.get_by_state(base_name, self.state)


class GridList(SpriteNode):
    """A container for equally spaced tiles that draws them onto a buffer.
    The default grid ignores the position/size attributes on each tile, if any,
    instead drawing them in a horizontal (if horizontal=True) or vertical grid.
    The draw() or update() methods of tiles are called if they exist, and the
    image attribute is used to draw the tiles.
    Add tiles by passing a generator to the grid, either on initialisation, or
    calling GridList.prepare_grid(tile_generator). An equivalent is modifying
    the tiles list, then calling GridList.prepare_grid().
    Takes the keyword argument background, or a style object, specifying the
    background color. This may be set to None for a transparent background.
    """
    def __init__(self, node_props, groups, horizontal=False, spacing=20, tile_generator=None, **kwargs):
        super().__init__(node_props, groups)
        self.style = Style.from_kwargs(kwargs)
        self.spacing = spacing
        self.scroll_pixels = 0
        self.tiles = []

        self.horizontal = horizontal
        self.use_update_method = self.use_draw_method = False
        self.prepare_grid(tile_generator)

    def prepare_grid(self, tile_generator=None):
        """Sets use_update_method and use_draw_method.
        If a tile_generator is supplied, adds each of its items to the grid.
        (class_name, *args, {**kwargs}) -> class_name(*args, **kwargs)
        """
        if tile_generator is not None:
            for (inst_class, *args, kwargs) in tile_generator:
                self.tiles.append(inst_class(*args, **kwargs))
        if self.tiles:
            # Check the first tile for methods and assume the rest are identical to it
            t_node = self.tiles[0]
            self.use_update_method = hasattr(t_node, 'update') and callable(t_node.update)
            self.use_draw_method = hasattr(t_node, 'draw') and callable(t_node.draw)

    def update(self):
        super().update()
        if self.use_update_method:
            for tile in self.tiles:
                tile.update()

    def draw(self):
        super().draw()
        if self._visible and self.dirty > 0:
            if self.style.get('background') is not None:
                self.image.fill(self.style.get('background'))
            else:
                self.image.fill(BACKGROUND_TRANSPARENT)

            indexes = self.indexes_in_view()
            if self.use_draw_method:
                for i in indexes:
                    self.tiles[i].draw()
            # Blit each of the tiles' images to the grid in place
            for i, position in zip(indexes, self.tile_positions(indexes.start)):
                if hasattr(self.tiles[i], 'image'):
                    self.image.blit(self.tiles[i].image, position)

    def indexes_in_view(self):
        start = self.scroll_pixels // self.spacing
        end = (self.scroll_pixels + self.transform.height) // self.spacing
        # Adds 1 to end to include the partially visible next tile
        return range(int(start), min(len(self.tiles), int(end) + 1))

    def tile_rects(self, start_index=0):
        """Yields the local Rects for tiles starting from the start index.
        This generator loops infinitely, so it must be used either
        with a break condition in a loop, or with parallel iteration:
          for tile, rect in zip(self.tiles, self.tile_rects(indexes.start)) ...
        """
        # Find the Rect of the tile at the start index
        tile_rect = self.index_to_rect(start_index)
        move_x, move_y = self.forward_to_position(self.spacing)
        # Loop infinitely yielding the next Rect on each iteration
        while True:
            yield tile_rect
            tile_rect.move_ip(move_x, move_y)  # translate by one tile's spacing

    def tile_positions(self, start_index=0):
        """Yields the positions for tiles starting from the start index.
        This generator loops infinitely, so it must be used either
        with a break condition in a loop, or with parallel iteration:
          for tile, position in zip(self.tiles, self.tile_positions(indexes.start)) ...
        """
        # Find the position of the tile at the start index
        position = list(self.index_to_position(start_index))
        index_x_or_y = not self.horizontal
        # Loop infinitely yielding the next position on each iteration
        while True:
            yield position
            position[index_x_or_y] += self.spacing  # translate by one tile's spacing

    def forward_to_position(self, forward_pixels=0) -> tuple:
        """A forward is the number of pixels along a list
        in the direction that it is orientated. Returns position."""
        if self.horizontal:
            return forward_pixels, 0
        else:
            return 0, forward_pixels

    def index_to_position(self, index) -> tuple:
        return self.forward_to_position(index * self.spacing - self.scroll_pixels)

    def forward_to_rect(self, forward_pixels=0):
        """A forward is the number of pixels along a list
        in the direction that it is orientated. Returns a Rect."""
        if self.horizontal:
            return pygame.Rect(forward_pixels, 0, self.spacing, self.transform.height)
        else:
            return pygame.Rect(0, forward_pixels, self.transform.width, self.spacing)

    def index_to_rect(self, index: int):
        return self.forward_to_rect(index * self.spacing - self.scroll_pixels)

    def forward_to_index(self, forward: float) -> int:
        """A forward is the number of pixels along a list
        in the direction that it is orientated. Returns an integer index."""
        return int((forward + self.scroll_pixels) // self.spacing)  # // can return float

    def position_to_index(self, position_x_y: (float, float)) -> int:
        # // can return float
        return int((position_x_y[not self.horizontal] + self.scroll_pixels) // self.spacing)

    def remove_tile_at_index(self, index):
        if self.dirty < 2:
            self.dirty = 1
        return self.tiles.pop(index)

    @property
    def scroll_limits(self):
        return 0, max(0, (len(self.tiles) - 1)) * self.spacing

# TODO: consider that SpriteList is not very useful in its current state
# A layout that considers each item's height, however, could be useful
class SpriteList(GridList):
    """A container for adjacent SpriteNodes that draws them onto a buffer,
    in a horizontal row (if horizontal=True) or vertical column.
    The draw() or update() methods of nodes are called if they exist.
    Add nodes by passing a generator to the grid, either on initialisation, or
      SpriteList.prepare_grid(tile_generator).
    The nodes are assigned to its Group rather than the scene LayeredDirty.
    Takes the keyword argument background, or a style object, specifying the
    background color. This may be set to None for a transparent background.
    """
    is_origin = 'SpriteList'

    def __init__(self, node_props, groups, tile_generator=None, horizontal=False, **kwargs):
        self.grid_group = pygame.sprite.Group()
        super().__init__(node_props, groups, horizontal, tile_generator=tile_generator, **kwargs)
        assert not self.tiles  # catch accidental use of tiles list
        self.tiles = self.nodes

    def prepare_grid(self, tile_generator=None):
        """Sets use_update_method and use_draw_method.
        If a tile_generator is supplied, adds each of its items to the grid.
        (class_name, *args, {**kwargs}) -> class_name(node_props, grid_group, *args, **kwargs)
        """
        if tile_generator is not None:
            for (inst_class, *args, kwargs), rect in zip(tile_generator, self.tile_rects()):
                node_props = NodeProperties(self, *rect)
                inst_class(node_props, self.grid_group, *args, **kwargs)
        if self.nodes:
            # Check the first tile for methods and assume the rest are identical to it
            t_node = self.nodes[0]
            self.use_update_method = hasattr(t_node, 'update') and callable(t_node.update)
            self.use_draw_method = hasattr(t_node, 'draw') and callable(t_node.draw)

    def draw(self):
        if self._visible and self.dirty > 0:
            if self.use_draw_method:
                for node in self.nodes:
                    node.draw()
            if self.style.get('background') is not None:
                self.image.fill(self.style.get('background'))
            else:
                self.image.fill(BACKGROUND_TRANSPARENT)
            for node, correct_rect in zip(self.nodes, self.tile_rects()):
                if node.transform.position != correct_rect.topleft:
                    node.transform.position = correct_rect.topleft
                if node.transform.size != correct_rect.size:
                    node.transform.size = correct_rect.size
            self.grid_group.draw(self.image)

    # These method differs from the base method as it does not cascade to children
    def _set_rect_position(self, x, y):
        self.rect.x, self.rect.y = self.transform.rect_position(x, y)
        if self.dirty < 2:
            self.dirty = 1

# TODO: horizontal scrolling
class Scrollbar(SpriteNode):
    event_handler = (pygame.MOUSEBUTTONDOWN, )

    def __init__(self, node_props, group, scroll_speed=12, **kwargs):
        super().__init__(node_props, group)
        self.style = Style.from_kwargs(kwargs)
        self.scroll_speed = scroll_speed
        if not hasattr(self.parent, 'scroll_pixels'):
            self.parent.scroll_pixels = 0
        if not hasattr(self.parent, 'scroll_limits'):
            self.parent.scroll_limits = None
        self.scroll_by(0)  # calculate and set the height
        self.state = State.idle
        self.CLICK_MARGIN_LEFT = 3

    def draw(self):
        if self._visible and self.dirty > 0:
            self.image.fill(self.style.get_by_state('color_scroll', self.state))

    def scroll_by(self, pixels):
        self.parent.scroll_pixels += pixels
        self.transform.x = self.parent.transform.width - self.transform.width

        if self.parent.scroll_limits is not None:
            min_scroll, max_scroll = self.parent.scroll_limits
            self.parent.scroll_pixels = min(max(
                self.parent.scroll_pixels, min_scroll), max_scroll)
            # Set scrollbar height to proportionately show the visible height
            full_height = max(1, self.parent.transform.height + max_scroll - min_scroll)
            start_bar = (self.parent.scroll_pixels - min_scroll) / full_height
            self.transform.y = start_bar * self.parent.transform.height
            self.transform.height = self.parent.transform.height ** 2 / full_height
            # Indicate if the scrollbar is usable
            if full_height > self.parent.transform.height:
                self.state = State.idle
            else:
                self.state = State.locked

        if self.parent.dirty < 2 and pixels != 0:
            self.parent.dirty = 1

    def scroll_to(self, pixels):
        self.scroll_by(pixels - self.parent.scroll_pixels)

    def event(self, event):
        # Collision check using parent rect for a larger scroll input area
        if self.parent.rect.collidepoint(event.pos):
            if event.button == 4:  # mouse scroll input
                self.scroll_by(-self.scroll_speed)
            elif event.button == 5:  # mouse scroll input
                self.scroll_by(self.scroll_speed)
            # Left click input on or slightly to the left of scrollbar
            elif event.button == 1 and self.rect.x - self.CLICK_MARGIN_LEFT < event.pos[0]:
                min_scroll, max_scroll = self.parent.scroll_limits
                # Scroll so scrollbar is centred across from click, within limits
                full_height = max(1, self.parent.transform.height + max_scroll - min_scroll)
                start_bar = event.pos[1] - self.transform.height // 2 - self.parent.rect.y
                self.scroll_to(start_bar*full_height/self.parent.transform.height + min_scroll)
