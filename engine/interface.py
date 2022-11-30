import pygame
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP, KEYDOWN, KEYUP
from math import sqrt

from .node import SpriteNode, NodeProps
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


class ListLayout(SpriteNode):
    """A container that displays a list of tiles in a horizontal row (if horizontal)
    or vertical column, ignoring position attributes. The tiles are
    spaced apart adjacently according to their transform.height (if horizontal)
    or transform.width. The image attribute is used to draw the tiles.
    Change the attributes used by overriding ListLayout.get_tile_spacing(tile)
    or ListLayout.get_tile_image(tile) respectively.

    The draw() or update() methods of tiles are called if they exist.
    Add tiles by passing a generator or iterable to the grid, either on initialisation,
    or by calling ListLayout.append_tiles(tiles). Or modify ListLayout.tiles,
    then call ListLayout.prepare_flags() with no arguments.
    Takes the keyword argument background, or a style object, specifying the
    background color. This may be set to None for a transparent background.
    """
    def __init__(self, node_props, groups, horizontal=False, tiles=None, **kwargs):
        super().__init__(node_props, groups)
        self.style = Style.from_kwargs(kwargs)
        self.scroll_pixels = 0
        self.tiles = []
        self.horizontal = horizontal
        self.use_update_method = self.use_draw_method = self.use_image = False
        self.append_tiles(tiles)

    def append_tiles(self, tiles=None):
        """Sets use_update_method and use_draw_method. If an iterable/generator
        tiles is supplied, adds each of its elements to the list layout. Format:
        (class_name, *args, {**kwargs}) -> class_name(*args, **kwargs)
        """
        if tiles is not None:
            for (inst_class, *args, kwargs) in tiles:
                self.tiles.append(inst_class(*args, **kwargs))
        if self.tiles:
            self.prepare_flags()

    def prepare_flags(self):
        # Check the first tile for methods and assume the rest are identical to it
        t_node = self.tiles[0]
        self.use_update_method = hasattr(t_node, 'update') and callable(t_node.update)
        self.use_draw_method = hasattr(t_node, 'draw') and callable(t_node.draw)
        self.use_image = isinstance(self.get_tile_image(t_node), pygame.Surface)

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
            if self.use_image:
                for i, position in zip(indexes, self.tile_positions(indexes.start)):
                    self.image.blit(self.get_tile_image(self.tiles[i]), position)

    def pop_tile(self, index):
        if self.dirty < 2:
            self.dirty = 1
        return self.tiles.pop(index)

    def clear_tiles(self):
        if self.dirty < 2:
            self.dirty = 1
        self.tiles.clear()

    def indexes_in_view(self):
        """Returns a range() for the indexes of tiles visible when drawn."""
        max_forward = self.transform.height if self.horizontal else self.transform.width
        i = forward = 0
        while forward < self.scroll_pixels:
            forward += self.get_tile_spacing(self.tiles[i])
            i += 1
        start = i
        while forward < max_forward + self.scroll_pixels and i < len(self.tiles):
            forward += self.get_tile_spacing(self.tiles[i])
            i += 1
        # Adds 1 to end to include the partially visible next tile
        return range(start, min(i + 1, len(self.tiles)))

    def get_tile_spacing(self, tile):
        if self.horizontal:
            return tile.transform.width
        else:
            return tile.transform.height

    @staticmethod
    def get_tile_image(tile):
        return getattr(tile, 'image', None)

    def tile_rects(self, start_index=0):
        raise NotImplemented()

    def tile_positions(self, start_index=0):
        """Yields the positions for tiles starting from the start index."""
        # Find the position of the tile at the start index
        position = list(self.index_to_position(start_index))
        index_x_or_y = not self.horizontal
        # Loop yielding the next position on each iteration (sum each spacing)
        for i in range(start_index, len(self.tiles)):
            yield position
            position[index_x_or_y] += self.get_tile_spacing(self.tiles[i])

    def index_to_forward(self, index: int):
        """A forward is the number of pixels along in the orientation direction."""
        forward = -self.scroll_pixels
        for i in range(min(index, len(self.tiles))):
            forward += self.get_tile_spacing(self.tiles[i])
        return forward

    def forward_to_position(self, forward_pixels=0) -> tuple:
        """A forward is the number of pixels along in the orientation direction."""
        if self.horizontal:
            return forward_pixels, 0
        else:
            return 0, forward_pixels

    def index_to_position(self, index: int) -> tuple:
        return self.forward_to_position(self.index_to_forward(index))

    def forward_to_rect(self, forward_pixels=0, spacing=0):
        """A forward is the number of pixels along in the orientation direction."""
        if self.horizontal:
            return pygame.Rect(forward_pixels, 0, spacing, self.transform.height)
        else:
            return pygame.Rect(0, forward_pixels, self.transform.width, spacing)

    def index_to_rect(self, index: int):
        return self.forward_to_rect(self.index_to_forward(index),
                                    self.get_tile_spacing(self.tiles[index]))

    def forward_to_index(self, forward: float) -> int:
        """A forward is the number of pixels along in the orientation direction."""
        forward += self.scroll_pixels
        for i, tile in enumerate(self.tiles):
            forward -= self.get_tile_spacing(tile)
            if forward < 0:
                return i
        return len(self.tiles)

    def position_to_index(self, position_x_y: (float, float)) -> int:
        return self.forward_to_index(position_x_y[not self.horizontal])

    @property
    def scroll_limits(self):
        return 0, self.index_to_forward(len(self.tiles)) + self.scroll_pixels

