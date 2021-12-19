import pygame
import engine.text
from engine.base_node import Node, SpriteNode, Transform
from constants import C_LIGHT, C_DARK, C_RED, C_LIGHT_ISH, C_DARK_ISH
from collections import namedtuple

TreeEntry = namedtuple('TreeEntry', ['nodes', 'node_uid', 'enabled', 'visible', 'tree_image'])

class TreeTab(SpriteNode):
    def __init__(self, node_props, group=None, ref=None):
        super(TreeTab, self).__init__(node_props, group, fill_color=C_LIGHT_ISH)
        self.ref = ref

    def draw(self, screen):
        if self.dirty and self.ref is not None and self.visible:
            self.image.fill(C_LIGHT_ISH)
            self.recursive_draw(self.ref)

    def recursive_draw(self, target, level=0, flat_index=0):
        start = flat_index
        for child in target:
            if isinstance(child, SpriteNode):
                symbol = 's'
            elif isinstance(child, Node):
                symbol = 'n'
            else:
                symbol = '?'

            message = ' '.join((str(type(child)).lstrip('<class ').rstrip('>'), str(child.transform)))
            state = ('e' if child.enabled else '') + ('v' if getattr(child, 'visible', False) else '')

            if getattr(child, 'message', False):
                message = repr(getattr(child, 'message')) + ' ' + message

            engine.text.draw(self.image, symbol, (level*18, flat_index*18), color=C_RED, static=True)
            engine.text.draw(self.image, state, (level*18 + 9, flat_index*18), color=C_DARK_ISH, static=True)
            engine.text.draw(self.image, message, (level*18 + 27, flat_index*18), color=C_DARK)
            flat_index += 1
            flat_index += self.recursive_draw(child.nodes, level + 1, flat_index)
        return flat_index - start
