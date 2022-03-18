import pygame
import ast

from engine import text as text
from engine.base_node import Node, SpriteNode, NodeProperties, Anchor
from engine.interface import Style, Scrollbar, State, TextEntry

from other_tab import TabHeading, string_color


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

class InspectorTab(SpriteNode):
    """Expected environment: parent has property 'selected_node'"""
    _layer = 0

    def __init__(self, node_props: NodeProperties, group, ui_style, **kwargs):
        super().__init__(node_props, group)
        self.style = Style.from_kwargs(kwargs)

        TabHeading(NodeProperties(self, 0, 0, self.transform.width, anchor_y=Anchor.bottom),
                   group, 'Inspector', style=self.style)

        Scrollbar(NodeProperties(self, width=2), group, style=self.style)

        self.scroll_pixels = 0
        self.widget_group = group
        self.selected_node = None

        self.widget_style = ui_style
        self.widgets = Node(NodeProperties(self, 5, 5))

    def update(self):
        super().update()
        if self.selected_node is not self.parent.selected_node:
            self.selected_node = self.parent.selected_node
            for i in range(len(self.widgets.nodes)):
                self.widgets.nodes[0].remove()
            self.widgets.nodes.clear()
            if self.selected_node is None:
                self.scene_description_widgets()
            else:
                self.generate_widgets()

    def scene_description_widgets(self):
        pass

    def generate_widgets(self):
        node = self.selected_node

        transform = getattr(node, 'transform', None)
        enabled = getattr(node, 'enabled', None)
        groups = getattr(node, 'groups', None)

        current_y = 4
        widget_x_half = self.transform.width // 2 + 3 + 20
        widget_width_half = self.transform.width // 2 - 90

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
            NumberEntry(NodeProperties(self.widgets, 55, current_y, widget_width_half, 15), self.widget_group,
                        str(getattr(self.selected_node, 'layer')), 'layer', allow_types=(int,),
                        style=self.widget_style, enter_callback=self.set_layer)

    def edit_transform_entry(self, x, y, width, height, bound_name, allow_types):
        NumberEntry(NodeProperties(self.widgets, x, y, width, height), self.widget_group,
                    str(getattr(self.selected_node.transform, bound_name)), bound_name,
                    allow_types=allow_types, style=self.widget_style,
                    background=self.widget_style.get('background_indent'),
                    enter_callback=self.set_selected_transform_attribute)

    def set_selected_transform_attribute(self, literal, bound_name):
        setattr(self.selected_node.transform, bound_name, literal)

    def set_layer(self, literal, bound_name):
        if self.selected_node.groups():
            self.selected_node.groups()[0].change_layer(self.selected_node, literal)

    def draw(self):
        super().draw()

        if self._visible and self.dirty > 0:
            self.image.fill(self.style.get('background'))

            for widget in self.widgets.nodes:
                widget.enabled = widget.transform.y > self.scroll_pixels

            if self.selected_node:
                node_name = type(self.selected_node).__name__
                name_color = string_color(node_name)
                surface = text.render(node_name, color=name_color)
                text.draw(self.image, str(self.selected_node), (5 + surface.get_rect().width, 240))
                self.image.blit(surface, (5, 240))

            node = self.selected_node

            if node is None:
                text.draw(self.image, type(self.parent.user_scene).__name__, (0, 0))
            else:
                self.widgets.transform.y = -self.scroll_pixels

                for _node in self.widgets.nodes:
                    if hasattr(_node, 'bound'):
                        text.draw(self.image, _node.bound, (_node.transform.x - 55, _node.transform.y - self.scroll_pixels))

                text_parent = 'Parent: ' + str(getattr(node, 'parent', None))
                text.draw(self.image, text_parent, (0, 80 - self.scroll_pixels))

                for i, prop in enumerate(self.readable_properties(node)):
                    text.draw(self.image, prop, (0, 100 + i * 12 - self.scroll_pixels), color=self.style.get('color'))
                    text.draw(self.image, str(getattr(node, prop)), (108, 100 + i * 12 - self.scroll_pixels))

    @staticmethod
    def readable_properties(node):
        for prop in dir(node):
            if (not prop.startswith('_') and type(getattr(node, prop))
                    in (int, str, tuple, bool, pygame.Rect)):
                yield prop

    @property
    def scroll_limits(self):
        return 0, 100
