import pygame
import engine.text
from engine.interface import Grid

class TreeEntry:
    def __init__(self, node_props, reference):
        if hasattr(reference, 'visible'):
            self.reference_visible = reference.visible
        else:
            self.reference_visible = -1
        self.reference_id = id(reference)
        self.reference_enabled = reference.enabled
        self.image = pygame.Surface((node_props[3], node_props[4]))

class TreeTabGrid(Grid):
    def __init__(self, node_props, group, tree, **kwargs):
        super().__init__(node_props, group, **kwargs)
        self.tree = tree
        self.copy_list = []
        self.get_copy_list(self.tree)
        self.nodes = self.copy_list  # alias

    def get_copy_list(self, tree, depth=0):
        for node in tree.nodes:
            self.make_copy_list_entry(node, depth)
            self.get_copy_list(node, depth + 1)

    def make_copy_list_entry(self, reference_node, depth):
        spacing = self.style.get('spacing', 20)
        if self.horizontal:
            node_props = (None, 0, 0, spacing, self.transform.height)
        else:
            node_props = (None, 0, 0, self.transform.width, spacing)
        entry = TreeEntry(node_props, reference_node)
        self.redraw_entry(entry, depth)
        self.copy_list.append(entry)

    def update(self):
        self.traverse_tree(self.tree)

    def traverse_tree(self, tree, index=0, depth=0):
        for node in tree.nodes:
            self.find_node_in_list(node, index, depth)
            if node.nodes:
                index = self.traverse_tree(node, index + 1, depth + 1)
            else:
                index += 1
        return index

    def find_node_in_list(self, node, index, depth):
        len_copy_list = len(self.copy_list)
        copy_node = None
        if index < len_copy_list:
            copy_node = self.copy_list[index]

        node_visible = getattr(node, 'visible', -1)
        node_enabled = getattr(node, 'enabled', - 1)
        node_id = id(node)
        start_index = index
        found_node = False

        while not found_node and index < len_copy_list:
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
        if index >= len_copy_list:
            assert not found_node
            print('make')
            self.make_copy_list_entry(node, depth)

        # Did we skip over any nodes in list? Delete those as they are no longer in tree
        elif start_index - index > 0:
            print('del')
            del self.copy_list[start_index:index]

    def redraw_entry(self, entry, depth):
        entry.image.fill(self.style.get('background'))
        if entry.reference_visible >= 0:
            symbol = 's'
        else:
            symbol = 'n'

        state = ('e' if entry.reference_enabled else '') + ('v' if entry.reference_visible == 1 else '')
        engine.text.draw(entry.image, symbol + ' ' + state, (depth*8, 0), color=self.style.get('color'))
        engine.text.draw(entry.image, hex(entry.reference_id), (depth*8 + 32, 0), color=self.style.get('color_dim', self.style.get('color')))
        self.dirty = 1
