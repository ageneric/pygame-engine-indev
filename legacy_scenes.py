from tkinter.filedialog import askopenfilename
from tkinter import Tk
Tk().withdraw()  # Do not show a root window.

import pygame as pg
# from interface import Button, Toggle, MOUSE_EVENTS
from unused_component_based_node import ComponentBasedNode, ImageComponent
import legacy_text
from engine.base_scene import Scene
from engine.interface import Button
from constants import *
from legacy_interface import MOUSE_EVENTS
from tree_tab import TreeTab
from engine.base_node import Node

from bad_logging import dlog
from random import randint

def end_of_path(file_directory, depth=2) -> str:
    """Get the last (depth) components of the file path."""
    return '/'.join(file_directory.split(r'/')[-depth:])

"""
class Menu(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)

        pg.display.set_caption('Coordinate Box (Menu)')
        self.file_dir = None
        self.file_preview = ''

        self.b_select_file = Button((40, 70, 170, 36), 'Select file', self.select_file,
                                    color=C_DARK, background=C_LIGHT)
        self.actors.append(self.b_select_file)
        self.b_change_scene = Button((40, 120, 170, 39), 'Edit', self.go_scene_editor,
                                     color=C_DARK, background=C_LIGHT, background_disabled=C_DARK_ISH)
        self.actors.append(self.b_change_scene)
        self.b_change_scene.state = Button.disabled

    def draw(self):
        self.screen.fill(C_DARK)
        for actor in self.actors:
            actor.draw(self.screen)

        legacy_text.draw(self.screen, 'Menu', (40, 40), justify=(False, False), static=True)

        if self.display_size_y() > 400:
            message = f'{self.clock.get_rawtime()}ms processing time / tick'
            legacy_text.draw(self.screen, message, (40, self.display_size_y() - 50),
                             color=C_DARK_ISH, justify=(False, True))

        if self.file_dir:
            message = f'File: {end_of_path(self.file_dir)}'
            legacy_text.draw(self.screen, message, (240, 40))
            legacy_text.box(self.screen, self.file_preview, (240, 70), 260, 40, color=C_GREEN)

    def handle_events(self, pygame_events):
        for event in pygame_events:
            if event.type in MOUSE_EVENTS:
                self.b_select_file.mouse_event(event)
                self.b_change_scene.mouse_event(event)

    def reset_file(self):
        self.file_preview = ''
        self.file_dir = None
        self.b_change_scene.state = Button.disabled

    def select_file(self):
        # Create an "Open" dialog box, return the path selected.
        try:
            self.file_dir = askopenfilename()
            pg.event.pump()  # Allow pygame to process internal events ("not responding").

            # Open the file to generate a preview and check it is readable.
            with open(self.file_dir, 'r', encoding='utf-8') as f:
                self.file_preview = f.read(32)
        except Exception as _error:
            print(f'Critical error opening file:\n    {_error}')
            self.reset_file()
            return

        if len(self.file_preview) >= 32:
            self.file_preview += '...'
        self.file_preview = self.file_preview.replace('\n', ' ¬ ')
        self.b_change_scene.state = Button.idle

    def go_scene_editor(self):
        self.change_scene(Editor, self.file_dir)


def rect_translation(start_x, start_y, end_x, end_y):
    return start_x, start_y, start_x - end_x, end_y - start_y

class Editor(Scene):
    cursor, add_rect = range(2)
    bar_height = 56

    def __init__(self, screen, clock, file_dir):
        super().__init__(screen, clock)

        pg.display.set_caption(f'Coordinate Box - {end_of_path(file_dir)}')
        self.tool = None
        self.buttons = []

        self.b_use_cursor = Toggle((0, 0, 90, self.bar_height), 'Cursor',
                                   self.set_tool_cursor, background=C_DARK,
                                   background_toggle=C_LIGHT, color_toggle=C_DARK)
        self.buttons.append(self.b_use_cursor)
        self.b_use_rect = Toggle((90, 0, 90, self.bar_height), 'Draw',
                                 self.set_tool_rect, background=C_DARK,
                                 background_toggle=C_LIGHT, color_toggle=C_DARK)
        self.buttons.append(self.b_use_rect)

        self.mouse_x = 0
        self.mouse_y = 0
        self.drag_event = False
        self.drag_from_x = 0
        self.drag_from_y = 0

    def draw(self):
        self.screen.fill(C_LIGHT)
        for actor in self.actors:
            actor.draw(self.screen)

        if self.tool == Editor.cursor:
            about_message = f"{self.mouse_x}, {self.mouse_y}"
            if self.mouse_y > self.display_size_y() - 30:
                legacy_text.draw(self.screen, about_message, (self.mouse_x, self.mouse_y - 14),
                                 color=C_DARK)
            else:
                legacy_text.draw(self.screen, about_message, (self.mouse_x, self.mouse_y + 24),
                                 color=C_DARK)
        elif self.tool == Editor.add_rect:
            pg.draw.rect(self.screen, C_BLUE, (self.mouse_x - 1, self.mouse_y - 1, 3, 3))

        if self.display_size_y() > 400:
            message = f'{self.clock.get_rawtime()}ms processing time / tick'
            legacy_text.draw(self.screen, message, (40, self.display_size_y() - 50),
                             color=C_DARK_ISH, justify=(False, True))

        pg.draw.rect(self.screen, C_DARK, (0, 0, self.display_size_x(), self.bar_height))
        for button in self.buttons:
            button.draw(self.screen)
        pg.draw.rect(self.screen, C_DARK, (0, self.bar_height - 2, self.display_size_x(), 2))

    def handle_events(self, pygame_events):
        for event in pygame_events:
            if event.type in MOUSE_EVENTS:
                for button in self.buttons:
                    button.mouse_event(event)

                if event.type == pg.MOUSEMOTION:
                    self.mouse_x, self.mouse_y = event.pos
                elif event.type == pg.MOUSEBUTTONDOWN:
                    self.drag_from_x, self.drag_from_y = event.pos
                    self.drag_event = False
                elif event.type == pg.MOUSEBUTTONUP:
                    self.drag_event = True

            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.set_tool(None, None)

    def set_tool(self, clicked_button, tool_value):
        # Set the tool option. Double-clicking an option will deselect all.
        if tool_value is None or tool_value == self.tool:
            self.tool = None
        else:
            self.tool = tool_value

        for button in self.buttons:
            if button is not clicked_button:
                button.checked = False

    def set_tool_cursor(self):
        self.set_tool(self.b_use_cursor, Editor.cursor)

    def set_tool_rect(self):
        self.set_tool(self.b_use_rect, Editor.add_rect)
"""


