import pygame
import ast

from engine import text as text
from engine.base_node import Node, SpriteNode, NodeProperties, Anchor
from engine.interface import Style, Scrollbar, State, TextEntry, Toggle
import engine.template as template

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
        if len(self.text) > 8192:
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

    def __init__(self, node_props, group):
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


transform_types = ((('x', 'y'), (float, int)), (('width', 'height'), (int,)),
                   (('anchor_x', 'anchor_y'), (float, int)))

class InspectorTab(SpriteNode):
    _layer = 0

    def __init__(self, node_props, group, ui_style, **kwargs):
        super().__init__(node_props, group)
        self.style = Style.from_kwargs(kwargs)

        TabHeading(NodeProperties(self, 0, 0, self.transform.width, anchor_y=Anchor.bottom),
                   group, 'Inspector', style=self.style)
        Scrollbar(NodeProperties(self, width=2), group, style=self.style)

        self.scroll_pixels = 0
        self.scroll_limits = 0, 90
        self.group = group
        self.ui_style = ui_style
        self.entry_style = Style.from_kwargs(dict(style=self.style, color_error=(224, 120, 120),
                                             background=self.style.get('background_indent')))
        self.describe_font = pygame.font.SysFont('Calibri', 13, italic=True)

        self.selected_node = None
        self._enabled_toggle = None
        self.widgets = Node(NodeProperties(self, 5, 5))
        self.label_top = InspectorLabel(NodeProperties(self, 0, 0, self.transform.width - 2,
                                                       18, enabled=False), self.group)

    def update(self):
        super().update()
        if self.selected_node is not self.parent.selected_node:
            self.selected_node = self.parent.selected_node
            for i in range(len(self.widgets.nodes)):
                self.widgets.nodes[0].remove()
            self.widgets.nodes.clear()
            self._enabled_toggle = None
            if self.selected_node is None:
                self.generate_scene_inspector()
            else:
                self.generate_node_inspector()

        if self.selected_node is not None:
            self.update_node_inspector()

    def generate_scene_inspector(self):
        self.label_top.enabled = False

    def half_widget_columns(self):
        return 100, self.transform.width // 2 + 45  # x for left, right columns

    def generate_node_inspector(self):
        self.label_top.enabled = True
        self.label_top.dirty = 1

        current_y = 36
        half_widget_columns = self.half_widget_columns()
        half_widget_width = self.transform.width // 2 - 60

        if getattr(self.selected_node, 'transform', False):
            current_y += 18
            for attribute_pair, allow_types in transform_types:
                for column in (0, 1):
                    LiteralEntry(NodeProperties(
                        self.widgets, half_widget_columns[column], current_y, half_widget_width, 15),
                        self.group, '', attribute_pair[column], self.set_transform_attribute,
                        allow_characters=LiteralEntry.NUMERIC, allow_types=allow_types,
                        style=self.entry_style)
                current_y += 18
            current_y += 8

        enabled = getattr(self.selected_node, 'enabled', None)
        if enabled is not None:
            self._enabled_toggle = Toggle(NodeProperties(
                self.widgets, half_widget_columns[0], current_y, half_widget_width, 15), self.group,
                str(enabled), self.set_enabled_attribute, enabled, style=self.ui_style)
            current_y += 20

        if isinstance(self.selected_node, pygame.sprite.DirtySprite):
            LiteralEntry(NodeProperties(
                self.widgets, half_widget_columns[0], current_y, half_widget_width, 15),
                self.group, '', '_layer', self.set_layer, allow_types=(int,),
                allow_characters=LiteralEntry.NUMERIC, style=self.entry_style)
            current_y += 20

    def resize_node_inspector(self):
        half_widget_columns = self.half_widget_columns()
        half_widget_width = self.transform.width // 2 - 60

        if getattr(self.selected_node, 'transform', False):
            for i in range(6):
                self.widgets.nodes[i].transform.x = half_widget_columns[i % 2]

        for widget in self.widgets.nodes:
            if isinstance(widget, LiteralEntry) and widget.state != State.selected:
                if widget.bound in ('x', 'y', 'width', 'height', 'anchor_x', 'anchor_y',
                                    'layer'):
                    widget.transform.width = half_widget_width

    def update_node_inspector(self):
        for widget in self.widgets.nodes:
            if isinstance(widget, LiteralEntry) and widget.state != State.selected:
                if widget.bound in ('x', 'y', 'width', 'height', 'anchor_x', 'anchor_y'):
                    value = getattr(self.selected_node.transform, widget.bound)
                else:
                    value = getattr(self.selected_node, widget.bound)
                if str(value) != widget.text:
                    widget.text = str(value)
                    widget.dirty = 1

        if getattr(self.selected_node, 'enabled', None) is not None:
            if self._enabled_toggle.checked != self.selected_node.enabled:
                self._enabled_toggle.checked = self.selected_node.enabled
                self._enabled_toggle.dirty = 1

    def set_enabled_attribute(self, set_enable):
        self.selected_node.enabled = set_enable
        self._enabled_toggle.message = str(set_enable)
        if not self.parent.play:
            template.update_node(self.selected_node, 'enabled')

    def set_attribute(self, literal, bound_name):
        setattr(self.selected_node, bound_name, literal)
        if not self.parent.play:
            template.update_node(self.selected_node, bound_name)

    def set_transform_attribute(self, literal, bound_name):
        setattr(self.selected_node.transform, bound_name, literal)
        if not self.parent.play:
            template.update_node(self.selected_node, bound_name)

    def set_layer(self, literal, _):
        if self.selected_node.groups():
            self.selected_node.groups()[0].change_layer(self.selected_node, literal)
        # TODO: implement layer switching

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
                self.draw_node_inspector()

                for i, prop in enumerate(self.readable_properties(node)):
                    text.draw(self.image, prop, (5, 210 + i * 13 - self.scroll_pixels), color=self.style.get('color'))
                    text.draw(self.image, repr(getattr(node, prop)), (135, 210 + i * 13 - self.scroll_pixels))

    def draw_node_inspector(self):
        self.widgets.transform.y = -self.scroll_pixels
        _widgets = (widget for widget in self.widgets.nodes)

        color = self.style.get('color')
        self.scroll_text('Any changes to the following attributes are saved in Editing mode.',
                         (5, 19), static=True, font=self.describe_font)

        # Label transform widgets: each label is to the left of a pair of entries
        if getattr(self.selected_node, 'transform', False):
            self.scroll_text('Transform', (5, 37), color, static=True)
            self.scroll_text('self.transform', (78, 37), self.style.get('color_scroll'), static=True)
            for label in ('Position', 'Size', 'Anchor'):
                widget_x, widget_y = next(_widgets).transform.position; next(_widgets)
                self.scroll_text(label, (widget_x - 80, widget_y), color, static=True)

        if self._enabled_toggle is not None:
            self.scroll_text('Enabled', (5, next(_widgets).transform.y), color)

        if isinstance(self.selected_node, pygame.sprite.DirtySprite):
            widget_y = next(_widgets).transform.y
            self.scroll_text('Layer', (5, widget_y), color, static=True)
            self.scroll_text('Group ' + str(self.selected_node.groups()), (5, widget_y + 18))

        self.scroll_text('The following attributes cannot be edited. Values since selected.',
                         (5, 195), font=self.describe_font, static=True)

    def scroll_text(self, message, position, color=text.COLOR_DEFAULT, **kwargs):
        text.draw(self.image, message, (position[0], position[1] - self.scroll_pixels),
                  color, **kwargs)

    def on_resize(self):
        super().on_resize()
        if self.selected_node is not None:
            self.resize_node_inspector()

    @staticmethod
    def readable_properties(node):
        for prop in dir(node):
            if (not (prop.startswith('_') or prop in ('enabled', 'layer', 'blendmode')) and
                    type(getattr(node, prop)) in (int, str, tuple, bool, pygame.Rect)):
                yield prop
