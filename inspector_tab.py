import pygame
import ast

from engine import text as text
from engine.node import Node, SpriteNode, NodeProps, Anchor
from engine.interface import Style, Scrollbar, State, TextEntry, Toggle, Button
import engine.template as template
from engine.spritesheet import tint_surface

from other_tab import TabHeading, string_color

INSPECTOR_NAME = 'Attributes'

class LiteralEntry(TextEntry):
    NUMERIC = '1234567890.-x'

    def __init__(self, node_props, group, default_text='', bound='', enter_callback=None,
                 edit_callback=None, allow_characters=None, allow_types=None, **kwargs):
        super().__init__(node_props, group, default_text, enter_callback, edit_callback,
                         allow_characters=allow_characters, **kwargs)
        self.allow_types = allow_types
        self.bound = bound

    def parse(self):
        if len(self.text) > 8192:  # ignore excessively long input
            return None
        try:
            literal = ast.literal_eval(self.text)
        except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
            return None

        if not self.allow_types or type(literal) in self.allow_types:
            return literal
        else:
            try:  # directly convertible to first allowed type (e.g. list to tuple)
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

    def draw(self):
        super().draw()
        if self._visible and self.dirty > 0:
            self.image.fill(self.parent.style.get('background'))
            node_name = type(self.parent.selected_node).__name__
            surface = text.render(node_name, color=string_color(node_name))
            message = str(self.parent.selected_node).replace(node_name, '#')
            text.draw(self.image, message, (9 + surface.get_rect().width, 2))
            self.image.blit(surface, (5, 2))


transform_types = ((('x', 'y'), (float, int)), (('width', 'height'), (int,)),
                   (('anchor_x', 'anchor_y'), (float, int)))

