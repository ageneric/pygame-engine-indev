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

    def update(self):
        super().update()

def grid_example_generator():
    yield SpriteNode, dict(fill_color=C_RED)
    yield SpriteNode, dict(fill_color=C_GREEN)
    yield SpriteNode, dict(fill_color=C_BLUE)

class ExampleHandling(Scene):
    """Demo interface components and event handling."""
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.create_draw_group((8, 6, 6))

        def demo_callback(*args):
            print(f'demo callback -> {args}')

        self.demo_button = interface.Button(NodeProperties(self, 100, 100, 150, 50), self.draw_group,
                                            'Demo clickable', demo_callback, background=C_LIGHT)

        self.demo_button2 = interface.Button(NodeProperties(self, 125, 125, 250, 50), self.draw_group,
                                             'Demo clickable 2', demo_callback, background=C_DARK)

        image = pygame.image.load('Assets/Placeholder.png').convert()
        toggle_visible_button = interface.Button(NodeProperties(self, 100, 50, 32, 32), self.draw_group,
                                                 'Image clickable', self.toggle_button, image=image)

        self.test_entry = interface.TextEntry(NodeProperties(self, 25, 25, 350, 20), self.draw_group,
                                              '12345', demo_callback, allow_characters='0123456789.',
                                              background=C_DARK)

        self.test_grid = interface.SpriteList(NodeProperties(self, 100, 200, 200, 200),
                                              self.draw_group, grid_example_generator(), background=C_LIGHT)

        self._first_frame = True  # temporary testing measure

    def update(self):
        super().update()
        if self._first_frame:
            self._first_frame = False

    def toggle_button(self):
        self.demo_button.enabled = not self.demo_button.enabled
        self.demo_button2.enabled = not self.demo_button2.enabled

class ExampleTree(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.create_draw_group((8, 6, 6))

        # for i in range(200):
        a = SpriteNode(NodeProperties(self, 20, 20, 20, 20), self.draw_group, fill_color=C_LIGHT)
        b = SpriteNode(NodeProperties(a, 20, 20, 20, 20), self.draw_group, fill_color=C_LIGHT_ISH)
        c = SpriteNode(NodeProperties(self, 20, 80, 20, 20), self.draw_group, fill_color=C_LIGHT)
        d = SpriteNode(NodeProperties(c, 20, 20, 20, 20), self.draw_group, fill_color=C_LIGHT_ISH)

    # def update(self):
    #     super().update()
    #     for i in self.nodes:
    #         i.transform.x += 1
    #         i.nodes[0].transform.x += 1

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
                if event.key == pygame.K_q:
                    self.nodes[0].transform.x = (self.nodes[0].transform.x + 1) % 600
                if event.key == pygame.K_w:
                    self.nodes[0].nodes[0].transform.x = (self.nodes[0].nodes[0].transform.x + 1) % 600


class ExampleDetail(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.group = pygame.sprite.Group()

        self.groups.append(self.group)
        self.recent_frames_ms = []

    def set_ref(self, ref):
        self.tree_tab = TreeTabGrid(NodeProperties(self, 30, 20, self.screen_size_x - 30, 125, enabled=False),
                                    self.group, ref, spacing=13, background=C_LIGHT_ISH, color=C_DARK)

    def update(self):
        super().update()

    def draw(self):
        super().draw()

        self.screen.fill(C_LIGHT)
        if self.tree_tab.visible:
            self.group.draw(self.screen)
            self.tree_tab.dirty = False

        rawtime = self.clock.get_rawtime()
        self.recent_frames_ms.append(rawtime)
        if len(self.recent_frames_ms) > 30:
            self.recent_frames_ms.pop(0)
            message = f'{sum(self.recent_frames_ms) * FPS // 30}ms / s ({rawtime}ms / frame)'
        else:
            message = f'{rawtime}ms processing / frame'
            
        text.draw(self.screen, message, (30, 5),
                  color=C_DARK_ISH, justify=(False, False))
