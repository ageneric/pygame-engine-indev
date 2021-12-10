import pygame
import engine.text as text
from engine.base_scene import Scene
from engine.base_node import Node, SpriteNode, NodeLocalProperties

class SceneTest1(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