class InspectorTab(SpriteNode):
    _layer = 0

    def __init__(self, node_props, group, ui_style, **kwargs):
        super().__init__(node_props, group)
        self.style = Style.from_kwargs(kwargs)

        self.header = TabHeading(NodeProps(
            self, 0, 0, self.transform.width, anchor_y=Anchor.bottom),
            group, INSPECTOR_NAME, style=self.style)
        self.scrollbar = Scrollbar(NodeProps(self, width=2), group, style=self.style)
        group.change_layer(self.scrollbar, 2)
        self.label_top = InspectorLabel(NodeProps(
            self, 0, 0, self.transform.width, 18, enabled=False), group)
        self.scroll_pixels = 0
        self.scroll_limits = 0, 0
        self.group = group
        self.ui_style = ui_style
        self.entry_style = Style.from_kwargs(dict(style=self.style, color_error=(224, 120, 120),
                                             background=self.style.get('background_indent')))
        self.describe_font = pygame.font.SysFont('Calibri', 13, italic=True)

        self.selected_node = None
        self.user_scene = None
        self.toggle_enabled = None
        self.widget_holder = Node(NodeProps(self, 5, 0))
        self.set_selected(self.parent.selected_node, self.parent.user_scene)

    def update(self):
        super().update()
        if self.selected_node is not None:
            self.update_node_inspector()

    def set_selected(self, node, user_scene):
        # Set the selected node and user scene to match the parent editor
        self.selected_node = node
        self.user_scene = user_scene
        # Delete all previous widgets and clear references to them
        for i in range(len(self.widget_holder.nodes)):
            self.widget_holder.nodes[0].remove()
        self.widget_holder.nodes.clear()
        self.toggle_enabled = None
        # Show either the scene or node inspector based on the selection
        if self.selected_node is None:
            self.generate_scene_inspector()
        else:
            self.generate_node_inspector()

    def generate_scene_inspector(self):
        self.label_top.enabled = False
        self.header.message = INSPECTOR_NAME
        self.header.dirty = 1
        self.dirty = 1
        self.scroll_pixels = 0
        self.scroll_limits = 0, 0
        question_icon = self.parent.icon_sheet.load_image(pygame.Rect(3, 0, 1, 1), 8)
        tint_surface(question_icon, self.style.get('color_scroll'))
        Button(NodeProps(
            self.widget_holder, 127, 54, 16, 16), self.group, image=question_icon,
            callback=lambda: self.parent.action_show_help('Groups'), style=self.ui_style)

    def half_widget_columns(self):
        """Return x values for left, right columns."""
        if self.transform.width >= 175:
            return 95, self.transform.width // 2 + 40
        else:
            return 0, self.transform.width // 2 - 5

    def generate_node_inspector(self):
        self.label_top.enabled = True
        self.label_top.transform.width = self.transform.width
        self.label_top.dirty = 1
        self.header.message = INSPECTOR_NAME + ' (Inspect)'
        self.header.dirty = 1
        self.dirty = 1

        current_y = 36
        half_widget_columns = self.half_widget_columns()
        half_widget_width = half_widget_columns[1] - half_widget_columns[0] - 5
        full_widget_column = half_widget_columns[self.transform.width < 175]

        if getattr(self.selected_node, 'transform', False):
            current_y += 18
            for attribute_pair, allow_types in transform_types:
                for column in (0, 1):
                    LiteralEntry(NodeProps(
                        self.widget_holder, half_widget_columns[column], current_y, half_widget_width, 15),
                        self.group, '', attribute_pair[column], self.set_transform_attribute,
                        allow_characters=LiteralEntry.NUMERIC, allow_types=allow_types,
                        style=self.entry_style)
                current_y += 18
            current_y += 8

        enabled = getattr(self.selected_node, 'enabled', None)
        if enabled is not None:
            self.toggle_enabled = Toggle(NodeProps(
                self.widget_holder, full_widget_column, current_y, half_widget_width, 15), self.group,
                str(enabled), self.set_enabled_attribute, enabled, style=self.ui_style)
            self.toggle_enabled.bound = 'enabled'
            current_y += 20

        if isinstance(self.selected_node, pygame.sprite.DirtySprite):
            LiteralEntry(NodeProps(
                self.widget_holder, full_widget_column, current_y, half_widget_width, 15),
                self.group, '', '_layer', self.set_layer, allow_types=(int,),
                allow_characters=LiteralEntry.NUMERIC, style=self.entry_style)
            current_y += 20
            indexes = list(template.group_indexes(self.user_scene, self.selected_node))
            LiteralEntry(NodeProps(
                self.widget_holder, full_widget_column, current_y, half_widget_width, 15),
                self.group, str(indexes)[1:-1], 'groups', self.set_groups, allow_types=(list, tuple),
                allow_characters='1234567890 [],', style=self.entry_style)

        self.scroll_limits = 0, max(0, 216 + sum(1 for _ in self.readable_properties(self.selected_node)) * 14 - self.transform.height)
        self.scrollbar.scroll_by(0)

    def resize_node_inspector(self):
        self.label_top.transform.width = self.transform.width
        half_widget_columns = self.half_widget_columns()
        half_widget_width = half_widget_columns[1] - half_widget_columns[0] - 5
        full_widget_column = half_widget_columns[self.transform.width < 175]

        if getattr(self.selected_node, 'transform', False):
            for i in range(6):
                self.widget_holder.nodes[i].transform.x = half_widget_columns[i % 2]

        for widget in self.widget_holder.nodes:
            if isinstance(widget, LiteralEntry) or widget is self.toggle_enabled:
                if widget.bound in ('x', 'y', 'width', 'height', 'anchor_x', 'anchor_y',
                                    '_layer', 'enabled', 'groups'):
                    widget.transform.width = half_widget_width
                if widget.bound in ('_layer', 'enabled', 'groups'):
                    widget.transform.x = full_widget_column
                    if 175 < self.transform.width < 375:
                        widget.transform.width = self.transform.width - 115

    def update_node_inspector(self):
        for widget in self.widget_holder.nodes:
            if isinstance(widget, LiteralEntry) and widget.state != State.selected:
                if widget.bound in template.DATA_NODE[:-1]:  # transform attributes
                    value = getattr(self.selected_node.transform, widget.bound)
                elif widget.bound == 'groups':
                    value = list(template.group_indexes(self.user_scene, self.selected_node))
                else:
                    value = getattr(self.selected_node, widget.bound)
                if str(value) != widget.text:
                    widget.text = str(value)
                    widget.dirty = 1

        if self.toggle_enabled is not None:
            if self.toggle_enabled.checked != self.selected_node.enabled:
                self.toggle_enabled.checked = self.selected_node.enabled
                self.toggle_enabled.dirty = 1

    def set_enabled_attribute(self, set_enable):
        self.selected_node.enabled = set_enable
        self.toggle_enabled.message = str(set_enable)
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
        if not self.parent.play:
            template.update_node(self.selected_node, 'layer')

    def set_groups(self, literal, _):
        self.selected_node.kill()
        for index in literal:
            if 0 <= index < len(self.user_scene.groups):
                self.selected_node.add(self.user_scene.groups[index])
        if not self.parent.play:
            template.update_node(self.selected_node, 'groups', self.user_scene)

    def draw(self):
        super().draw()

        if self._visible and self.dirty > 0:
            self.image.fill(self.style.get('background'))

            self.widget_holder.transform.y = -self.scroll_pixels
            for widget in self.widget_holder.nodes:
                widget.enabled = 0 < widget.transform.y - self.scroll_pixels < self.transform.height

            if self.selected_node is None:
                text.draw(self.image, 'Scene: ' + type(self.user_scene).__name__, (5, 2))
                text.draw(self.image, 'Scene groups table', (5, 55),
                          color=self.style.get('color'), static=True)
                for i, group in enumerate(self.user_scene.groups):
                    text.draw(self.image, str(i), (5, 80 + i * 14))
                    text.draw(self.image, str(group), (25, 80 + i * 14), color=self.style.get('color_scroll'))
            else:
                self.draw_node_inspector()
                for i, prop in enumerate(self.readable_properties(self.selected_node)):
                    text.draw(self.image, prop, (5, 210 + i * 14 - self.scroll_pixels),
                              color=self.style.get('color'))
                    text.draw(self.image, repr(getattr(self.selected_node, prop)),
                              (135, 210 + i * 14 - self.scroll_pixels))

    def draw_node_inspector(self):
        _widgets = (widget for widget in self.widget_holder.nodes)

        color = self.style.get('color')
        if self.selected_node in template.node_to_template:
            saving_text = 'Changes to the following attributes are saved in Editing mode.'
        else:
            saving_text = 'Generated by code. Changes to any attributes are not saved.'
        self.scroll_text(saving_text, (5, 19), static=True, font=self.describe_font)

        # Label transform widgets: each label is to the left of a pair of entries
        if getattr(self.selected_node, 'transform', False):
            self.scroll_text('Transform', (5, 37), color, static=True)
            self.scroll_text('self.transform', (78, 37), self.style.get('color_scroll'), static=True)
            for label in ('Position', 'Size', 'Anchor'):
                widget_x, widget_y = next(_widgets).transform.position
                self.scroll_text(label, (widget_x - 80, widget_y), color, static=True)
                next(_widgets)  # skip widget to get to next column

        if self.toggle_enabled is not None:
            self.scroll_text('Enabled', (5, next(_widgets).transform.y), color)

        if isinstance(self.selected_node, pygame.sprite.DirtySprite):
            widget_y = next(_widgets).transform.y
            self.scroll_text('Layer', (5, widget_y), color, static=True)
            self.scroll_text('Group IDs', (5, widget_y + 18), color, static=True)
            self.scroll_text('List type. Refer to the scene groups table.', (5, widget_y + 36),
                             font=self.describe_font, static=True)

        self.scroll_text('The following attributes cannot be edited. Values since selected.',
                         (5, 195), font=self.describe_font, static=True)

    def scroll_text(self, message, position, color=text.COLOR_DEFAULT, **kwargs):
        text.draw(self.image, message, (position[0], position[1] - self.scroll_pixels),
                  color, **kwargs)

    def on_resize(self):
        super().on_resize()
        if self.selected_node is not None:
            self.resize_node_inspector()
        self.scrollbar.scroll_by(0)

    @staticmethod
    def readable_properties(node):
        for prop in dir(node):
            if (not (prop.startswith('_') or prop in ('enabled', 'layer', 'blendmode')) and
                    type(getattr(node, prop)) in (int, str, tuple, bool, pygame.Rect)):
                yield prop
