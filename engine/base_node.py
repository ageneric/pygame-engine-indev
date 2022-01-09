import pygame
from collections import namedtuple

NodeProperties = namedtuple('NodeProperties', ['parent',
                            'x', 'y', 'width', 'height', 'anchor_x', 'anchor_y', 'rotation', 'enabled'],
                            defaults=[0, 0, 0, 0, 0, 0, 0, True])

class Anchor:
    top = left = 0.0
    center = middle = 0.5
    bottom = right = 1.0

class Transform:
    __slots__ = 'node', 'x', 'y', 'width', 'height', 'anchor_x', 'anchor_y', 'rotation'

    def __init__(self, x: float, y: float, width=0, height=0, anchor_x=0.0, anchor_y=0.0, rotation=0.0, node=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        self.rotation = rotation
        self.node = node

    def __repr__(self) -> str:
        return f'(XY {self.x}, {self.y}, WH {self.width}, {self.height}, aXY {self.anchor_x}, {self.anchor_y})'

    @classmethod
    def from_rect(cls, rect, anchor_x=0.0, anchor_y=0.0, rotation=0.0):
        return cls(rect.x, rect.y, rect.width, rect.height, anchor_x, anchor_y, rotation)

    def rect(self):
        return pygame.Rect(int(self.x - self.width * self.anchor_x),
                           int(self.y - self.height * self.anchor_y), self.width, self.height)

    def __setattr__(self, name, val):  # may alternatively be achieved using properties
        object.__setattr__(self, name, val)
        if hasattr(self, 'node') and name in ('x', 'y', 'width', 'height'):
            self.node.transform_on_update()

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
        self.transform = Transform(*node_props[1:7], node=self)
        self._enabled = node_props[8]

        self.rect = self.transform.rect()
        if not hasattr(self.parent, 'is_origin'):
            self.rect.move_ip(self.parent.rect.x, self.parent.rect.y)
        self.nodes = []

    def update(self):
        if self.nodes:  # checking this is not a leaf node takes ~0.9x the time
            for child in self.nodes:
                if child.enabled:
                    child.update()

    def draw(self):
        if self.nodes:  # checking this is not a leaf node takes ~0.9x the time
            for child in self.nodes:
                if child.enabled:
                    child.draw()

    def add_child(self, child):
        """Called internally. To specify the parent of a Node on
        initialisation, set NodeProperties[0]. Do not use this method."""
        self.nodes.append(child)
        child.parent = self

    def remove_child(self, child):
        if child in self.nodes:
            child.remove()
        else:
            print(f'Engine warning: could not remove child {child} as it could not be found.')

    def world_rect(self) -> pygame.Rect:
        rect = self.transform.rect()
        parent = self.parent
        while not hasattr(parent, 'is_origin'):
            rect.move_ip(parent.transform.x, parent.transform.y)
            parent = parent.parent
        return rect

    def scene(self):
        parent = self.parent
        while isinstance(parent, Node):
            parent = parent.parent
        return parent

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, set_enable: bool):
        self._enabled = set_enable
        self.cascade_set_visible(set_enable)

    def transform_on_update(self):
        if hasattr(self.parent, 'is_origin'):
            dx, dy = self.transform.x - self.rect.x, self.transform.y - self.rect.y
        else:
            dx, dy = self.transform.x - self.rect.x + self.parent.rect.x, self.transform.y - self.rect.y + self.parent.rect.y
        if dx or dy:
            self.cascade_move_rect(dx, dy)
        else:
            self.resize_rect()

    def resize_rect(self):
        self.rect.width = self.transform.width
        self.rect.height = self.transform.height

    def cascade_set_visible(self, set_visible: bool):
        if self.nodes:
            for child in self.nodes:
                child.cascade_set_visible(set_visible)

    def cascade_move_rect(self, dx, dy):
        self.rect.move_ip(dx, dy)
        if self.nodes:
            for child in self.nodes:
                child.cascade_move_rect(dx, dy)

    def remove(self):
        if self in self.parent.nodes:
            self.parent.nodes.remove(self)
        self.transform.node = None
        for child in self.nodes:
            child.remove()

class SpriteNode(Node, pygame.sprite.DirtySprite):
    def __init__(self, node_props: NodeProperties, *groups, image=None, fill_color=None):
        if groups and isinstance(groups[0], pygame.sprite.AbstractGroup):
            pygame.sprite.DirtySprite.__init__(self, *groups)
        else:
            print('Engine warning: a SpriteNode was initialised without a group or with an incorrect type.\n'
                  + 'This may be because the "group" parameter was missed.')
            pygame.sprite.DirtySprite.__init__(self)

        Node.__init__(self, node_props)
        self._visible = self.world_visible()

        if image is None:
            self.image = pygame.Surface(self.transform.size)
            if fill_color is not None:
                self.image.fill(fill_color)
        else:
            self.image = pygame.Surface(self.transform.size, 0, image)

    def remove(self):
        pygame.sprite.Sprite.kill(self)
        Node.remove(self)

    def world_visible(self) -> bool:
        visible = self._enabled
        parent = self.parent
        while visible and isinstance(parent, Node):
            visible = (not hasattr(parent, 'visible') or parent.visible) and visible
            parent = parent.parent
        return visible

    def cascade_set_visible(self, set_visible):
        set_visible = set_visible and self.enabled
        if set_visible != self._visible:
            self._visible = set_visible
            Node.cascade_set_visible(self, set_visible)
            if self.dirty < 2:
                self.dirty = 1

    def cascade_move_rect(self, dx, dy):
        Node.cascade_move_rect(self, dx, dy)
        if self.dirty < 2:
            self.dirty = 1

    def resize_rect(self):
        Node.resize_rect(self)
        self.image = pygame.Surface(self.transform.size)
        if self.dirty < 2:
            self.dirty = 1
