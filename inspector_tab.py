import pygame
import ast

from engine import text as text
from engine.base_node import Node, SpriteNode, NodeProperties, Anchor
from engine.interface import Style, Scrollbar, State, TextEntry, Toggle

from other_tab import TabHeading, string_color

class LiteralEntry(TextEntry):
    NUMERIC = '1234567890.-x'

    def __init__(self, node_props, group, default_text='', bound='', enter_callback=None,
                 edit_callback=None, allow_characters=None, allow_types=None, **kwargs):
        super().__init__(node_props, group, default_text, enter_callback, edit_callback,
                         allow_characters=allow_characters, **kwargs)
        self.allow_types = allow_types
        self.bound = bound

    def parse(self):
        if len(self.text) > 5120:
            return None
        try:
            literal = ast.literal_eval(self.text)
        except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
            return None

        if not self.allow_types or type(literal) in self.allow_types:
            return literal
        else:
            try:
                return self.allow_types[0](literal)
            except TypeError:
                return None

    def on_enter(self):
        literal = self.parse()
        if literal is not None and callable(self.enter_callback):
            self.text = str(literal)
            self.enter_callback(literal, self.bound)
        self.state = State.idle

    def switch_style(self, base_name):
        error_string = '_error' if self.parse() is None else ''
        return self.style.get_by_state(base_name + error_string, self.state)


class InspectorLabel(SpriteNode):
    _layer = 1

    def __init__(self, node_props: NodeProperties, group):
        super().__init__(node_props, group)

    def draw(self):
        super().draw()

        if self._visible and self.dirty > 0:
            self.image.fill(self.parent.style.get('background'))
            node_name = type(self.parent.selected_node).__name__
            name_color = string_color(node_name)
            surface = text.render(node_name, color=name_color)
            message = str(self.parent.selected_node).replace(node_name, '#')
            text.draw(self.image, message, (6 + surface.get_rect().width, 2))
            self.image.blit(surface, (5, 2))

labels = {'x': 'Position', 'width': 'Size', 'anchor_x': 'Anchor', '_layer': 'Layer'}

