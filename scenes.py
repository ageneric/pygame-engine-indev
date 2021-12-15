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
        self.background = pygame.Surface(self.display_size)
        self.background.fill((0, 0, 8))
        self.group = pygame.sprite.LayeredDirty()

        def callback():
            print('button click -> demo')

        self.button = interface.Button(NodeLocalProperties(self, 100, 100, 150, 50),
                                       'Demo clickable', callback, self.group, background=C_LIGHT)
        image = pygame.image.load('Assets/Placeholder.png').convert()
        toggle_visible_button = interface.Button(NodeLocalProperties(self, 100, 200, 32, 32),
                                                 'Image clickable', self.toggle_button, self.group,
                                                 image=image)
        self.event_handlers.append(self.button)
        self.event_handlers.append(toggle_visible_button)
        self.groups.append(self.group)

        self.group2 = pygame.sprite.LayeredDirty()

        self.test_button = interface.Button(NodeLocalProperties(self, 125, 125, 250, 50),
                                            'Second group clickable', callback, self.group,
                                            background=C_DARK)
        self.event_handlers.append(self.test_button)

        self.test_node = Node(NodeLocalProperties(self.test_button, 200, 200))

        self.groups.append(self.group2)

    def draw(self):
        for group in self.groups:
            group.clear(self.screen, self.background)
        # self.screen.fill((0, 0, 8))

        super().draw()

    def toggle_button(self):
        self.button.enabled = not self.button.enabled
        self.test_button.enabled = not self.test_button.enabled

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
        self.recent_frames_ms = []

    def set_ref(self, ref):
        self.tree_tab.ref = ref

    def draw(self):
        self.screen.fill(C_LIGHT)
        super().draw()

        rawtime = self.clock.get_rawtime()
        self.recent_frames_ms.append(rawtime)
        if len(self.recent_frames_ms) > FPS:
            self.recent_frames_ms.pop(0)

        message = f'{rawtime}ms processing time / tick ({sum(self.recent_frames_ms)}ms / s)'
        text.draw(self.screen, message, (30, 5),
                  color=C_DARK_ISH, justify=(False, False))
