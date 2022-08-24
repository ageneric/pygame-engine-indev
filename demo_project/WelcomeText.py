import pygame
from engine.base_node import SpriteNode
from engine import text
from engine import interface

class WelcomeText(SpriteNode):
    def __init__(self, node_props, groups, message=None):
        super().__init__(node_props, groups)
        self.message = message

    def draw(self):
        super().draw()
        if self.dirty and self.visible:
            # This sprite's image is self.image, a rectangular Pygame Surface
            # Filling the colour in (optional)
            self.image.fill((45, 10, 25))

            # Drawing three diagonal lines that become darker left to right
            line_end = self.transform.height
            for i in range(3):
                color = interface.brighten_color((45, 10, 25), 20 - i*4)
                pygame.draw.line(self.image, color, (i * 10, line_end), (line_end + i*10, 0), 6)

            # Drawing the message
            text.draw(self.image, self.message, (line_end, 5), color=(200, 200, 200))
