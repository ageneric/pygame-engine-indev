import pygame
from engine.scene import Scene
from engine.node import NodeProps, SpriteNode
import engine.interface as interface
import engine.text as text
from constants import *

def grid_example_generator():
    yield SpriteNode, 10, dict(fill_color=C_RED)
    yield SpriteNode, 20, dict(fill_color=C_GREEN)
    yield SpriteNode, 30, dict(fill_color=C_BLUE)

class ExampleScene(Scene):
    """Demo interface components and event handling."""
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.load_template()

        self.large_font = pygame.font.SysFont('Verdana, Calibri', 16)
        blue_style = interface.Style(color=(210, 220, 255), background=C_DARK_BLUE)

        def demo_callback(*args):
            print(f'demo callback -> {args}')

        # Nodes can be modified by setting their attributes directly
        # Button 1
        self.nodes[1].nodes[0].message = 'Press "Play" to enable events'
        self.nodes[1].nodes[0].callback = demo_callback
        self.nodes[1].nodes[0].style.dict['color'] = C_DARK
        self.nodes[1].nodes[0].style.dict['background'] = C_LIGHT

        # Nodes can be created through code, though changes to
        # these arguments in the Inspector tab will not persist
        # Button 2
        demo_button2 = interface.Button(NodeProps(self.nodes[1], 45, 30, 250, 40),
                                        self.draw_group, 'Change my layer in the Inspector',
                                        demo_callback, style=blue_style)

        image = pygame.image.load('Assets/Placeholder.png').convert()
        toggle_visible_button = interface.Button(NodeProps(self, 330, 63, 32, 32), self.draw_group,
                                                 '+/-', self.toggle_button, image=image, color=C_DARK)

        self.test_entry = interface.TextEntry(NodeProps(self, 10, 125, 200, 20), self.draw_group,
                                              'Text value', demo_callback, style=blue_style)

        self.test_grid = interface.SpriteListLayout(NodeProps(self.nodes[2], 0, 50, 200, 200),
                                                    self.draw_group, grid_example_generator(),
                                                    background=C_LIGHT)

    def toggle_button(self):
        self.nodes[1].enabled = not self.nodes[1].enabled


class ExampleBlank(Scene):
    """This is the minimum required code for a scene."""
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
