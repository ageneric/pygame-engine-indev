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
        demo_button_1 = self.nodes[1].nodes[0]
        demo_button_1.message = 'Press "Play" to enable events'
        demo_button_1.callback = demo_callback
        demo_button_1.style.dict['color'] = C_DARK
        demo_button_1.style.dict['background'] = C_LIGHT

        # Nodes can be created through code, though changes to
        # these arguments in the Inspector tab will not persist
        demo_button_2 = interface.Button(NodeProps(self.nodes[1], 45, 30, 250, 40),
                                         self.group_draw, 'Change my layer in the Inspector',
                                         demo_callback, style=blue_style)

        image = pygame.image.load('Assets/Placeholder.png').convert()
        visible_toggle = interface.Toggle(NodeProps(self, 330, 63, 32, 32), self.group_draw,
                                          '+/-', self.use_visible_toggle, image=image, color=C_DARK)
        visible_toggle.reorder_before(self.nodes[2])

        self.test_entry = interface.TextEntry(NodeProps(self, 10, 125, 200, 20), self.group_draw,
                                              'Text value', demo_callback, style=blue_style)

        self.test_grid = interface.SpriteListLayout(NodeProps(self.nodes[3], 0, 50, 200, 200),
                                                    self.group_draw, grid_example_generator(),
                                                    background=C_LIGHT)

    def use_visible_toggle(self, checked):
        self.nodes[1].enabled = not checked


class ExampleBlank(Scene):
    """This is the minimum required code for a scene."""
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
