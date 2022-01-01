import pygame
from collections import namedtuple

NodeProperties = namedtuple('NodeProperties', ['parent',
                            'x', 'y', 'width', 'height', 'anchor_x', 'anchor_y', 'rotation', 'enabled'],
                            defaults=[0, 0, 0, 0, 0, 0, 0, True])

class Anchor:
    top = left = 0
    center = middle = 0.5
    bottom = right = 1

class Transform:
    def __init__(self, x: float, y: float, width=0, height=0, anchor_x=0.0, anchor_y=0.0, rotation=0.0):
        self.is_modified = True
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        self.rotation = rotation

    def __repr__(self) -> str:
        return f'(XY {self.x}, {self.y}, WH {self.width}, {self.height}, aXY {self.anchor_x}, {self.anchor_y})'

    @classmethod
    def from_rect(cls, rect, anchor_x=0, anchor_y=0, rotation=0):
        return cls(rect.x, rect.y, rect.width, rect.height, anchor_x, anchor_y, rotation)

    def rect(self):
        return pygame.Rect(int(self.x - self.width * self.anchor_x),
                           int(self.y - self.height * self.anchor_y), int(self.width), int(self.height))

    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)
        if not self.is_modified and key not in ('anchor', 'anchor_x', 'anchor_y'):
            object.__setattr__(self, 'is_modified', True)

    # Getters and setters for transform properties
    @property
    def position(self) -> (float, float):
        return self.x, self.y

    @position.setter
    def position(self, position_x_y: (float, float)):
        self.x, self.y = position_x_y

    @property
    def size(self) -> (int, int):
        return self.width, self.height

    @size.setter
    def size(self, width_height: (int, int)):
        self.width, self.height = width_height

    @property
    def anchor(self) -> (float, float):
        return self.anchor_x, self.anchor_y

    @anchor.setter
    def anchor(self, anchor_x_y: (float, float)):
        self.anchor_x, self.anchor_y = anchor_x_y

class Node:
    def __init__(self, node_props: NodeProperties):
        if not hasattr(node_props[0], 'add_child'):
            raise AttributeError(f'Incorrect type for parent, NodeProperties[0] (got {node_props[0]})')
        self.parent = node_props[0]
        self.parent.add_child(self)
        self.transform = Transform(*node_props[1:-1])
        self._enabled = node_props[8]

        self.nodes = []

    def update(self):
        if self.nodes:  # optimisation; check for leaf node (~0.9x time)
            for child in self.nodes:
                if child.enabled:
                    child.update()

    def draw(self, surface):
        if self.nodes:  # optimisation; check for leaf node (~0.9x time)
            for child in self.nodes:
                if child.enabled:
                    child.draw(surface)

    def add_child(self, child):
        self.nodes.append(child)
        child.parent = self

    def remove_child(self, child):
        if child in self.nodes:
            self.nodes.remove(child)
            child.parent = None
        else:
            print(f'Engine warning: could not remove child {child} as it could not be found.')

    def world_rect(self) -> pygame.Rect:
        if isinstance(self.parent, Node):
            parent_rect = self.parent.world_rect()
            return self.transform.rect().move(parent_rect.x, parent_rect.y)
        else:
            return self.transform.rect()

    def __del__(self):
        self.parent = None
        # Calls __del__() for each child node, and by recursion all nodes below it
        # Equivalent to self.nodes.clear() but not del self.nodes
        del self.nodes[:]

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, set_enable: bool):
        self._enabled = set_enable
        self.cascade_set_visible(set_enable)

    def cascade_set_visible(self, set_visible: bool):
        for child in self.nodes:
            child.cascade_set_visible(set_visible)


class SpriteNode(pygame.sprite.DirtySprite, Node):
    def __init__(self, node_props: NodeProperties, *groups, image=None, fill_color=None):
        if groups and isinstance(groups[0], pygame.sprite.AbstractGroup):
            pygame.sprite.DirtySprite.__init__(self, *groups)
        else:
            print('Engine warning: a SpriteNode was initialised without a group or with an incorrect type.\n'
                  + 'This may be because the "group" parameter was missed.')
            pygame.sprite.DirtySprite.__init__(self)

        Node.__init__(self, node_props)
        self._visible = self.enabled
        self.rect = self.world_rect()
        # print(f'{self}, rect {self.rect}, parent {self.parent}, {self.groups()}')

        if image is None:
            self.image = pygame.Surface(self.transform.size)
            if fill_color is not None:
                self.image.fill(fill_color)
        else:
            self.image = pygame.Surface(self.transform.size, 0, image)

    def draw(self, surface):
        if self.transform.is_modified:
            self.transform.is_modified = False
            if self.dirty < 2:
                self.dirty = 1
            self.rect = self.world_rect()
        Node.draw(self, self.dirty)

    def __del__(self):
        pygame.sprite.Sprite.kill(self)
        Node.__del__(self)

    def cascade_set_visible(self, set_visible):
        Node.cascade_set_visible(self, set_visible)
        self._visible = int(set_visible and self._enabled)