class InspectorTab(SpriteNode):
    _layer = 0

    def __init__(self, node_props: NodeProperties, group, ui_style, **kwargs):
        super().__init__(node_props, group)
        self.style = Style.from_kwargs(kwargs)

        TabHeading(NodeProperties(self, 0, 0, self.transform.width, anchor_y=Anchor.bottom),
                   group, 'Inspector', style=self.style)
        Scrollbar(NodeProperties(self, width=2), group, style=self.style)

        self.scroll_pixels = 0
        self.group = group
        self.selected_node = None
        self.ui_style = ui_style
        self.entry_style = Style.from_kwargs(dict(style=self.style, color_error=(224, 120, 120),
                                             background=self.style.get('background_indent')))
        self.widgets = Node(NodeProperties(self, 5, 5))

        self._enabled_toggle = None
        self.label_top = InspectorLabel(NodeProperties(self, 0, 0, self.transform.width - 2,
                                                       18, enabled=False), self.group)

    def update(self):
        super().update()
        if self.selected_node is not self.parent.selected_node:
            self.selected_node = self.parent.selected_node
            for i in range(len(self.widgets.nodes)):
                self.widgets.nodes[0].remove()
            self.widgets.nodes.clear()
            if self.selected_node is None:
                self.scene_description_widgets()
                self.label_top.enabled = False
            else:
                self.generate_widgets()
                self.label_top.enabled = True
            self.label_top.dirty = 1
        self.update_widgets()

    def scene_description_widgets(self):
        pass

    def generate_widgets(self):
        node = self.selected_node
        transform = getattr(node, 'transform', None)
        enabled = getattr(node, 'enabled', None)
        groups = getattr(node, 'groups', None)

        current_y = 22
        half_widget_columns = (100, self.transform.width // 2 + 45)
        half_widget_width = self.transform.width // 2 - 60

        if transform is not None:
            breakdown = ((('x', 'y'), (float, int)), (('width', 'height'), (int,)),
                         (('anchor_x', 'anchor_y'), (float, int)))
            for (attribute_pair, allow_types) in breakdown:
                for i in (0, 1):
                    LiteralEntry(NodeProperties(
                        self.widgets, half_widget_columns[i], current_y, half_widget_width, 15),
                        self.group, '', attribute_pair[i], self.set_transform_attribute,
                        allow_characters=LiteralEntry.NUMERIC, allow_types=allow_types,
                        style=self.entry_style)
                current_y += 19

        if enabled is not None:
            self._enabled_toggle = Toggle(
                NodeProperties(self.widgets, 60, current_y, half_widget_width, 15),
                self.group, str(enabled), self.set_enabled_attribute, enabled, style=self.ui_style)
            current_y += 20

        if isinstance(node, pygame.sprite.DirtySprite):
            LiteralEntry(NodeProperties(self.widgets, half_widget_columns[0], current_y, half_widget_width, 15),
                         self.group, '', '_layer', self.set_layer, allow_types=(int,),
                         allow_characters=LiteralEntry.NUMERIC, style=self.entry_style)
            current_y += 20

    def resize_widgets(self):
        pass

    def update_widgets(self):
        for widget in self.widgets.nodes:
            if isinstance(widget, LiteralEntry) and widget.state != State.selected:
                if widget.bound in ('x', 'y', 'width', 'height', 'anchor_x', 'anchor_y'):
                    value = getattr(self.selected_node.transform, widget.bound)
                else:
                    value = getattr(self.selected_node, widget.bound)
                if str(value) != widget.text:
                    widget.text = str(value)
                    if widget.dirty < 1:
                        widget.dirty = 1
            elif widget is self._enabled_toggle:
                widget.checked = self.selected_node.enabled

    def set_enabled_attribute(self, set_enable):
        self.selected_node.enabled = set_enable
        self._enabled_toggle.message = str(set_enable)

    def set_attribute(self, literal, bound_name):
        setattr(self.selected_node, bound_name, literal)

    def set_transform_attribute(self, literal, bound_name):
        setattr(self.selected_node.transform, bound_name, literal)

    def set_layer(self, literal, _):
        if self.selected_node.groups():
            self.selected_node.groups()[0].change_layer(self.selected_node, literal)

    def draw(self):
        super().draw()

        if self._visible and self.dirty > 0:
            self.image.fill(self.style.get('background'))

            for widget in self.widgets.nodes:
                widget.enabled = self.scroll_pixels + self.transform.height > widget.transform.y > self.scroll_pixels

            node = self.selected_node

            if node is None:
                text.draw(self.image, type(self.parent.user_scene).__name__ + ' (scene)', (5, 2))
            else:
                self.widgets.transform.y = -self.scroll_pixels

                for _node in self.widgets.nodes:
                    if hasattr(_node, 'bound') and _node.bound in labels:
                        text.draw(self.image, labels[_node.bound], (_node.transform.x - 80,
                                  _node.transform.y - self.scroll_pixels), self.style.get('color'))

                text_parent = 'Parent: ' + str(getattr(node, 'parent', None))
                text.draw(self.image, text_parent, (5, 125 - self.scroll_pixels))

                for i, prop in enumerate(self.readable_properties(node)):
                    text.draw(self.image, prop, (5, 140 + i * 12 - self.scroll_pixels), color=self.style.get('color'))
                    text.draw(self.image, str(getattr(node, prop)), (108, 140 + i * 12 - self.scroll_pixels))

    @staticmethod
    def readable_properties(node):
        for prop in dir(node):
            if (not (prop.startswith('_') or prop in ('enabled', 'layer', 'blendmode')) and
                    type(getattr(node, prop)) in (int, str, tuple, bool, pygame.Rect)):
                yield prop

    @property
    def scroll_limits(self):
        return 0, 100
