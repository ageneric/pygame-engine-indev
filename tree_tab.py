import pygame
import engine.text as text
from engine.spritesheet import tint_surface
from engine.base_node import SpriteNode, NodeProperties, Anchor
import engine.interface as interface
from engine.template import NODE_CLASSES, INTERFACE_CLASSES, node_to_template

from other_tab import TabHeading, string_color, DropdownEntry
import weakref


class LinearEntry:
    __slots__ = 'weak_reference', 'reference_visible', 'reference_enabled', 'image', 'depth'

    def __init__(self, reference_node, image_size, depth):
        self.weak_reference = weakref.ref(reference_node)
        self.reference_visible = getattr(reference_node, 'visible', -1)
        self.reference_enabled = getattr(reference_node, 'enabled', -1)
        self.image = pygame.Surface(image_size)
        self.depth = depth

class TreeTabGrid(interface.GridList):
    """This tab visualises the tree of nodes for the user scene.
    It maintains a linearised version of the tree as self.linear_copy."""
    event_handler = interface.MOUSE_EVENTS

    def __init__(self, node_props, group, tree, icon_sheet, **kwargs):
        super().__init__(node_props, group, **kwargs)

        image_node = icon_sheet.load_image((0, 0, 1, 1), 8)
        image_sprite_node = icon_sheet.load_image((1, 0, 1, 1), 8)
        self.icon_images = ((image_node, image_sprite_node),
                            (image_node.copy(), image_sprite_node.copy()))
        for icon in self.icon_images[0]:
            tint_surface(icon, interface.brighten_color(self.style.get('color'), -18))

        self.selected_entry = None
        self.hovered_entry = None
        self.tree = tree
        self.linear_copy = self.tiles  # alias
        self.get_linear_copy(self.tree)

        text_surf = text.render('generated ', color=(255, 255, 255), save_sprite=False)
        self.g_text_offset = text_surf.get_width()

    def get_linear_copy(self, tree, depth=0):
        for node in tree.nodes:
            self.linear_copy.append(self.new_entry(node, depth))
            self.get_linear_copy(node, depth + 1)

    def new_entry(self, reference_node, depth):
        entry = LinearEntry(reference_node, self.forward_to_rect(0).size, depth)
        self.entry_redraw(entry)
        return entry

    def update(self):
        node_count = self.traverse_tree(self.tree)
        # Remove deleted nodes at the end of the tree
        if node_count < len(self.linear_copy):
            # print('del remainder', node_count, len(self.linear_copy))
            del self.linear_copy[node_count:]
            self.dirty = 1

    def traverse_tree(self, tree, index_list=0, depth=0) -> int:
        """Perform a pre-order traversal of the tree and update the linear copy
        to match the tree, by detecting which nodes have been added or removed.
        Entries at the end of the linear copy are never removed, so to clear
        these, del list[i:] using the return value i (number of real entries).
        """
        for node in tree.nodes:
            self.find_node_in_list(node, index_list, depth)
            index_list += 1
            if node.nodes:  # checking it is not a leaf node is an optimisation
                index_list = self.traverse_tree(node, index_list, depth + 1)
        return index_list

    def find_node_in_list(self, node, index_list, depth):
        """Check for the given node in the linear copy, at or following the
        index, and update the linear copy to match the tree at that index."""
        start_index = index_list
        len_list = len(self.linear_copy)

        # Loop until the node is found or the end of the list is reached
        found_node = False
        while not found_node and index_list < len_list:
            copy_node = self.linear_copy[index_list]
            if node is copy_node.weak_reference():
                node_visible = getattr(node, 'visible', -1)
                node_enabled = getattr(node, 'enabled', - 1)
                # If the entry corresponding to a node is found, ensure that
                # its properties still match - redraw it if they have changed
                if (node_enabled != copy_node.reference_enabled
                        or node_visible != copy_node.reference_visible):
                    copy_node.reference_enabled = node_enabled
                    copy_node.reference_visible = node_visible
                    self.entry_redraw(copy_node)
                found_node = True  # exit loop
            else:
                index_list += 1

        # Node not found in list, so it must be new, so insert it into list
        if index_list >= len_list:
            # print('create', start_index, depth)  # assert not found_node
            self.linear_copy.insert(start_index, self.new_entry(node, depth))

        # Did we skip over any nodes in list? Delete those as they are no longer in tree
        elif index_list - start_index > 0:
            # print('del from tree', start_index, index_list)
            del self.linear_copy[start_index:index_list]
            self.dirty = 1

    def entry_redraw(self, entry):
        background_name = 'background'
        if entry == self.selected_entry:
            background_name = 'background_selected'
        elif entry == self.hovered_entry:
            background_name = 'background_hovered'
        background = self.style.get(background_name)

        if entry.reference_visible >= 0:
            icon_image = self.icon_images[entry.reference_enabled][1]
        else:
            icon_image = self.icon_images[entry.reference_enabled][0]

        entry.image.fill(background)
        entry.image.blit(icon_image, (entry.depth*8 + 2, self.spacing // 2 - 4))

        state = ('e' if entry.reference_enabled else '') + ('v' if entry.reference_visible == 1 else '')
        text.draw(entry.image, state, (entry.depth * 8 + 12, 2), color=self.style.get('color'))
        node_name = type(entry.weak_reference()).__name__
        if entry.reference_visible == 0:
            name_color = interface.brighten_color(self.style.get('color'), -18)
        else:
            name_color = string_color(node_name)
        text.draw(entry.image, node_name, (entry.depth * 8 + 32, 2), color=name_color)
        if not entry.weak_reference() in node_to_template:
            if entry == self.selected_entry or entry == self.hovered_entry:
                text.draw(entry.image, 'generated +', (self.transform.width - self.g_text_offset - 15, 2),
                          interface.brighten_color(background, 20), static=True)
            else:
                text.draw(entry.image, '+', (self.transform.width - 15, 2),
                          interface.brighten_color(self.style.get('color'), -18), static=True)
        self.dirty = 1

    def on_resize(self):
        super().on_resize()
        for tile in self.tiles:
            if hasattr(tile, 'image'):
                tile.image = pygame.Surface(self.forward_to_rect(0).size)
                self.entry_redraw(tile)
        if self.nodes:
            self.nodes[0].scroll_by(0)  # reposition and resize the scrollbar

    def event(self, event):
        if self.rect.collidepoint(event.pos):
            index = self.position_to_index((event.pos[0] - self.rect.x,
                                            event.pos[1] - self.rect.y))
            if 0 <= index < len(self.tiles):
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.replace_entry(self.tiles[index], 'selected_entry')
                    self.parent.parent.set_selected_node(self.selected_entry.weak_reference())
                elif event.type == pygame.MOUSEMOTION:
                    self.replace_entry(self.tiles[index], 'hovered_entry')
        elif event.type == pygame.MOUSEMOTION:
            self.replace_entry(None, 'hovered_entry')

    def replace_entry(self, new_entry, attribute_name):
        previous_entry = getattr(self, attribute_name, None)
        if new_entry is previous_entry:  # skip if the entry does not change
            return
        setattr(self, attribute_name, new_entry)  # reassign entry (read by entry_redraw)
        if previous_entry is not None:
            self.entry_redraw(previous_entry)  # previous entry un-highlighted
        if new_entry is not None:
            self.entry_redraw(new_entry)  # newly stored entry is highlighted
        return new_entry

    def set_tree(self, tree):
        self.tree = tree
        self.linear_copy.clear()
        self.get_linear_copy(self.tree)
        self.dirty = 1

class TreeTab(SpriteNode):
    _layer = 0

    def __init__(self, node_props, group, tree, icon_sheet,
                 ui_style, **kwargs):
        super().__init__(node_props, group)
        self.style = interface.Style.from_kwargs(kwargs)

        TabHeading(
            NodeProperties(self, 0, 0, self.transform.width, anchor_y=Anchor.bottom),
            group, 'Tree View', style=self.style)
        self.grid = TreeTabGrid(
            NodeProperties(self, 5, 25, max(0, self.transform.width - 10), max(0, self.transform.height - 120)),
            group, tree, icon_sheet, color=self.style.get('color'),
            background=self.style.get('background_indent'))
        interface.Scrollbar(
            NodeProperties(self.grid, width=2), group, style=self.style)

        class_options = list(NODE_CLASSES + INTERFACE_CLASSES)
        if hasattr(self.grid.tree, 'template') and 'modules' in self.grid.tree.template:
            class_options.extend(self.grid.tree.template['modules'])

        self.toggle = interface.Toggle(
            NodeProperties(self, 5, self.grid.transform.y - 20, 60, 20),
            group, 'Nodes v', style=ui_style, callback=self.toggle_grid, checked=self.grid.enabled)
        self.pick_class = DropdownEntry(
            NodeProperties(self, 5, self.transform.height - 72, max(0, self.transform.width - 115), 18),
            group, default_text=class_options[0], options=class_options, style=ui_style)
        self.button_add = interface.Button(
            NodeProperties(self, self.transform.width - 105, self.transform.height - 72, 100, 18),
            group, 'Same Level', style=ui_style, callback=self.action_add_node)
        self.button_add_child = interface.Button(
            NodeProperties(self, self.transform.width - 105, self.transform.height - 52, 100, 18),
            group, 'As Child', style=ui_style, callback=self.action_add_child_node)
        self.button_delete = interface.Button(
            NodeProperties(self.grid, self.grid.transform.width, 0, 60, 20, Anchor.right, Anchor.bottom, False),
            group, 'Delete', style=ui_style, callback=self.action_delete_node, background=(76, 36, 36))
        self.button_clear = interface.Button(NodeProperties(
            self.grid, self.grid.transform.width - 65, 0, 100, 20, Anchor.right, Anchor.bottom, False),
            group, 'Clear Selected', self.action_clear, style=ui_style)

    def update(self):
        super().update()
        if self.parent.selected_node is None and self.button_add_child.state != interface.State.locked:
            self.button_add_child.state = interface.State.locked
            self.button_add_child.dirty = 1
            self.button_delete.enabled = self.button_clear.enabled = False
        elif self.parent.selected_node and self.button_add_child.state == interface.State.locked:
            self.button_add_child.state = interface.State.idle
            self.button_add_child.dirty = 1
            self.button_delete.enabled = self.button_clear.enabled = True

    def draw(self):
        super().draw()

        if self._visible and self.dirty > 0:
            self.image.fill(self.style.get('background'))
            text.draw(self.image, 'Create Instance', (5, self.transform.height - 89),
                      color=self.style.get('color'))
            if self.parent.play:
                text.draw(self.image, 'Changes are not saved in Play mode.',
                          (5, self.transform.height - 35))

    def toggle_grid(self, checked):
        self.grid.enabled = checked
        self.toggle.message = 'Nodes v' if checked else 'Nodes x'

    def on_resize(self):
        super().on_resize()
        self.grid.transform.size = (max(0, self.transform.width - 10),
                                    max(0, self.transform.height - 120))
        self.pick_class.transform.width = max(0, self.transform.width - 115)
        self.pick_class.grid.transform.width = self.pick_class.transform.width
        self.pick_class.transform.y = self.transform.height - 72
        for i, button in enumerate((self.button_add, self.button_add_child)):
            button.transform.position = (self.transform.width - 105,
                                         self.transform.height - 72 + 20 * i)
        self.button_delete.transform.x = self.grid.transform.width
        self.button_clear.transform.x = self.grid.transform.width - 65

    def action_clear(self):
        self.grid.replace_entry(None, 'selected_entry')
        self.parent.clear_selected_node()

    def set_pick_class_options(self, user_class_options):
        class_options = list(NODE_CLASSES + INTERFACE_CLASSES)
        class_options.extend(user_class_options)
        self.pick_class.options = class_options

    def action_add_node(self):
        if self.parent.selected_node is not None:
            self.parent.add_node(self.pick_class.text, self.parent.selected_node.parent)
        else:
            self.parent.add_node(self.pick_class.text, self.grid.tree)

    def action_add_child_node(self):
        if self.parent.selected_node is not None:
            self.parent.add_node(self.pick_class.text, self.parent.selected_node)

    def action_delete_node(self):
        if self.parent.selected_node is not None:
            self.parent.remove_selected_node()
