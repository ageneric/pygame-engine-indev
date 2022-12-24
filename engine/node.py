import pygame
from typing import NamedTuple

_NODE_VALUE_WARNING = (
    '\nThis may be because the "parent" (argument 0) in NodeProps was missed.'
    '\nCheck that the first element is a Node, Scene, or related type.')

class NodeProps(NamedTuple):
    """NodeProps(parent, x=0, y=0, width=0, height=0, anchor_x=0, anchor_y=0, enabled=True)
    The base node properties used to initialise a node. Has default values."""
    parent: object
    x: float = 0
    y: float = 0
    width: int = 0
    height: int = 0
    anchor_x: float = 0  # proportion of size between 0 (left) and 1 (right)
    anchor_y: float = 0  # proportion of size between 0 (top) and 1 (bottom)
    enabled: bool = True

class Anchor:
    top = left = 0.0
    center = middle = 0.5
    bottom = right = 1.0

class Transform:
    """A data structure that stores position, size and relative anchor position.
    Every node will hold an instance of this class as Node.transform."""
    __slots__ = 'x', 'y', 'width', 'height', '_anchor_x', '_anchor_y', 'transform_update'

    def __init__(self, x: float, y: float, width=0, height=0,
                 anchor_x=Anchor.left, anchor_y=Anchor.top, transform_update=None):
        self.transform_update = None
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self._anchor_x = anchor_x  # proportion of size between 0 (left) and 1 (right)
        self._anchor_y = anchor_y  # proportion of size between 0 (top) and 1 (bottom)
        self.transform_update = transform_update  # observes changes to the transform

    def __repr__(self) -> str:
        return (f'Transform({self.x}, {self.y}, {self.width}, {self.height}, '
                f'{self._anchor_x}, {self._anchor_y})')

    def __str__(self) -> str:
        position_size_text = (f'Transform ({round(self.x, 3)}, {round(self.y, 3)}) '
                              f'{self.width}*{self.height}')
        if self._anchor_x == 0 and self._anchor_y == 0:
            return f'<{position_size_text}>'
        else:
            return f'<{position_size_text} anchored at ({self._anchor_x}, {self._anchor_y})>'

    # Alternative constructor and conversions for use by use
    @classmethod
    def from_rect(cls, rect, anchor_x: float = 0, anchor_y: float = 0):
        """Instantiate a Transform from a Pygame Rect (and optionally an anchor)."""
        return cls(rect.x + rect.width * anchor_x, rect.y + rect.height * anchor_y,
                   rect.width, rect.height, anchor_x, anchor_y)

    def rect(self):
        return pygame.Rect(*self.rect_position(self.x, self.y), *self.get_surface_size())

    def rect_position(self, x: float, y: float) -> (int, int):
        return int(x - self.width * self._anchor_x), int(y - self.height * self._anchor_y)

    # Called when any attribute is set
    # May alternatively be achieved using properties
    def __setattr__(self, name, val):
        object.__setattr__(self, name, val)
        if name in ('x', 'y', 'width', 'height') and self.transform_update is not None:
            self.transform_update(name)

    # Getters and setters for transform properties
    @property
    def position(self) -> (float, float):
        return self.x, self.y

    @position.setter
    def position(self, position_x_y: (float, float)):
        # Set the first attribute directly so only one _transform_update is used
        object.__setattr__(self, 'x', position_x_y[0])
        self.y = position_x_y[1]

    @property
    def size(self) -> (int, int):
        return self.width, self.height

    @size.setter
    def size(self, width_height: (int, int)):
        # Set the first attribute directly so only one _transform_update is used
        object.__setattr__(self, 'width', width_height[0])
        self.height = width_height[1]

    def get_surface_size(self) -> (int, int):
        return max(0, min(8192, self.width)), max(0, min(8192, self.height))

    @property
    def anchor_position(self) -> (float, float):
        return self._anchor_x, self._anchor_y

    @anchor_position.setter
    def anchor_position(self, anchor_x_y: (float, float)):
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
        # Set the x attribute directly, no _transform_update is needed
        object.__setattr__(self, 'x', new_x)
        self._anchor_x = anchor_x

    @anchor_y.setter
    def anchor_y(self, anchor_y: float):
        # Shift y value so that the rectangle stays in place
        new_y = self.y + (anchor_y - self._anchor_y) * self.height
        # Set the y attribute directly, no _transform_update is needed
        object.__setattr__(self, 'y', new_y)
        self._anchor_y = anchor_y


