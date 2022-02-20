import pygame
import engine.text as text
import engine.interface as interface
from engine.base_scene import Scene
from engine.base_node import NodeProperties
from engine.spritesheet import TileSpriteSheet
from constants import *

from tree_tab import TreeTab
from other_tab import SceneTab
from inspector_tab import InspectorTab

TAB_PADDING = 8

class Editor(Scene):
    """The editor that enables the user to edit a scene."""
    def __init__(self, screen, clock, user_scene_class):
        super().__init__(screen, clock)
        self.create_draw_group((20, 20, 24))

        # TODO: read module to check validity, get initial scene name/size
        # TODO: move imports and reloads for module user_project.scenes here
        user_scene_width = 450
        user_scene_height = 450
        scene_tab_x = self.screen_size_x - user_scene_width - TAB_PADDING

        self.selected_node = None
        self.play = False

        self.user_scene_rect = pygame.Rect(scene_tab_x, 52, user_scene_width, user_scene_height)
        self.user_surface = pygame.Surface(self.user_scene_rect.size, 0, screen)

        tab_style = interface.Style(background_editor=(20, 20, 24), background=(48, 48, 50),
                                    background_indent=interface.brighten_color((48, 48, 50), 5),
                                    tabsize=20, color=C_LIGHT, color_scroll=(74, 76, 82))

        self.icon_sheet = TileSpriteSheet('Assets/node_sprite_icons.png')

        self.user_scene_class = user_scene_class
        self.user_scene = user_scene_class(self.user_surface, clock)
        self.tree_tab = TreeTab(NodeProperties(self, TAB_PADDING, 32, scene_tab_x - TAB_PADDING*2, self.screen_size_y // 2),
            self.draw_group, self.user_scene, self.icon_sheet, style=tab_style)
        self.inspector_tab = InspectorTab(NodeProperties(self, TAB_PADDING, 32 + TAB_PADDING + self.screen_size_y // 2, scene_tab_x - TAB_PADDING*2, self.screen_size_y // 2 - 32 - TAB_PADDING * 2),
            self.draw_group, style=tab_style)
        self.scene_tab = SceneTab(NodeProperties(self, scene_tab_x, 32, self.user_scene_rect.width, tab_style.get('tabsize')),
            self.draw_group, self.user_scene, style=tab_style)

        inspector_scrollbar = interface.Scrollbar(NodeProperties(self.inspector_tab, width=5), self.draw_group)
        self.toggle_play = interface.Toggle(NodeProperties(self, 280, 4, 40, 20), self.draw_group, 'Play', self.action_play,
                                            checked=self.play, background_checked=C_RED, background=tab_style.get('background_editor'))
        button_reload = interface.Button(NodeProperties(self, 330, 4, 40, 20), self.draw_group, 'Reload', self.action_reload,
                                         background=tab_style.get('background_editor'))

        self.recent_frames_ms = []

    def resize(self):
        self.resize_draw_group()
        self.user_scene.resize_draw_group()
        scene_tab_x = self.screen_size_x - self.user_scene_rect.width - TAB_PADDING
        self.user_scene_rect.left = scene_tab_x
        if scene_tab_x - TAB_PADDING*2 < 16:
            self.tree_tab.enabled = False
            self.inspector_tab.enabled = False
        else:
            self.tree_tab.enabled = True
            self.tree_tab.transform.width = scene_tab_x - TAB_PADDING*2
            self.inspector_tab.enabled = True
            self.inspector_tab.transform.width = scene_tab_x - TAB_PADDING*2
        self.scene_tab.transform.x = scene_tab_x
        self.scene_tab.transform.width = self.user_scene_rect.width

    def update(self):
        super().update()
        if self.play:
            self.user_scene.update()

    def draw(self):
        rects = super().draw()
        user_rects = self.user_scene.draw()
        user_scene_top_left = self.user_scene_rect.topleft
        # Shift all user scene draw rectangles to align with blit destination
        _local_rects_extend = rects.extend
        if user_rects:
            for rect in user_rects:
                rect.move_ip(user_scene_top_left)
            _local_rects_extend(user_rects)

        self.screen.blit(self.user_surface, user_scene_top_left)

        # TODO: move this frame counter to an appropriate tab
        rawtime = self.clock.get_rawtime()
        self.recent_frames_ms.append(rawtime)
        if len(self.recent_frames_ms) > 30:
            self.recent_frames_ms.pop(0)
            message = f'{sum(self.recent_frames_ms) * FPS // 30}ms / s ({rawtime}ms / frame)'
        else:
            message = f'{rawtime}ms processing / frame'

        text.draw(self.screen, message, (30, 5), color=C_LIGHT_ISH)
        self.draw_group.repaint_rect((30, 5, 180, 20))

        return rects

    def handle_events(self, pygame_events):
        super().handle_events(pygame_events)

        for event in pygame_events:
            if event.type == pygame.VIDEORESIZE:
                self.resize()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    self.selected_node.transform.x += 1
                if event.key == pygame.K_LEFT:
                    self.selected_node.transform.x -= 1
                if event.key == pygame.K_DOWN:
                    self.selected_node.transform.y += 1
                if event.key == pygame.K_UP:
                    self.selected_node.transform.y -= 1
                if event.key == pygame.K_DELETE:
                    self.selected_node.remove()

        if not self.play:
            return
        # Not an ideal approach; the scene should believe it's at (0, 0), but
        # this means its event checks will be offset. To compensate, the mouse
        # events must shift. Some events will currently have out of bounds
        # coordinates, but events cannot be removed from the data structure.
        rect = self.user_scene_rect
        for event in pygame_events:
            if event.type in interface.MOUSE_EVENTS:
                event.pos = (event.pos[0] - rect.x, event.pos[1] - rect.y)

        self.user_scene.handle_events(pygame_events)

    def set_selected_node(self, node):
        self.selected_node = node
        self.inspector_tab.dirty = 1

    def action_play(self, checked):
       self.play = checked

    def action_reload(self):
        if self.play:
            self.toggle_play.checked = True
            self.toggle_play.dirty = 1
            self.action_play(True)  # stop playing

        self.user_scene = self.user_scene_class(self.user_surface, self.clock)
        self.tree_tab.clear(self.user_scene)
        print('reload!')

class Select(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.next_scene = ''

    def select_scene(self):
        self.change_scene(Editor, self.next_scene)

    def update(self):
        super().update()
