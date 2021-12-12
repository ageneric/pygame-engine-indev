import pygame
import engine.text as text
import engine.interface as interface
from engine.base_scene import Scene
from engine.base_node import Node, SpriteNode, NodeLocalProperties
from constants import *

from tree_tab import TreeTab

class ExampleBlank(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)

        self.n = Node(NodeLocalProperties(self, 30, 30))
        Node(NodeLocalProperties(self.n, 75, 30))

    def update(self):
        super().update()
        self.n.transform.x = self.n.transform.x + 1 % self.display_size_x

class ExampleHandling(Scene):
    """Demo interface components and event handling."""
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.group = pygame.sprite.Group()

        def callback():
            print('button click -> demo')

        button = interface.Button(NodeLocalProperties(self, 100, 100, 150, 50),
                                  'Demo clickable', callback, self.group, background=C_LIGHT)
        image = pygame.image.load('Assets/Placeholder.png').convert()
        button2 = interface.Button(NodeLocalProperties(self, 100, 200, 32, 32),
                                   'Image clickable', callback, self.group, image=image)
        self.event_handlers.append(button)
        self.event_handlers.append(button2)
        self.groups.append(self.group)

    def handle_events(self, pygame_events):
        for event in pygame_events:
            if event.type in interface.MOUSE_EVENTS:
                for button in self.event_handlers:
                    button.mouse_event(event)


class ExampleDetail(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.group = pygame.sprite.Group()

        self.tree_tab = TreeTab(NodeLocalProperties(self, 30, 20, self.display_size_x - 30, 125),
                                self.group, None)

        self.groups.append(self.group)

    def set_ref(self, ref):
        self.tree_tab.ref = ref

    def draw(self):
        self.screen.fill(C_LIGHT)
        super().draw()

        message = f'{self.clock.get_rawtime()}ms processing time / tick'
        text.draw(self.screen, message, (30, 5),
                  color=C_DARK_ISH, justify=(False, False))
