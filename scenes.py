import pygame
import engine.text as text
from engine.base_scene import Scene
from engine.base_node import Node, SpriteNode, NodeLocalProperties
from constants import *

from tree_tab import TreeTab

class ExampleBlank(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)

        Node(NodeLocalProperties(self, 30, 30))

class ExampleDetail(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.group = pygame.sprite.Group()

        self.tree_tab = TreeTab(NodeLocalProperties(self, 30, 20, display_width - 30, 125),
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
