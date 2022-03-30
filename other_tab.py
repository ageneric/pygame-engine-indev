import pygame

import engine.text as text
from engine.base_node import Node, SpriteNode, NodeProperties, Anchor
from engine.interface import Style, TextEntry, Button, GridList, \
    MOUSE_EVENTS, brighten_color, State, Scrollbar

def string_color(name: str):
    """Generates an arbitrary bright colour from the first six characters."""
    key = map(ord, name.ljust(6, ' '))
    color = []
    for i in range(3):
        c = (16 * next(key) + next(key)) % 256  # use next two values as color
        color.append(c if c > 137 else 247)  # make dark colour channels bright
    return color

class TabHeading(SpriteNode):
    def __init__(self, node_props, group, message, fit=True, **kwargs):
        super().__init__(node_props, group)
        self.style = Style.from_kwargs(kwargs)
        self.message = message
        self.resize_to_fit = fit

    def draw(self):
        if self._visible and self.dirty > 0:
            style_get = self.style.get
            width = None if self.resize_to_fit else self.transform.width
            rect = text.box(self.image, self.message, (0, 0), height=style_get('tabsize'),
                            width=width, font=style_get('font'), color=style_get('color'),
                            box_color=brighten_color(style_get('background'), -3))
            if self.resize_to_fit and self.transform.size != rect.size:
                self.transform.size = rect.size  # resize to fit the text box
                self.draw()  # redraw at the new size (one recursion only)

class HelpTab(SpriteNode):
    _layer = 0
    TEXT_PATH = 'Assets/docs.md'

    def __init__(self, node_props, group, font_reading, **kwargs):
        super().__init__(node_props, group)
        self.style = Style.from_kwargs(kwargs)

        TabHeading(NodeProperties(self, 0, 0, self.transform.width, anchor_y=Anchor.bottom),
                   group, 'Help Documents', style=self.style)
        Scrollbar(NodeProperties(self, width=2), group, style=self.style)

        self.seek_to_page = 'Introduction'
        self.lines = []
        self.font_monospace = pygame.font.SysFont('Consolas, Courier New', 13)
        self.font_small = pygame.font.SysFont('Calibri', 12, italic=True)
        self.font_reading = font_reading
        self.scroll_pixels = 0
        self.scroll_limits = 0, 0

        button_hide_help = Button(NodeProperties(self, 119, -20, 50, 18), group, 'Close',
            self.parent.action_hide_help, style=self.style, background=(76, 36, 36))

        # Initialise buttons to access help pages
        x = 171
        pairs = ('Node', 'Node'), ('Scene', 'Scene'), ('Text', 'Text'), ('Sprite', 'SpriteNode')
        for name, key in pairs:
            Button(NodeProperties(self, x, -20, 45, 18), group, name,
                   lambda page=key: self.parent.action_show_help(page), style=self.style)
            x += 45 + 2

    def draw(self):
        super().draw()
        if self._visible and self.dirty > 0:
            self.image.fill(self.style.get('background'))
            current_y = self.draw_help_text()
            self.scroll_limits = 0, max(0, current_y - self.transform.height)

    def draw_help_text(self):
        # Iterate through lines and draw them to the image top to bottom
        current_y = 4
        color = self.style.get('color')
        for line in self.lines:
            if line == '':
                current_y += 8
                continue
            # Apply the font and style of the tag at line start
            elif line.startswith('`') and line.endswith('`'):
                current_y = self.scroll_wrap(line[2:-1], current_y, color, self.font_monospace)
            elif line.startswith('(') and line.endswith(')'):
                current_y = self.scroll_wrap(line[1:], current_y, font=self.font_small)
            else:
                current_y = self.scroll_wrap(line, current_y, color, self.font_reading)
        return current_y

    def open_page(self, page):
        self.seek_to_page = page
        try:
            with open(self.TEXT_PATH, 'r') as f:
                all_lines = [line.rstrip('\n') for line in f.readlines()]
        except OSError:
            print('Engine warning: Text help file could not be opened.')
            return
        # Copy the lines from the target '# heading' until the next
        start = end = 0
        for i, line in enumerate(all_lines):
            if line.lstrip('#').lstrip(' ') == self.seek_to_page:
                start = i
            if end <= start and line.startswith('#'):
                end = i
        self.lines = all_lines[start:end]
        self.dirty = 1

    def scroll_wrap(self, message, current_y, color=text.COLOR_DEFAULT,
                    font=text.FONT_DEFAULT):
        words = message.split()
        lines, line_number = [''], 0
        max_width = max(100, min(450, self.transform.width - 8))
        # Split the message into lines, wrapping when width does not fit
        for word in words:
            if font.size(lines[line_number] + word)[0] > max_width:
                lines.append(word + ' ')  # begin a new line with the word
                line_number += 1
            else:
                lines[line_number] += word + ' '

        for line in lines:
            if -20 < current_y - self.scroll_pixels < self.transform.height:
                text.draw(self.image, line, (5, current_y - self.scroll_pixels),
                          color, font)
            current_y += font.size('A')[1] + 1
        return current_y + 1

