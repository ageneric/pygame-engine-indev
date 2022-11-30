scene_template_code = """import pygame
from engine.base_scene import Scene

class {0}(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.load_template()
    
    # Called every frame. Optional.
    def update(self):
        super().update()
    
    # Called every frame. Optional.
    def draw(self):
        super().draw()
"""

node_subclass_code = """import pygame
from engine.base_node import Node, SpriteNode, NodeProps

# Useful properties: self.parent, self.transform, self.enabled, self.rect, self.nodes
# Useful methods: self.scene(), self.remove()
# For SpriteNode use: self.image, self.visible; all pygame.sprite.DirtySprite methods

class {0}({1}):
    def __init__(self, node_props{2}):
        super().__init__(node_props{2})
    
    # Called every frame on every node in tree order. Optional.
    def update(self):
        super().update()
    
    # Called every frame on every node in tree order. Optional.
    def draw(self):
        super().draw()
"""
