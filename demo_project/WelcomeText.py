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
            # This sprite's image is self.image - a (rectangular) Pygame Surface
            # Filling the colour in
            self.image.fill((45, 10, 25))

            # Drawing a brighter underline at the bottom of the box
            underline = (0, self.transform.height - 2, self.transform.width, 2)
            pygame.draw.rect(self.image, interface.brighten_color((45, 10, 25), 20), underline)

            # Drawing a decorative diagonal line
            line_end = self.transform.height
            pygame.draw.line(self.image, interface.brighten_color((45, 10, 25), 20),
                             (0, line_end), (line_end, 0), 6)

            # Drawing the message
            text.draw(self.image, self.message, (line_end, 5), color=(200, 200, 200))