class Test(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
    
        self.group = pg.sprite.Group()
        self.groups.append(self.group)
        # self.block = pg.sprite.Sprite()
        # self.block.image = pg.image.load('Assets/Placeholder.png')
        # self.block.rect = pg.Rect(40, 40, 40, 40)
        # self.block = Block((30, 30, 30), 20, 20)
        # self.block.add(self.group)
        self.f = 0  # frame counter for testing

        self.tree_tab = TreeTab((display_width - 360 - 5, 145, 360, 300), self, self.group)

        def f_example(s='default'):
            print('callback:', s)

        image = pg.image.load('Assets/Placeholder.png').convert()
        # button = Button((20, 20, 60, 60), "hello", f_example, self, self.group,
        #                 color=C_LIGHT, background=(100, 100, 200))
        print(self.nodes)
        button2 = Mover((20, 20, 60, 60), "move", f_example, self, self.group, 1,
                        color=C_LIGHT, background=(100, 100, 200))
        print(self.nodes)
        button3 = Mover((20, 20, 32, 32), "movie", f_example, self, self.group, 2,
                        color=C_BLUE, image=image)
        print(self.nodes)
        # self.event_handlers.append(button)
        self.event_handlers.append(button2)
        self.event_handlers.append(button3)
        image = pg.image.load('Assets/Placeholder.png').convert()
        button_n = Button((150, 50, 32, 32), "e ch", f_example, button2, self.group,
                          color=C_RED, image=image)
        self.event_handlers.append(button_n)
        image = pg.image.load('Assets/Placeholder.png').convert()
        button_n3 = Button((200, 50, 32, 32), "ie ch", f_example, button3, self.group,
                           color=C_GREEN, image=image)
        self.event_handlers.append(button_n3)

        self.tree_tab.ref = self.nodes

        # self.me = SceneNode()
        # Node(pg.Rect(20, 0, 32, 32), pg.image.load('Assets/Placeholder.png').convert(), self.me)
        # self.me.add(self.group)
        # self.me.children[0].add(self.group)

        """for i in range(10):
            x = Node(pg.Rect(40, 40, 32, 32), pg.image.load('Assets/Placeholder.png').convert())

            self.me.children[0].add_child(x)
            tmp = self.me.children[0].children[i]
            tmp.add(self.group)
            tmp.local_rect.x += randint(-199, 199)
            tmp.local_rect.y += randint(-199, 199)"""

    def update(self):
        super().update()

    def draw(self):
        self.screen.fill(C_DARK)
        super().draw()

        #if self.display_size_y() > 400:
        #    message = f'{self.clock.get_rawtime()}ms processing time / tick'
        #    text.draw(self.screen, message, (40, self.display_size_y() - 50),
        #              color=C_DARK_ISH, justify=(False, True))
        #rects.append(pg.Rect(40, self.display_size_y() - 60, 200, 30))

        legacy_text.draw(self.screen, "test", (display_width / 2, display_height / 2),
                         color=(255, 0, 0))

    def handle_events(self, pygame_events):
        for event in pygame_events:
            if event.type in MOUSE_EVENTS:
                for button in self.event_handlers:
                    button.mouse_event(event)

                if event.type == pg.MOUSEMOTION:
                    self.mouse_x, self.mouse_y = event.pos
                elif event.type == pg.MOUSEBUTTONDOWN:
                    self.drag_from_x, self.drag_from_y = event.pos
                    self.drag_event = False
                elif event.type == pg.MOUSEBUTTONUP:
                    self.drag_event = True


class Detail(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)

    def draw(self):
        self.screen.fill(C_LIGHT)

        message = f'{self.clock.get_rawtime()}ms processing time / tick'
        legacy_text.draw(self.screen, message, (40, 20),
                         color=C_DARK_ISH, justify=(False, False))


class Mover(Button):
    def __init__(self, transform, message, callback, parent, group,
                 velocity, enabled=True, visible=True, **kwargs):
        super().__init__(transform, message, callback, parent, group, enabled, visible, **kwargs)
        self.velocity = velocity
        self.score = 0

    def update(self):
        super().update()
        self.transform.x = (self.transform.x + self.velocity) % display_width
        self.dirty = 1

    def on_click(self):
        self.callback(self.message)
        self.score += 1
        self.message = str(self.score)
