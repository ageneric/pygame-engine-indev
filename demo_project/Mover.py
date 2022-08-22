import pygame
from engine.base_node import Node

class Mover(Node):
    # Allows the node to receive all events with a pygame.KEYDOWN type.
    event_handler = [pygame.KEYDOWN]

    def __init__(self, node_props):
        super().__init__(node_props)
        self.move_towards = 300

    def update(self):
        super().update()
        # While in play mode / running as a standalone program
        # This node will move towards the move_towards value.
        self.transform.x -= (self.transform.x - self.move_towards) / 60

    def event(self, event):
        # While in play mode / running as a standalone program
        # Receives pygame.KEYDOWN events - press LeftArrow or RightArrow.
        if event.key == pygame.K_RIGHT:
            self.move_towards = 350
        elif event.key == pygame.K_LEFT:
            self.move_towards = 250