class UniformListLayout(ListLayout):
    """A container that draws a list of tiles, ignoring their position attributes,
    in a horizontal row (if horizontal==True) or vertical column.
    The spacing of tiles is fixed which makes this class more efficient.
    The draw() or update() methods of tiles are called if they exist, and the
    image attribute is used to draw the tiles.
    Add tiles by passing a generator to the grid, either on initialisation, or by
    calling UniformListLayout.prepare_flags(tile_generator). Alternatively, modify the
    tiles list, then call UniformListLayout.prepare_flags() with no arguments.
    Takes the keyword argument background, or a style object, specifying the
    background color. This may be set to None for a transparent background.
    """
    def __init__(self, node_props, groups, horizontal=False, spacing=20, tiles=None, **kwargs):
        super().__init__(node_props, groups, horizontal, tiles, **kwargs)
        self.style = Style.from_kwargs(kwargs)
        self.spacing = spacing

    def indexes_in_view(self):
        max_forward = self.transform.height if self.horizontal else self.transform.width
        start = self.scroll_pixels // self.spacing
        end = (self.scroll_pixels + max_forward) // self.spacing
        # Adds 1 to end to include the partially visible next tile
        return range(int(start), min(int(end) + 1, len(self.tiles)))

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

    def index_to_forward(self, index: int):
        # This method is folded into other methods for efficiency.
        return index * self.spacing - self.scroll_pixels

    def forward_to_position(self, forward_pixels=0) -> tuple:
        if self.horizontal:
            return forward_pixels, 0
        else:
            return 0, forward_pixels

    def index_to_position(self, index: int) -> tuple:
        return self.forward_to_position(index * self.spacing - self.scroll_pixels)

    def forward_to_rect(self, forward_pixels=0, spacing=0):
        return super().forward_to_rect(forward_pixels, spacing or self.spacing)

    def index_to_rect(self, index: int):
        return self.forward_to_rect(index * self.spacing - self.scroll_pixels)

    def forward_to_index(self, forward: float) -> int:
        return int((forward + self.scroll_pixels) // self.spacing)  # // can return float

    def position_to_index(self, position_x_y: (float, float)) -> int:
        # // can return float
        return int((position_x_y[not self.horizontal] + self.scroll_pixels) // self.spacing)

    @property
    def scroll_limits(self):
        return 0, max(0, len(self.tiles) - 1) * self.spacing

class SpriteListLayout(ListLayout):
    """A container for adjacent SpriteNodes that draws them onto a buffer,
    in a horizontal row (if horizontal==True) or vertical column.
    The draw() or update() methods of nodes are called if they exist.
    Add tiles by passing a generator or iterable to the grid, either on initialisation,
    or by calling ListLayout.append_tiles(tiles). Or modify ListLayout.tiles,
    then call ListLayout.prepare_flags() with no arguments.
    The nodes are assigned to its Group rather than the scene LayeredDirty.
    Takes the keyword argument background, or a style object, specifying the
    background color. This may be set to None for a transparent background.
    """
    is_origin = 'SpriteList'

    def __init__(self, node_props, groups, tiles=None, horizontal=False, **kwargs):
        self.tiles_group = pygame.sprite.LayeredDirty()
        super().__init__(node_props, groups, horizontal, tiles=tiles, **kwargs)
        if self.style.get('background') is not None:
            self.image.fill(self.style.get('background'))
        else:
            self.image.fill(BACKGROUND_TRANSPARENT)
        self.tiles_group.clear(self.image, self.image.copy())

    def append_tiles(self, tiles=None):
        """Sets use_update_method and use_draw_method.
        If a tile_generator is supplied, adds each of its items to the grid.
        (class_name, spacing, *args, {**kwargs})
        -> class_name(node_props, tiles_group, *args, **kwargs)
        """
        self.tiles = self.nodes
        if tiles is not None:
            if self.tiles:
                if self.horizontal:
                    forward = self.tiles[-1].transform.x
                else:
                    forward = self.tiles[-1].transform.y
            else:
                forward = 0
            for inst_class, spacing, *args, kwargs in tiles:
                node_props = NodeProps(self, *self.forward_to_rect(forward, spacing))
                inst_class(node_props, self.tiles_group, *args, **kwargs)
                forward += spacing
        if self.tiles:
            self.prepare_flags()

    def pop_tile(self, index):
        if self.dirty < 2:
            self.dirty = 1
        tile = self.tiles[index]
        tile.remove()
        return tile

    def clear_tiles(self):
        if self.dirty < 2:
            self.dirty = 1
        while self.tiles:
            self.tiles[0].remove()

    def draw(self):
        if self._visible:
            if self.dirty > 0 or self.tiles_group.draw(self.image):
                self._position_tiles()
                if self.dirty < 2:
                    self.dirty = 1
                if self.use_draw_method:
                    for node in self.nodes:
                        node.draw()

    # These method differs from the base method as it does not cascade to children
    def _set_rect_position(self, x, y):
        self.rect.x, self.rect.y = self.transform.rect_position(x, y)
        if self.dirty < 2:
            self.dirty = 1

    def _position_tiles(self):
        for node, correct_position in zip(self.nodes, self.tile_positions()):
            if list(node.transform.position) != correct_position:
                node.transform.position = correct_position
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
