import pygame
from .base_scene import Scene


class Node:
    def __init__(self, transform, parent=None, enabled=True, visible=True):
        if isinstance(transform, Transform):
            self.transform = transform
        elif isinstance(transform, pygame.Rect):
            self.transform = Transform.from_rect(transform)
        else:
            self.transform = Transform(*transform)

        if parent:
            parent.nodes.append(self)

        self.parent = parent
        self.enabled = enabled
        self.visible = visible

        self.nodes = []

    def update(self):
        if self.enabled:
            for child in self.nodes:
                child.update()

    def draw(self, surface):
        if self.visible:
            for child in self.nodes:
                child.draw(surface)

    def add_child(self, child):
        self.nodes.append(child)
        child.parent = self

    def remove_child(self, child):
        if child in self.nodes:
            self.nodes.remove(child)
            child.parent = None

    def world_transform(self):
        if self.parent and not isinstance(self.parent, Scene):
            return self.transform + self.parent.world_transform()
        else:
            return self.transform

    def world_rect(self) -> pygame.Rect:
        return self.transform.rect()

    def __del__(self):
        self.parent.remove_child(self)

        for i in range(len(self.nodes)):
            child = self.nodes.pop(0)
            if child:
                del child


class SpriteNode(pygame.sprite.DirtySprite, Node):
    def __init__(self, transform, image, parent=None, group=None, enabled=True, visible=True):
        Node.__init__(self, transform, parent, enabled, visible)
        if group is not None:
            pygame.sprite.Sprite.__init__(self, group)
            print(self)
        else:
            pygame.sprite.Sprite.__init__(self)
        if group:
            self.group = group
            group.add(self)
        self.rect = self.world_rect()
        print(f'{self=} {self.rect=} {self.parent=} {self.group=}')
        self.image = image

    def update(self):
        Node.update(self)
        self.rect = self.world_rect()

    @classmethod
    def single_color(cls, transform, color, parent=None, group=None, enabled=True, visible=True):
        image = pygame.Surface((transform.width, transform.height))
        image.fill(color)
        return cls(transform, image, parent, group, enabled, visible)

    def __del__(self):
        pygame.sprite.Sprite.kill(self)
        print("del", self)
        # Node.__del__(self)

    def handle_events(self, events):
        self.event_handlers = {}
        # {pygame.KEYDOWN: function}

        for event in events:
            if event.type in self.event_handlers.keys():
                self.event_handlers[event.type](event)

"""
    @self.event(pygame.KEYDOWN)

@window.event
def on_draw ():
    pass

@window.event
def on_click (x, y, modifiers):
    pass
"""
"""# Get the method with the name draw() if it exists and call it
draw_method = getattr(node, "draw", None)
if callable(draw_method):
    draw_method(self.screen)"""

class Anchor:
    top = left = 0
    center = middle = 0.5
    bottom = right = 1


class Transform:
    def __init__(self, x, y, width=0, height=0, anchor_x=0, anchor_y=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y

    def __repr__(self) -> str:
        return f'(XY {self.x}, {self.y}, WH {self.width}, {self.height}, anchorXY {self.anchor_x}, {self.anchor_y})'

    @classmethod
    def from_rect(cls, rect, x_scale=1, y_scale=1, rotation=0):
        return cls(rect.x, rect.y, rect.width, rect.height, x_scale, y_scale, rotation)

    def __add__(self, other):
        return Transform(self.x + other.x, self.y + other.y, self.width, self.height,
                         self.anchor_x, self.anchor_y)

    def rect(self):
        return pygame.Rect(int(self.x - self.width * self.anchor_x),
                           int(self.y - self.height * self.anchor_y), int(self.width), int(self.height))

    @property
    def position(self):
        return [self.x, self.y]

    @position.setter
    def position(self, value):
        self.x, self.y = value

    @property
    def size(self):
        return [self.width, self.height]

    @size.setter
    def size(self, value):
        self.width, self.height = value

    # TODO: anchor setter
    # TODO: scaling
