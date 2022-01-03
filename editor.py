import pygame
import engine.text as text
import engine.interface as interface
from engine.base_scene import Scene
from engine.base_node import NodeProperties
from constants import *

from tree_tab import TreeTab

class Editor(Scene):
    """The editor that enables the user to edit a scene."""
    def __init__(self, screen, clock, user_scene):
        super().__init__(screen, clock)

        self.user_scene = user_scene(screen, clock)
        self.tree_tab = TreeTab(self.user_scene)

    def update(self):
        super().update()
