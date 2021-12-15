import pygame


class Anchor:
    top = left = 0
    center = middle = 0.5
    bottom = right = 1

class NodeLocalProperties:
    def __init__(self, parent, x, y, width=0, height=0, anchor_x=0, anchor_y=0, rotation=0, enabled=True, visible=1):
        self.parent = parent
        self.enabled = enabled
        self.visible = visible
        self.transform = Transform(x, y, width, height, anchor_x, anchor_y, rotation)

    @classmethod
    def from_rect(cls, parent, rect, anchor_x=0, anchor_y=0, rotation=0, enabled=True, visible=1):
        return cls(parent, rect.x, rect.y, rect.width, rect.height, anchor_x, anchor_y, rotation, enabled, visible)

class Transform:
    def __init__(self, x, y, width=0, height=0, anchor_x=0, anchor_y=0, rotation=0):
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

    # def __add__(self, other):
    #     return LocalState(self.x + other.x, self.y + other.y, self.width, self.height,
    #                            self.anchor_x, self.anchor_y)

    def rect(self):
        return pygame.Rect(int(self.x - self.width * self.anchor_x),
                           int(self.y - self.height * self.anchor_y), int(self.width), int(self.height))

    # Getters and setters for transform properties
    @property
    def position(self):
        return self.x, self.y

    @position.setter
    def position(self, position_x_y):
        self.x, self.y = position_x_y

    @property
    def size(self):
        return self.width, self.height

    @size.setter
    def size(self, width_height):
        self.width, self.height = width_height

    @property
    def anchor(self):
        return self.width, self.height

    @anchor.setter
    def anchor(self, anchor_x_y):
        self.anchor_x, self.anchor_y = anchor_x_y

class Node:
    def __init__(self, node_props: NodeLocalProperties):
        assert isinstance(node_props, NodeLocalProperties)
        self.parent = node_props.parent
        self.visible = node_props.visible
        self._enabled = node_props.enabled
        self.transform = node_props.transform
        # For each property in local_properties, set this on the node
        # self.__dict__.update(local_properties.__dict__)
        self.parent.nodes.append(self)
        self.nodes = []

    def update(self):
        for child in self.nodes:
            if child.enabled:
                child.update()

    def draw(self, surface):
        for child in self.nodes:
            child.draw(surface)

    def add_child(self, child):
        self.nodes.append(child)
        child.parent = self

    def remove_child(self, child):
        if child in self.nodes:
            self.nodes.remove(child)
            child.parent = None

    def world_rect(self):
        if isinstance(self.parent, Node):
            parent_rect = self.parent.world_rect()
            return self.transform.rect().move(parent_rect.x, parent_rect.y)
        else:
            return self.transform.rect()

    def __del__(self):
        self.parent.remove_child(self)

        for i in range(len(self.nodes)):
            child = self.nodes.pop(0)
            if child:
                del child

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, set_enable: bool):
        self._enabled = set_enable
        self.set_visible_on_self_and_all_children(int(set_enable))

    def set_visible_on_self_and_all_children(self, set_visible):
        if self.visible < 2:
            self.visible = set_visible and self._enabled
        for child in self.nodes:
            child.set_visible_on_self_and_all_children(set_visible)


class SpriteNode(pygame.sprite.DirtySprite, Node):
    def __init__(self, node_props: NodeLocalProperties, *groups, image=None, fill_color=None):
        if isinstance(groups[0], pygame.sprite.AbstractGroup):
            pygame.sprite.DirtySprite.__init__(self, *groups)
        else:
            print('Engine warning: a SpriteNode was initialised without a group or with an incorrect type.\n'
                  + 'This may be because the "group" parameter was missed.')
            pygame.sprite.DirtySprite.__init__(self)

        Node.__init__(self, node_props)
        self.rect = self.world_rect()
        print(f'{self}, rect {self.rect}, parent {self.parent}, {self.groups()}')

        if image:
            self.image = pygame.Surface(self.transform.size, 0, image)
        else:
            self.image = pygame.Surface(self.transform.size)
            if fill_color:
                self.image.fill(fill_color)

    def update(self):
        Node.update(self)
        self.rect = self.world_rect()

    def __del__(self):
        print("del", self)
        pygame.sprite.Sprite.kill(self)
        Node.__del__(self)
