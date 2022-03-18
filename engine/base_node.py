import pygame
from collections import namedtuple

NodeProperties = namedtuple('NodeProperties', ['parent',
                            'x', 'y', 'width', 'height', 'anchor_x', 'anchor_y', 'enabled'],
                            defaults=[0, 0, 0, 0, 0.0, 0.0, True])

class Anchor:
    top = left = 0.0
    center = middle = 0.5
    bottom = right = 1.0

class Transform:
    __slots__ = 'x', 'y', 'width', 'height', '_anchor_x', '_anchor_y', 'node'

    def __init__(self, x: float, y: float, width=0, height=0, anchor_x=0.0, anchor_y=0.0, node=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self._anchor_x = anchor_x
        self._anchor_y = anchor_y
        self.node = node  # optional; observes changes to the transform

    def __repr__(self) -> str:
        return f'Transform({self.x}, {self.y}, {self.width}, {self.height}, {self.anchor_x}, {self.anchor_y})'

    def __str__(self) -> str:
        if self.anchor_x == 0 and self.anchor_y == 0:
            return f'<Transform({round(self.x, 3)}, {round(self.y, 3)}), ' \
                   f'{self.width}, {self.height}>'
        else:
            return f'<Transform({round(self.x, 3)}, {round(self.y, 3)}), ' \
                   f'{self.width}, {self.height}, {self.anchor_x}, {self.anchor_y}>'

    @classmethod
    def from_rect(cls, rect, anchor_x=0.0, anchor_y=0.0):
        return cls(rect.x + rect.width * anchor_x, rect.y + rect.height * anchor_y,
                   rect.width, rect.height, anchor_x, anchor_y)

    def rect(self):
        x, y = self.rect_position(self.x, self.y)
        return pygame.Rect(x, y, self.width, self.height)

    def rect_position(self, x: float, y: float) -> (int, int):
        return int(x - self.width * self._anchor_x), int(y - self.height * self._anchor_y)

    def __setattr__(self, name, val):  # may alternatively be achieved using properties
        object.__setattr__(self, name, val)
        node = getattr(self, 'node', None)
        if node is not None and name in ('x', 'y', 'width', 'height'):
            node.transform_update(name)

    # Getters and setters for transform properties
    @property
    def position(self) -> (float, float):
        return self.x, self.y

    @position.setter
    def position(self, position_x_y: (float, float)):
        # Set the first attribute directly so only one transform_update is used
        object.__setattr__(self, 'x', position_x_y[0])
        self.y = position_x_y[1]

    @property
    def size(self) -> (int, int):
        return self.width, self.height

    @size.setter
    def size(self, width_height: (int, int)):
        # Set the first attribute directly so only one transform_update is used
        object.__setattr__(self, 'width', width_height[0])
        self.height = width_height[1]

    def get_positive_size(self) -> (int, int):
        return max(0, self.width), max(0, self.height)

    @property
    def anchor(self) -> (float, float):
        return self._anchor_x, self._anchor_y

    @anchor.setter
    def anchor(self, anchor_x_y: (float, float)):
        self._anchor_x, self._anchor_y = anchor_x_y

    @property
    def anchor_x(self) -> float:
        return self._anchor_x

    @property
    def anchor_y(self) -> float:
        return self._anchor_y

    @anchor_x.setter
    def anchor_x(self, anchor_x: float):
        # Shift x value so that the rectangle stays in place
        new_x = self.x + (anchor_x - self._anchor_x) * self.width
        # Set the x attribute directly, no transform_update is needed
        object.__setattr__(self, 'x', new_x)
        self._anchor_x = anchor_x

    @anchor_y.setter
    def anchor_y(self, anchor_y: float):
        # Shift y value so that the rectangle stays in place
        new_y = self.y + (anchor_y - self._anchor_y) * self.width
        # Set the y attribute directly, no transform_update is needed
        object.__setattr__(self, 'y', new_y)
        self._anchor_y = anchor_y

class Node:
    def __init__(self, node_props: NodeProperties):
        self.parent = node_props[0]
        # Check that the supplied node has the necessary attributes to be the parent
        if not hasattr(self.parent, 'nodes'):
            raise ValueError('Missing nodes attribute on parent, NodeProperties[0]'
                          + f'(got {self.parent})\nUsually a Node, Scene, or related type')
        elif not (hasattr(self.parent, 'rect') or hasattr(self.parent, 'is_origin')):
            raise ValueError('Missing rect or is_origin on parent, NodeProperties[0]'
                          + f'(got {self.parent})\nUsually a node, Scene, or related type')
        self.parent.nodes.append(self)
        self.transform = Transform(*node_props[1:7], node=self)
        self._enabled = node_props[7]
        self.nodes = []

        if hasattr(self, 'event_handler'):
            self.scene().add_event_handler(self)
        # Get screen co-ordinates, shift position to be relative to the parent node
        self.rect = self.transform.rect()
        if not hasattr(self.parent, 'is_origin'):
            self.rect.move_ip(self.parent.rect.x, self.parent.rect.y)
        self.nodes = []

    def update(self):
        # Recursively update child nodes, if not a leaf node (check uses ~0.9x time)
        if self.nodes:
            for child in self.nodes:
                if child.enabled:
                    child.update()

    def draw(self):
        # Recursively draw child nodes, if not a leaf node (check uses ~0.9x time)
        if self.nodes:
            for child in self.nodes:
                if child.enabled:
                    child.draw()

    def world_rect(self) -> pygame.Rect:
        """Calculate the on-screen rectangle of a Node. Cached as Node.rect."""
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
        self._set_visible(set_enable)

    def transform_update(self, name):
        """Update the rect attribute (on-screen position/size) for this
        node and all child nodes when its transform is modified."""
        if self.rect == self.world_rect():  # no changes to apply
            return

        if name in ('width', 'height'):
            self.on_resize()

        # Move the top-left of the rectangle if position changes or
        # the rectangle is resized about a point that is not the top-left
        if name in ('x', 'y') or not self.transform.anchor == (0, 0):
            x, y = self.transform.x, self.transform.y
            if not hasattr(self.parent, 'is_origin'):
                x += self.parent.rect.x
                y += self.parent.rect.y
            self._set_rect_position(x, y)

    def on_resize(self):
        self.rect.width = self.transform.width
        self.rect.height = self.transform.height

    def _set_visible(self, set_visible: bool):
        if self.nodes:
            for child in self.nodes:
                child._set_visible(set_visible)

    def _set_rect_position(self, x, y):
        x, y = self.transform.rect_position(x, y)
        self.rect.x, self.rect.y = x, y
        if self.nodes:
            for child in self.nodes:
                child._set_rect_position(x + child.transform.x, y + child.transform.y)

    def remove(self):
        if self in self.parent.nodes:
            self.parent.nodes.remove(self)
        self.transform.node = None
        if hasattr(self, 'event_handler'):
            self.scene().remove_event_handler(self)
        for i in range(len(self.nodes)):
            self.nodes[0].remove()

class SpriteNode(Node, pygame.sprite.DirtySprite):
    def __init__(self, node_props: NodeProperties, groups=None, image=None, fill_color=None):
        try:
            pygame.sprite.DirtySprite.__init__(self, groups)
        except TypeError:  # for example when groups = None (default)
            print('Engine warning: a SpriteNode was initialised without a group or with an incorrect type.'
                  + f'\nThis may be because the "group" parameter was missed. ({self})')
            pygame.sprite.DirtySprite.__init__(self)

        Node.__init__(self, node_props)
        self._visible = self.world_visible()

        if image is None:
            flags = pygame.SRCALPHA * (fill_color is None or len(fill_color) > 3)
            self.image = pygame.Surface(self.transform.get_positive_size(), flags)
            if fill_color is not None:
                self.image.fill(fill_color)
        else:
            self.image = pygame.Surface(self.transform.get_positive_size(),
                                        image.get_flags(), image)

    def remove(self):
        pygame.sprite.Sprite.kill(self)
        Node.remove(self)

    def world_visible(self) -> bool:
        visible = self._enabled
        parent = self.parent
        while visible and isinstance(parent, Node):
            visible = getattr(parent, 'visible', True) and visible
            parent = parent.parent
        return visible

    def _set_visible(self, set_visible):
        set_visible = set_visible and self.enabled
        if set_visible != self._visible:
            self._visible = set_visible
            Node._set_visible(self, set_visible)
            if self.dirty < 2:
                self.dirty = 1

    def _set_rect_position(self, x, y):
        Node._set_rect_position(self, x, y)
        if self.dirty < 2:
            self.dirty = 1

    def on_resize(self):
        Node.on_resize(self)
        self.image = pygame.Surface(self.transform.get_positive_size(),
                                    self.image.get_flags(), self.image)
        if self.dirty < 2:
            self.dirty = 1
