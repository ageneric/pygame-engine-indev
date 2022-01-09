import pygame
import engine.text as text
from engine.spritesheet import tint_surface
from engine.base_node import SpriteNode, NodeProperties
from engine.interface import Grid, Style, Toggle, modify_color


def string_color(name: str):
    """Generates an arbitrary bright colour from the first six characters."""
    key = map(ord, name.ljust(6, ' '))
    color = []
    for i in range(3):
        c = (16 * next(key) + next(key)) % 256  # use next two values as color
        color.append(c if c > 137 else 247)  # make dark colour channels bright
    return color

class LinearEntry:
    __slots__ = 'reference_id', 'reference_name', 'reference_visible', 'reference_enabled', 'image'

    def __init__(self, node_props, reference):
        self.reference_id = id(reference)
        self.reference_name = type(reference).__name__
        if hasattr(reference, 'visible'):
            self.reference_visible = reference.visible
        else:
            self.reference_visible = -1
        self.reference_enabled = reference.enabled
        self.image = pygame.Surface((node_props[3], node_props[4]))

    def __repr__(self):
        return hex(self.reference_id)[2:]

class TreeTabGrid(Grid):
    """This tab visualises the tree of nodes for the user scene.
    It maintains a linearised version of the tree as self.linear_copy."""
    def __init__(self, node_props, group, tree, icon_sheet, **kwargs):
        image_node = icon_sheet.load_image((0, 0, 1, 1), 8)
        image_sprite_node = icon_sheet.load_image((1, 0, 1, 1), 8)
        self.icon_images = [[image_node, image_node.copy()],
                            [image_sprite_node, image_sprite_node.copy()]]
        tint_surface(self.icon_images[0][0], (110, 100, 100))
        tint_surface(self.icon_images[1][0], (110, 100, 100))

        super().__init__(node_props, group, **kwargs)
        self.tree = tree
        self.linear_copy = self.nodes  # alias
        self.get_linear_copy(self.tree)

    def get_linear_copy(self, tree, depth=0):
        for node in tree.nodes:
            self.linear_copy.append(self.new_entry(node, depth))
            self.get_linear_copy(node, depth + 1)

    def new_entry(self, reference_node, depth):
        if self.horizontal:
            node_props = (None, 0, 0, self.spacing, self.transform.height)
        else:
            node_props = (None, 0, 0, self.transform.width, self.spacing)
        entry = LinearEntry(node_props, reference_node)
        self.redraw_entry(entry, depth)
        return entry

    def update(self):
        # print(", ".join(map(hex, map(id, self.tree.nodes))))
        # print(self.linear_copy)
        self.traverse_tree(self.tree)
        # print(self.linear_copy)

    def traverse_tree(self, tree, index=0, depth=0):
        for node in tree.nodes:
            self.find_node_in_list(node, index, depth)
            if node.nodes:
                index = self.traverse_tree(node, index + 1, depth + 1)
            else:
                index += 1
        # TODO: Remove deleted nodes at the end of the tree
        return index

    def find_node_in_list(self, node, index, depth):
        len_list_copy = len(self.linear_copy)

        node_visible = getattr(node, 'visible', -1)
        node_enabled = getattr(node, 'enabled', - 1)
        node_id = id(node)
        start_index = index
        found_node = False

        while not found_node and index < len_list_copy:
            copy_node = self.linear_copy[index]
            if node_id == copy_node.reference_id:
                if (node_enabled != copy_node.reference_enabled
                        or node_visible != copy_node.reference_visible):
                    copy_node.reference_enabled = node_enabled
                    copy_node.reference_visible = node_visible
                    self.redraw_entry(copy_node, depth)
                found_node = True  # exit loop
            else:
                index += 1

        # Node could not be found in list, it must be new. Create it in list
        if index >= len_list_copy:
            print('create', start_index)
            assert not found_node
            self.linear_copy.insert(start_index, self.new_entry(node, depth))

        # Did we skip over any nodes in list? Delete those as they are no longer in tree
        if index - start_index > 0:
            print('del from tree', start_index, index)
            del self.linear_copy[start_index:index]
            self.dirty = 1

    def redraw_entry(self, entry, depth):
        entry.image.fill(self.style.get('background'))
        if entry.reference_visible >= 0:
            icon_image = self.icon_images[1][entry.reference_enabled]
        else:
            icon_image = self.icon_images[0][entry.reference_enabled]

        entry.image.blit(icon_image, (2+depth*8, self.spacing - 16))

        state = ('e' if entry.reference_enabled else '') + ('v' if entry.reference_visible == 1 else '')
        text.draw(entry.image, state, (depth*8 + 12, 0),
                  color=self.style.get('color'))
        name_color = string_color(entry.reference_name)
        if entry.reference_visible == 0:
            name_color = modify_color(self.style.get('color'), -18)
        text.draw(entry.image, entry.reference_name, (depth*8 + 32, 0),
                  color=name_color)
        self.dirty = 1


class TreeTab(SpriteNode):
    _layer = 0

    def __init__(self, node_props: NodeProperties, group, tree, icon_sheet, **kwargs):
        super().__init__(node_props, group)
        self.style = Style.from_kwargs(kwargs)

        self.grid = TreeTabGrid(NodeProperties(self, 5, 45, max(0, self.transform.width - 10), 200),
            group, tree, icon_sheet, color=self.style.get('color'),
            background=modify_color(self.style.get('background'), 5))

        self.toggle = Toggle(NodeProperties(self, 5, self.grid.transform.y - 20, 60, 20),
            group, "Nodes v", background=modify_color(self.style.get('background'), -5),
            style=self.style, callback=self.toggle_grid, checked=self.grid.enabled)

        add_mouse_handler = self.scene().mouse_handlers.append
        add_mouse_handler(self.toggle)

    def draw(self):
        super().draw()

        if self._visible and self.dirty > 0:
            self.image.fill(self.style.get('background_editor'))

            background, tabsize = self.style.get('background'), self.style.get('tabsize')
            w, h = self.transform.width, self.transform.height
            text.box(self.image, 'Node Tree', (0, 0), height=tabsize, box_color=background,
                     font=self.style.get('font'), color=self.style.get('color'))
            pygame.draw.rect(self.image, background, (0, tabsize, w, h - tabsize))

    def toggle_grid(self, checked):
        self.grid.enabled = checked
        self.toggle.message = "Nodes v" if checked else "Nodes x"

    def resize_rect(self):
        super().resize_rect()
        self.grid.transform.width = max(0, self.transform.width - 10)