class SceneTab(Node):
    def __init__(self, node_props, group_, overlay_group, user_scene, style):
        super().__init__(node_props)
        self.user_scene = user_scene
        self.heading = TabHeading(NodeProperties(self, 0, 0, self.transform.width, style.get('tabsize'),
                                                 anchor_y=Anchor.bottom),
                                  group_, 'Scene View', fit=False, style=style)
        self.box = BorderBox(NodeProperties(self, 0, 0, 0, 0), group_)

    def update(self):
        super().update()
        target = self.parent.selected_node
        if target is not None and hasattr(target, 'rect') and getattr(target.parent, 'is_origin', 'Scene') == 'Scene':
            if target.rect.width > 0 and target.rect.height > 0:
                self.box.transform.position = target.rect.x - 1, target.rect.y - 1
                self.box.transform.size = target.rect.width + 2, target.rect.height + 2
                self.box.is_point = False
            else:
                self.box.transform.position = target.rect.x - 4, target.rect.y - 4
                self.box.transform.size = 9, 9
                self.box.is_point = True
            self.box.enabled = True
        else:
            self.box.enabled = False

    def on_resize(self):
        super().on_resize()
        self.heading.transform.width = self.transform.width

class BorderBox(SpriteNode):
    _layer = 32767

    def __init__(self, node_props, groups):
        super().__init__(node_props, groups, fill_color=None)
        self.is_point = False

    def draw(self):
        super().draw()
        if self._visible and self.dirty > 0:
            if not self.is_point:
                corners = ((0, 0), (self.transform.width - 1, 0),
                           (self.transform.width - 1, self.transform.height - 1), (0, self.transform.height - 1))
                pygame.draw.lines(self.image, (255, 255, 255, 127), True, corners, 1)
            else:
                pygame.draw.line(self.image, (255, 127, 127, 127), (0, 9 // 2), (9, 9 // 2))
                pygame.draw.line(self.image, (127, 255, 127, 127), (9 // 2, 0), (9 // 2, 9))

class ListSelector(GridList):
    event_handler = MOUSE_EVENTS
    _layer = 2

    def __init__(self, node_props, group, horizontal=False, spacing=20, options=None, **kwargs):
        super().__init__(node_props, group, horizontal, spacing, **kwargs)
        self.tiles = options
        self.hovered_index = None
        self.transform.height = self.spacing * len(self.tiles)

    def draw(self):
        SpriteNode.draw(self)
        if self._visible and self.dirty > 0:
            self.image.fill(self.style.get('background'))
            indexes = self.indexes_in_view()
            for i, position in zip(indexes, self.tile_positions(indexes.start)):
                if i == self.hovered_index:
                    text.box(self.image, self.tiles[i], position, self.transform.width, self.spacing,
                             box_color=self.style.get('background_selected'), color=self.style.get('color'))
                else:
                    text.box(self.image, self.tiles[i], position, self.transform.width, self.spacing,
                             box_color=self.style.get('background'), color=self.style.get('color'))

    def event(self, event):
        if self.rect.collidepoint(event.pos):
            index = self.position_to_index((event.pos[0] - self.rect.x,
                                            event.pos[1] - self.rect.y))
            if 0 <= index < len(self.tiles):
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.parent.text == self.tiles[index]:
                        # Close the grid on a double-click or repeat selection
                        self.enabled = False
                        self.parent.state = State.idle
                    else:
                        self.parent.text = self.tiles[index]
                    if self.parent.dirty < 1:
                        self.parent.dirty = 1
                elif event.type == pygame.MOUSEMOTION:
                    self.hovered_index = index
                    self.dirty = 1
        elif event.type == pygame.MOUSEMOTION:
            self.hovered_index = None
            self.dirty = 1

class DropdownEntry(TextEntry):
    event_handler = MOUSE_EVENTS

    def __init__(self, node_props, group, horizontal=False, default_text='', options=None,
                 enter_callback=None, **kwargs):
        super().__init__(node_props, group, default_text, enter_callback, cursor=' v', **kwargs)
        self.options = options
        self.grid = ListSelector(NodeProperties(self, 0, self.transform.height,
                                                self.transform.width, 0),
                                 group, horizontal, self.transform.height, options, style=self.style,
                                 background=brighten_color(self.style.get('background'), -5))
        self.grid.enabled = False

    def event(self, event):
        if self.state == State.locked or not self._visible:
            return

        last_state = self.state
        last_text = self.text

        if event.type in MOUSE_EVENTS:
            if self.rect.collidepoint(event.pos) or (self.grid.rect.collidepoint(event.pos)
                                                     and self.grid.enabled):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.state = State.selected
                    self.grid.options = self.options
                    self.grid.enabled = True
                elif last_state == State.idle:
                    self.state = State.hovered
            elif last_state == State.hovered or event.type == pygame.MOUSEBUTTONDOWN:
                self.state = State.idle
                self.grid.enabled = False

        if last_state != self.state or last_text != self.text:
            self.dirty = 1
