import pygame
from engine.base_scene import Scene
from engine.base_node import NodeProperties, SpriteNode
import engine.interface as interface
import engine.text as text
from constants import *

def grid_example_generator():
    yield SpriteNode, dict(fill_color=C_RED)
    yield SpriteNode, dict(fill_color=C_GREEN)
    yield SpriteNode, dict(fill_color=C_BLUE)

class ExampleScene(Scene):
    """Demo interface components and event handling."""
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.load_template()

        self.large_font = pygame.font.SysFont('Verdana, Calibri', 16)

        def demo_callback(*args):
            print(f'demo callback -> {args}')

        # Nodes can be created by setting their attributes directly
        # Button 1
        self.nodes[1].nodes[0].message = 'Press "Play" to enable events'
        self.nodes[1].nodes[0].callback = demo_callback
        self.nodes[1].nodes[0].style.dict['background'] = C_LIGHT

        # Nodes can be created through code, though changes to
        # these arguments in the Inspector tab will not persist
        # Button 2
        self.demo_button2 = interface.Button(NodeProperties(self.nodes[1], 45, 30, 250, 40), self.draw_group,
                                             'Change my layer in the Inspector', demo_callback, background=C_DARK)

        image = pygame.image.load('Assets/Placeholder.png').convert()
        toggle_visible_button = interface.Button(NodeProperties(self, 330, 44, 32, 32), self.draw_group,
                                                 'Click', self.toggle_button, image=image)

        self.test_entry = interface.TextEntry(NodeProperties(self, 10, 125, 200, 20), self.draw_group,
                                              '12345', demo_callback, allow_characters='1234567890. ',
                                              background=C_DARK_BLUE)

        self.test_grid = interface.SpriteList(NodeProperties(self.nodes[2], 0, 50, 200, 200),
                                              self.draw_group, grid_example_generator(),
                                              background=C_LIGHT)

    def toggle_button(self):
        self.demo_button2.enabled = not self.demo_button2.enabled


class ExampleBlank(Scene):
    """This is the minimum required code for a scene."""
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
