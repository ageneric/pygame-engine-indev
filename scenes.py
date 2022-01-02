import pygame
import engine.text as text
import engine.interface as interface
from engine.base_scene import Scene
from engine.base_node import Node, SpriteNode, NodeProperties
from constants import *

from tree_tab import TreeTabGrid

class ExampleBlank(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)

        self.n = Node(NodeProperties(self, 30, 30))
        Node(NodeProperties(self, 75, 75))

    def update(self):
        super().update()
        self.n.transform.x = self.n.transform.x + 1 % self.screen_size_x

def grid_example_generator():
    for i in range(2):
        yield SpriteNode, dict(fill_color=C_RED)

class ExampleHandling(Scene):
    """Demo interface components and event handling."""
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.create_draw_group((8, 6, 6))

        def demo_callback(*args):
            print(f'demo callback -> {args}')
        
        self.button = interface.Button(NodeProperties(self, 100, 100, 150, 50), self.draw_group,
                                       'Demo clickable', demo_callback, background=C_LIGHT)
        image = pygame.image.load('Assets/Placeholder.png').convert()
        toggle_visible_button = interface.Button(NodeProperties(self, 100, 200, 32, 32), self.draw_group,
                                                 'Image clickable', self.toggle_button,
                                                 image=image)
        self.mouse_handlers.append(self.button)
        self.mouse_handlers.append(toggle_visible_button)

        self.test_button = interface.Button(NodeProperties(self, 125, 125, 250, 50), self.draw_group,
                                            'Second group clickable', demo_callback,
                                            background=C_DARK)
        self.mouse_handlers.append(self.test_button)

        self.test_entry = interface.TextEntry(NodeProperties(self, 125, 425, 350, 20), self.draw_group,
                                              '12345', demo_callback, allow_characters='0123456789.',
                                              background=C_DARK)

        self.test_grid = interface.SpriteGrid(NodeProperties(self, 200, 200, 200, 200),
                                              self.draw_group, grid_example_generator(), background=C_LIGHT)

    def toggle_button(self):
        self.button.enabled = not self.button.enabled
        self.test_button.enabled = not self.test_button.enabled

    def handle_events(self, pygame_events):
        for event in pygame_events:
            if event.type in interface.MOUSE_EVENTS:
                for button in self.mouse_handlers:
                    button.mouse_event(event)
        self.test_entry.events(pygame_events)

class ExampleTree(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.create_draw_group((8, 6, 6))

        a = SpriteNode(NodeProperties(self, 20, 20, 20, 20), self.draw_group, fill_color=C_LIGHT)
        b = SpriteNode(NodeProperties(a, 20, 20, 20, 20), self.draw_group, fill_color=C_LIGHT_ISH)
        c = SpriteNode(NodeProperties(self, 20, 80, 20, 20), self.draw_group, fill_color=C_LIGHT)
        d = SpriteNode(NodeProperties(c, 20, 20, 20, 20), self.draw_group, fill_color=C_LIGHT_ISH)

    def handle_events(self, pygame_events):
        for event in pygame_events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.nodes[0].enabled = not self.nodes[0].enabled
                if event.key == pygame.K_2:
                    self.nodes[0].nodes[0].enabled = not self.nodes[0].nodes[0].enabled
                if event.key == pygame.K_3:
                    self.nodes[1].enabled = not self.nodes[1].enabled
                if event.key == pygame.K_4:
                    self.nodes[1].nodes[0].enabled = not self.nodes[1].nodes[0].enabled


class ExampleDetail(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.group = pygame.sprite.Group()

        self.groups.append(self.group)
        self.recent_frames_ms = []

    def set_ref(self, ref):
        self.tree_tab = TreeTabGrid(NodeProperties(self, 30, 20, self.screen_size_x - 30, 125, enabled=False),
                                    self.group, ref, spacing=13, background=C_LIGHT_ISH, color=C_DARK)

    def draw(self):
        super().draw()
        self.screen.fill(C_LIGHT)
        self.group.draw(self.screen)

        rawtime = self.clock.get_rawtime()
        self.recent_frames_ms.append(rawtime)
        if len(self.recent_frames_ms) > FPS:
            self.recent_frames_ms.pop(0)
            message = f'{rawtime}ms processing time / frame ({sum(self.recent_frames_ms)}ms / s)'
        else:
            message = f'{rawtime}ms processing time / frame'
            
        text.draw(self.screen, message, (30, 5),
                  color=C_DARK_ISH, justify=(False, False))
