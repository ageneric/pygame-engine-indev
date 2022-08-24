from engine.base_scene import Scene

class ExampleRemote(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.load_template()

from engine.base_node import NodeProperties, SpriteNode
from engine.interface import brighten_color, saturate_color
import pygame

import engine.interface as interface
from constants import *

class ExampleColor(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)

    def draw(self):
        super().draw()
        for i in range(50):  # white to black
            color = brighten_color((0, 0, 0), 2*i)
            pygame.draw.rect(self.screen, color, (i*4, 0, 4, 15))
        for i in range(50):  # black to white
            color = brighten_color((255, 255, 255), -2*i)
            pygame.draw.rect(self.screen, color, (i*4, 20, 4, 15))
        for i in range(50):
            color = brighten_color((128, 0, 0), 2*i)
            pygame.draw.rect(self.screen, color, (i*4, 40, 4, 15))
        for i in range(50):
            color = brighten_color((0, 64, 192), -2*i)
            pygame.draw.rect(self.screen, color, (i*4, 60, 4, 15))

        pygame.display.flip()

def grid_example_generator():
    yield SpriteNode, dict(fill_color=C_RED)
    yield SpriteNode, dict(fill_color=C_GREEN)
    yield SpriteNode, dict(fill_color=C_BLUE)

class ExampleHandling(Scene):
    """Demo interface components and event handling."""
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.create_draw_group((8, 6, 6))

        def demo_callback(*args):
            print(f'demo callback -> {args}')

        self.demo_button = interface.Button(NodeProperties(self, 100, 100, 150, 50), self.draw_group,
                                            'Demo clickable', demo_callback, background=C_LIGHT)

        self.demo_button2 = interface.Button(NodeProperties(self, 125, 125, 250, 50), self.draw_group,
                                             'Demo clickable 2', demo_callback, background=C_DARK)

        image = pygame.image.load('Assets/Placeholder.png').convert()
        toggle_visible_button = interface.Button(NodeProperties(self, 100, 50, 32, 32), self.draw_group,
                                                 'Image clickable', self.toggle_button, image=image)

        self.test_entry = interface.TextEntry(NodeProperties(self, 25, 25, 350, 20), self.draw_group,
                                              '12345', demo_callback,
                                              background=C_DARK_BLUE)

        self.test_grid = interface.SpriteList(NodeProperties(self, 100, 200, 200, 200),
                                              self.draw_group, grid_example_generator(),
                                              background=C_LIGHT, horizontal=True)

        self._first_frame = True  # temporary testing measure

    def update(self):
        super().update()
        if self._first_frame:
            self._first_frame = False

    def toggle_button(self):
        self.demo_button.enabled = not self.demo_button.enabled
        self.demo_button2.enabled = not self.demo_button2.enabled


class ExampleBlank(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)

    def update(self):
        super().update()