class Node:
    def __init__(self, node_props: NodeProps):
        self.parent = node_props[0]
        # Check that the supplied node has the necessary attributes to be the parent
        if not hasattr(self.parent, 'nodes'):
            raise ValueError('No nodes attribute found on given parent '
                             f'(got {self.parent}) {_NODE_VALUE_WARNING} ({self})')
        elif not (hasattr(self.parent, 'rect') or hasattr(self.parent, 'is_origin')):
            raise ValueError('No rect or is_origin attribute found on given parent '
                             f'(got {self.parent}) {_NODE_VALUE_WARNING} ({self})')
        self.parent.nodes.append(self)
        self.transform = Transform(*node_props[1:7], transform_update=self._transform_update)
        self._enabled = node_props[7]
        self.nodes = []

        if hasattr(self, 'event_handler'):
            self.scene().add_event_handler(self)
        # Get screen co-ordinates, shift position to be relative to the parent node
        self.rect = self.transform.rect()
        if not hasattr(self.parent, 'is_origin'):
            self.rect.move_ip(self.parent.rect.x, self.parent.rect.y)
        else:
            # Optimise method call if at top-level - position is not relative to any node
            self.global_rect = self.transform.rect
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

    def global_rect(self) -> pygame.Rect:
        """Calculate the on-screen rectangle of a node. Cached as Node.rect."""
        rect = self.transform.rect()
        parent = self.parent
        while not hasattr(parent, 'is_origin'):
            rect.move_ip(parent.transform.x, parent.transform.y)
            parent = parent.parent
        return rect

    def scene(self):
        """Get the scene that this node belongs to."""
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

    def _transform_update(self, name):
        """Update the rect attribute (on-screen position/size) for this
        node and all child nodes when its transform is modified."""
        if self.rect == self.global_rect():  # no changes to apply
            return

        if name in ('width', 'height'):
            self.on_resize()

        # Move the top-left of the rectangle if position changes or
        # the rectangle is resized about a point that is not the top-left
        if name in ('x', 'y') or (not self.transform.anchor_position == (0, 0)
                                  and name in ('width', 'height')):
            x, y = self.transform.x, self.transform.y
            if not hasattr(self.parent, 'is_origin'):
                x += self.parent.rect.x
                y += self.parent.rect.y
            self._set_rect_position(x, y)

    def on_resize(self):
        self.rect.size = self.transform.get_surface_size()

    def _set_visible(self, set_visible: bool):
        """Internal method to set the visible attribute of child sprites."""
        if self.nodes:
            for child in self.nodes:
                child._set_visible(set_visible)

    def _set_rect_position(self, x, y):
        """Internal method to set the rect attribute of child nodes."""
        x, y = self.transform.rect_position(x, y)
        self.rect.x, self.rect.y = x, y
        if self.nodes:
            for child in self.nodes:
                child._set_rect_position(x + child.transform.x, y + child.transform.y)

    def remove(self):
        """Fully delete a node and remove it from the tree."""
        if self in self.parent.nodes:
            self.parent.nodes.remove(self)
        self.transform.transform_update = None
        if hasattr(self, 'event_handler'):
            self.scene().remove_event_handler(self)
        for i in range(len(self.nodes)):
            self.nodes[0].remove()

    def order_before(self, before_node):
        """Move this node before a sibling node in the parent's node list
        using the list.insert() method. This method will not change the parent."""
        parent_nodes = self.parent.nodes
        parent_nodes.remove(self)
        try:
            index = parent_nodes.index(before_node)
        except ValueError as _error:
            print('Engine warning: Node.order_before() takes a sibling node as an argument, '
                  f'but a non-sibling node (got {before_node}) was supplied!')
            raise _error
        parent_nodes.insert(index, self)

    def order(self, index: int):
        """Move this node before the given index of the parent's node list
        using the list.insert() method. Negative indices from end."""
        parent_nodes = self.parent.nodes
        parent_nodes.remove(self)
        parent_nodes.insert(self, index)


class SpriteNode(Node, pygame.sprite.DirtySprite):
    def __init__(self, node_props: NodeProps, groups=None, image=None, fill_color=None):
        try:
            if groups is None or isinstance(groups, str):
                raise TypeError
            pygame.sprite.DirtySprite.__init__(self, groups)
        except TypeError:  # for example when groups = None (default)
            print('Engine warning: a SpriteNode was initialised with an incorrect group type '
                  f'(got {groups}). \nThis may be because the "group" parameter was missed.')
            pygame.sprite.DirtySprite.__init__(self)

        Node.__init__(self, node_props)
        # Show or hide the SpriteNode based on its parent nodes in the tree
        # If any parent node is disabled then its child nodes are not visible
        self._visible = self.world_visible()
        surface_size = self.transform.get_surface_size()

        if image is None:
            # Use the per-pixel alpha flag if given no/a transparent colour
            flags = pygame.SRCALPHA * (fill_color is None or len(fill_color) > 3)
            self.image = pygame.Surface(surface_size, flags)
            if fill_color is not None:
                self.image.fill(fill_color)
                self.fill_color = fill_color
        else:
            # Copy the given image and its flags including per-pixel alpha
            self.image = pygame.Surface(surface_size, image.get_flags(), image)

    def remove(self):
        pygame.sprite.Sprite.kill(self)
        Node.remove(self)

    def world_visible(self) -> bool:
        """Determine if the node should be visible, if all its parent nodes are
        enabled, or otherwise not visible. Cached as SpriteNode.visible."""
        visible = self._enabled
        parent = self.parent
        while visible and isinstance(parent, Node):
            visible = getattr(parent, 'visible', True) and parent.enabled
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
        self.image = pygame.Surface(self.transform.get_surface_size(),
                                    self.image.get_flags(), self.image)
        if getattr(self, 'fill_color', None) is not None:
            self.image.fill(self.fill_color)  # repaint fill colour
        if self.dirty < 2:
            self.dirty = 1
