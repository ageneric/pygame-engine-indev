import pygame
import ast

from engine import text as text
from engine.base_node import Node, SpriteNode, NodeProperties
from engine.interface import Style, Scrollbar, TextEntry, State

from tree_tab import string_color


class NumberEntry(TextEntry):
    def __init__(self, node_props, group, default_text='', bound='', enter_callback=None,
                 edit_callback=None, allow_types=None, **kwargs):
        super().__init__(node_props, group, default_text, enter_callback, edit_callback,
                         allow_characters='1234567890.-box', **kwargs)
        self.allow_types = allow_types
        self.bound = bound

    def parse(self):
        if len(self.text) > 5120:
            return None
        try:
            literal = ast.literal_eval(self.text)
        except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
            return None

        if self.allow_types and type(literal) not in self.allow_types:
            try:
                return self.allow_types[0](literal)
            except TypeError:
                return None
        else:
            return literal

    def on_enter(self):
        literal = self.parse()
        if literal is not None and callable(self.enter_callback):
            self.text = str(literal)
            self.enter_callback(literal, self.bound)
        self.state = State.idle

    def switch_style(self, base_name):
        error_string = '_error' if self.parse() is None else ''
        return self.style.get_by_state(base_name + error_string, self.state)

class Inspector(SpriteNode):
    def __init__(self, node_props: NodeProperties, group, **kwargs):
        super().__init__(node_props, group)
        self.style = Style.from_kwargs(kwargs)
        self.scroll_pixels = 0
        self.draw_group = group
        self.selected_node = None

        self.widget_style = Style.from_kwargs(dict(style=self.style, color_error=(251, 110, 110),
                                                   background=self.style.get('background_indent')))
        self.widgets = Node(NodeProperties(self, 0, 0))

    def update(self):
        super().update()
        if self.selected_node is not self.parent.parent.selected_node:
            self.selected_node = self.parent.parent.selected_node
            if self.selected_node is not None:
                self.generate_widgets()

    def generate_widgets(self):
        node = self.selected_node

        transform = getattr(node, 'transform', None)
        enabled = getattr(node, 'enabled', None)
        groups = getattr(node, 'groups', None)

        current_y = 4
        widget_x_half = self.transform.width // 2 + 3 + 20
        widget_width_half = self.transform.width // 2 - 90

        for i in range(len(self.widgets.nodes)):
            self.widgets.nodes[0].remove()

        if transform is not None:
            self.edit_transform_entry(55, current_y, widget_width_half, 15, 'x', (float, int))
            self.edit_transform_entry(widget_x_half, current_y, widget_width_half, 15,
                                      'y', (float, int))
            current_y += 16
            self.edit_transform_entry(55, current_y, widget_width_half, 15, 'width', (int,))
            self.edit_transform_entry(widget_x_half, current_y, widget_width_half, 15,
                                      'height', (int,))
            current_y += 16
            self.edit_transform_entry(55, current_y, widget_width_half, 15, 'anchor_x', (float, int))
            self.edit_transform_entry(widget_x_half, current_y, widget_width_half, 15,
                                      'anchor_y', (float, int))
            current_y += 24

        if isinstance(node, SpriteNode):
            NumberEntry(NodeProperties(self.widgets, 55, current_y, widget_width_half, 15), self.draw_group,
                        str(getattr(self.selected_node, 'layer')), 'layer', allow_types=(int,),
                        style=self.widget_style, enter_callback=self.set_layer)

    def edit_transform_entry(self, x, y, width, height, bound_name, allow_types):
        NumberEntry(NodeProperties(self.widgets, x, y, width, height), self.draw_group,
                    str(getattr(self.selected_node.transform, bound_name)), bound_name, allow_types=allow_types,
                    style=self.widget_style, enter_callback=self.set_selected_transform_attribute)

    def set_selected_transform_attribute(self, literal, bound_name):
        setattr(self.selected_node.transform, bound_name, literal)

    def set_layer(self, literal, bound_name):
        if self.selected_node.groups():
            self.selected_node.groups()[0].change_layer(self.selected_node, literal)

    def draw(self):
        super().draw()

        self.image.fill(self.style.get('background'))
        node = self.selected_node

        if node is None:
            return

        self.widgets.transform.y = -self.scroll_pixels

        for _node in self.widgets.nodes:
            if hasattr(_node, 'bound'):
                text.draw(self.image, _node.bound, (_node.transform.x - 55, _node.transform.y - self.scroll_pixels))

        self.dirty = 1

        text_parent = 'Parent: ' + str(getattr(node, 'parent', None))
        text.draw(self.image, text_parent, (0, 80 - self.scroll_pixels))

        for i, prop in enumerate(self.readable_properties(node)):
            text.draw(self.image, prop, (0, 100 + i*12 - self.scroll_pixels), color=self.style.get('color'))
            text.draw(self.image, str(getattr(node, prop)), (108, 100 + i*12 - self.scroll_pixels))

    @staticmethod
    def readable_properties(node):
        for prop in dir(node):
            if not prop.startswith('_') and type(getattr(node, prop)) in (int, str, tuple, bool):
                yield prop

    @property
    def scroll_limits(self):
        return 0, 100

class InspectorTab(SpriteNode):
    """Expected environment: parent has property 'selected_node'"""
    def __init__(self, node_props: NodeProperties, group, **kwargs):
        super().__init__(node_props, group)
        self.style = Style.from_kwargs(kwargs)

        self.inspector = Inspector(NodeProperties(self, 5, 40, max(0, self.transform.width - 10),
                                                  max(50, self.transform.height - 40)),
                                   group, style=self.style)
        Scrollbar(NodeProperties(self.inspector, width=2), group, style=self.style)

    def update(self):
        super().update()

    def draw(self):
        super().draw()

        if self._visible and self.dirty > 0:
            self.image.fill(self.style.get('background_editor'))

            background, tabsize = self.style.get('background'), self.style.get('tabsize')
            w, h = self.transform.width, self.transform.height
            text.box(self.image, 'Inspector', (0, 0), height=tabsize, box_color=background,
                     font=self.style.get('font'), color=self.style.get('color'))
            pygame.draw.rect(self.image, background, (0, tabsize, w, h - tabsize))

            if self.inspector.selected_node:
                node_name = type(self.inspector.selected_node).__name__
                name_color = string_color(node_name)
                surface = text.render(node_name, color=name_color)
                text.draw(self.image, str(self.inspector.selected_node), (5 + surface.get_rect().width, 24))
                self.image.blit(surface, (5, 24))

    def resize_rect(self):
        super().resize_rect()
        self.inspector.transform.width = max(0, self.transform.width - 10)
        self.inspector.transform.height = max(50, self.transform.height - 40)
        self.inspector.selected_node = None
