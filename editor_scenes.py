import pygame
from importlib import reload as importlib_reload
import engine.text as text
import engine.interface as interface
from engine.base_scene import Scene
from engine.base_node import NodeProperties
from engine.spritesheet import TileSpriteSheet
from engine.template import read_local_json, register_node, nodes_to_template, resolve_class
from constants import *

from other_tab import SceneTab, ProjectFileTab
from tree_tab import TreeTab
from inspector_tab import InspectorTab

TAB_PADDING = 8

class Editor(Scene):
    """The editor that enables the user to edit a scene."""
    def __init__(self, screen, clock, user_module, user_path):
        super().__init__(screen, clock)
        self.create_draw_group((20, 20, 24))

        self.user_module = user_module
        self.user_path = user_path
        self.user_scene, self.user_scene_rect, self.user_surface = self.create_user_scene()

        self.selected_node = None
        self.play = False

        scene_tab_x = self.screen_size_x - self.user_scene_rect.width - TAB_PADDING
        tab_style = interface.Style(background_editor=(20, 20, 24),
            background=(48, 48, 50), background_indent=(60, 60, 60),
            tabsize=20, color=C_LIGHT, color_scroll=(100, 100, 100))
        ui_style = interface.Style.from_kwargs(
            dict(style=tab_style, background=(30, 36, 36)))
        font_small = pygame.font.SysFont('Calibri', 15)

        self.icon_sheet = TileSpriteSheet('Assets/EditorIcons.png')

        self.tree_tab = TreeTab(NodeProperties(
            self, TAB_PADDING, 48, scene_tab_x - TAB_PADDING*2, self.screen_size_y // 2 - TAB_PADDING),
            self.draw_group, self.user_scene, self.icon_sheet, ui_style, style=tab_style)
        self.inspector_tab = InspectorTab(NodeProperties(
            self, TAB_PADDING, 68 + self.screen_size_y // 2, scene_tab_x - TAB_PADDING*2,
            self.screen_size_y // 2 - 60 - TAB_PADDING * 2),
            self.draw_group, ui_style, style=tab_style)
        self.scene_tab = SceneTab(NodeProperties(
            self, scene_tab_x, 52, self.user_scene_rect.width, 0),
            self.draw_group, self.user_scene.draw_group, self.user_scene, style=tab_style)
        self.project_file_tab = ProjectFileTab(NodeProperties(
            self, scene_tab_x, 72 + self.user_scene_rect.height + TAB_PADDING, self.user_scene_rect.width,
            self.screen_size_y - self.user_scene_rect.height - TAB_PADDING*2 - 72),
            self.draw_group, style=tab_style)

        self.toggle_play = interface.Toggle(NodeProperties(self, 280, 4, 40, 20),
            self.draw_group, 'Play', self.action_play, checked=self.play,
            background_checked=C_RED, background=tab_style.get('background_editor'))
        button_reload = interface.Button(NodeProperties(self, 330, 4, 60, 20),
            self.draw_group, 'Reload', self.action_reload,
            background=tab_style.get('background_editor'), color=tab_style.get('color'))
        self.button_clear = interface.Button(NodeProperties(
            self, 80, self.inspector_tab.transform.y - 20, 33, 18, enabled=False),
            self.draw_group, '<\u2014', self.action_clear, style=tab_style, font=font_small)

        self.recent_frames_ms = []

    def resize(self):
        self.resize_draw_group()
        if hasattr(self.user_scene, 'background_surf'):
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
        if user_rects or self.scene_tab.repaint_overlay:
            for rect in user_rects:
                rect.move_ip(user_scene_top_left)
            rects.extend(user_rects)
            # Blit the user scene, then overlays, to the screen
            self.screen.blit(self.user_surface, user_scene_top_left)
            rects.append(self.scene_tab.box.rect)
            self.screen.blit(self.scene_tab.box.image, self.scene_tab.box.rect.topleft)

        # TODO: move this frame counter to an appropriate tab
        rawtime = self.clock.get_rawtime()
        self.recent_frames_ms.append(rawtime)
        if len(self.recent_frames_ms) > 30:
            self.recent_frames_ms.pop(0)
            message = f'{sum(self.recent_frames_ms) * FPS // 30}ms / s ({rawtime}ms / frame)'
        else:
            message = f'{rawtime}ms processing / frame'

        rect = text.draw(self.screen, message, (30, 5), color=C_LIGHT_ISH)
        self.draw_group.repaint_rect(rect)

        return rects

    def handle_events(self, pygame_events):
        super().handle_events(pygame_events)

        for event in pygame_events:
            if event.type == pygame.VIDEORESIZE:
                self.resize()
            elif event.type == pygame.VIDEOEXPOSE:
                # Display is cleared when minimised, so redraw all elements
                self.draw_group.repaint_rect(self.screen.get_rect())
            elif event.type == pygame.KEYDOWN:
                if self.selected_node is not None:
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

    def create_user_scene(self):
        configuration = read_local_json('config.engine')
        user_scene_width = configuration['display_width']
        user_scene_height = configuration['display_height']

        scene_tab_x = self.screen_size_x - user_scene_width - TAB_PADDING
        scene_rect = pygame.Rect(scene_tab_x, 52, user_scene_width, user_scene_height)
        surface = pygame.Surface(scene_rect.size)

        user_scene_class = getattr(self.user_module, configuration['entry_scene'])
        return user_scene_class(surface, self.clock), scene_rect, surface

    def set_selected_node(self, node):
        self.selected_node = node
        self.inspector_tab.dirty = 1
        self.button_clear.enabled = True

    def action_play(self, checked):
        self.play = checked

    def action_reload(self):
        if self.play:
            self.toggle_play.checked = False
            self.toggle_play.dirty = 1
            self.action_play(False)  # stop playing

        self.selected_node = None
        importlib_reload(self.user_module)
        self.user_scene, self.user_scene_rect, self.user_surface = self.create_user_scene()
        self.tree_tab.clear(self.user_scene)
        print('reload!')

    def action_clear(self):
        self.selected_node = None
        self.tree_tab.clear_selected_node()
        self.inspector_tab.dirty = 1
        self.button_clear.enabled = False

    def add_node(self, class_name, parent):
        inst_class = resolve_class(self.user_scene, class_name)
        if issubclass(inst_class, pygame.sprite.Sprite):
            new_node = inst_class(NodeProperties(parent, 0, 0, 40, 40), self.user_scene.draw_group)
        else:
            new_node = inst_class(NodeProperties(parent, 0, 0, 0, 0))
        register_node(nodes_to_template[parent], new_node)

class Select(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.next_scene = ''

    def select_scene(self):
        self.change_scene(Editor, self.next_scene)

    def update(self):
        super().update()
