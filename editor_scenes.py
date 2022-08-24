import pygame
import sys
from importlib import import_module, reload

import engine.text as text
import engine.interface as interface
from engine.base_scene import Scene
from engine.base_node import NodeProperties, SpriteNode
from engine.spritesheet import TileSpriteSheet
import engine.template as template
from constants import *

from other_tab import SceneTab, HelpTab
from project_file_tab import ProjectFileTab
from tree_tab import TreeTab
from inspector_tab import InspectorTab

TAB_PADDING = 8  # spacing between tabs in the editor
directions = {  # movement directions caused by pressing Shift + key
    pygame.K_RIGHT: ('x', 1), pygame.K_LEFT: ('x', -1),
    pygame.K_DOWN: ('y', 1),  pygame.K_UP: ('y', -1)
}

class Editor(Scene):
    """The editor that enables the user to edit a scene.
    Takes user_module, the module to run, and user_path, the path to the module.
    """
    def __init__(self, screen, clock, user_module, user_path):
        super().__init__(screen, clock)
        self.create_draw_group((20, 20, 24))

        self.user_module = user_module
        self.user_path = user_path
        self.user_scene, self.user_scene_rect, self.user_surface = self.create_user_scene()

        self.selected_node = None
        self.play = False
        self.help_opened = False

        # Define constant graphical settings and load graphics
        scene_tab_x = self.screen_size_x - self.user_scene_rect.width - TAB_PADDING
        tab_style = interface.Style(background_editor=(20, 20, 24),
            background=(48, 48, 50), background_indent=(60, 60, 60),
            tabsize=20, color=C_LIGHT, color_scroll=(100, 100, 100))
        ui_style = interface.Style.from_kwargs(
            dict(style=tab_style, background=(30, 36, 36)))
        menu_bar_style = interface.Style.from_kwargs(
            dict(style=tab_style, background=tab_style.get('background_editor'), imagex=5))
        self.font_reading = pygame.font.SysFont('Calibri', 15)
        self.icon_sheet = TileSpriteSheet('Assets/EditorIcons.png')

        # Initialise the tabs
        self.tree_tab = TreeTab(NodeProperties(
            self, TAB_PADDING, 48, scene_tab_x - TAB_PADDING*2, self.screen_size_y // 2 - TAB_PADDING),
            self.draw_group, self.user_scene, self.icon_sheet, ui_style, style=tab_style)
        self.inspector_tab = InspectorTab(NodeProperties(
            self, TAB_PADDING, 68 + self.screen_size_y // 2, scene_tab_x - TAB_PADDING*2,
            self.screen_size_y // 2 - 60 - TAB_PADDING * 2),
            self.draw_group, ui_style, style=tab_style)
        self.scene_tab = SceneTab(NodeProperties(
            self, scene_tab_x, 48, self.user_scene_rect.width, 0),
            self.draw_group, self.user_scene.draw_group, self.user_scene, style=tab_style)
        self.project_file_tab = ProjectFileTab(NodeProperties(
            self, scene_tab_x, 72 + self.user_scene_rect.height + TAB_PADDING, self.user_scene_rect.width,
            self.screen_size_y - self.user_scene_rect.height - TAB_PADDING*2 - 72),
            self.draw_group, ui_style, self.font_reading, style=tab_style)
        self.help_tab = HelpTab(NodeProperties(
            self, scene_tab_x, 48, self.user_scene_rect.width, 300, enabled=False),
            self.draw_group, self.font_reading, style=tab_style)

        self.toggle_play = interface.Toggle(NodeProperties(self, 280, 4, 40, 20),
            self.draw_group, 'Play', self.action_play, checked=self.play,
            background_checked=C_RED, background=tab_style.get('background_editor'))
        button_reload = interface.Button(NodeProperties(self, 330, 4, 60, 20),
            self.draw_group, 'Reload', self.action_reload,
            background=tab_style.get('background_editor'), color=tab_style.get('color'))
        button_save = interface.Button(NodeProperties(self, 440, 4, 40, 20),
            self.draw_group, 'Save', self.save_scene_changes,
            background=tab_style.get('background_editor'), color=tab_style.get('color'))
        self.button_show_help = interface.Button(NodeProperties(
            self, self.screen_size_x - 5, 4, 60, 20, anchor_x=1), self.draw_group,
            'Help', lambda: self.action_show_help('Introduction'),
            background=tab_style.get('background_editor'), color=tab_style.get('color'))

        self.recent_frames_ms = []  # used by frame speed counter

    def resize(self):
        user_scene_width = self.user_scene_rect.width
        scene_tab_x = self.screen_size_x - user_scene_width - TAB_PADDING
        self.user_scene_rect.x = scene_tab_x

        # Update sizes
        if scene_tab_x - TAB_PADDING*2 < 16:
            self.tree_tab.enabled = self.inspector_tab.enabled = False
        else:
            self.tree_tab.enabled = self.inspector_tab.enabled = True
            self.tree_tab.transform.size = (
                scene_tab_x - TAB_PADDING*2, self.screen_size_y // 2 - TAB_PADDING)
            self.inspector_tab.transform.size = (
                scene_tab_x - TAB_PADDING*2, self.screen_size_y // 2 - 60 - TAB_PADDING * 2)
            self.project_file_tab.transform.size = (
                user_scene_width, self.screen_size_y - self.user_scene_rect.height - TAB_PADDING * 2 - 72)
        # Update positions
        self.inspector_tab.transform.y = 68 + self.screen_size_y // 2
        for right_tab in self.scene_tab, self.project_file_tab, self.help_tab:
            right_tab.transform.x = scene_tab_x
        self.button_show_help.transform.x = self.screen_size_x - 5
        self.scene_tab.transform.width = self.user_scene_rect.width

    def update(self):
        super().update()
        if self.play:
            self.user_scene.update()

    def draw(self):
        rects = super().draw()

        user_rects = self.user_scene.draw()
        if not self.help_opened:
            user_scene_top_left = self.user_scene_rect.topleft
            # Shift all user scene draw rectangles to align with blit destination
            if user_rects:
                for rect in user_rects:
                    rect.move_ip(user_scene_top_left)
                rects.extend(user_rects)
            # Blit the user scene, then overlays, to the screen
            self.screen.blit(self.user_surface, user_scene_top_left)
            rects.append(self.scene_tab.box.rect)
            if self.scene_tab.box.enabled:
                self.screen.blit(self.scene_tab.box.image, self.scene_tab.box.rect.topleft)

        # TODO: consider moving this frame counter to an appropriate tab
        rawtime = self.clock.get_rawtime()
        self.recent_frames_ms.append(rawtime)
        if len(self.recent_frames_ms) > 12:
            self.recent_frames_ms.pop(0)
            message = f'{sum(self.recent_frames_ms) * FPS // 12}ms / s ({rawtime}ms / frame)'
        else:
            message = f'{rawtime}ms processing / frame'

        rect = text.draw(self.screen, message, (54, 5), color=C_LIGHT_ISH, font=self.font_reading)
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
                if getattr(self.user_scene, 'draw_group', None) is not None:
                    self.user_scene.draw_group.repaint_rect(self.user_scene.screen.get_rect())
            elif event.type == pygame.KEYDOWN:
                if self.selected_node is not None:
                    if event.mod & pygame.KMOD_SHIFT:
                        self.translate_selected_node(event)
                    if event.key == pygame.K_DELETE:
                        self.remove_selected_node()

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
        configuration = template.read_local_json('project_config')
        user_scene_width = configuration['display_width']
        user_scene_height = configuration['display_height']

        scene_tab_x = self.screen_size_x - user_scene_width - TAB_PADDING
        scene_rect = pygame.Rect(scene_tab_x, 48, user_scene_width, user_scene_height)
        surface = pygame.Surface(scene_rect.size)

        user_scene_class = getattr(self.user_module, configuration['entry_scene'])
        return user_scene_class(surface, self.clock), scene_rect, surface

    def set_selected_node(self, node):
        self.selected_node = node
        self.inspector_tab.dirty = 1

    def remove_selected_node(self):
        if not self.play and getattr(self.user_scene, 'template', False):
            template.nodes_to_template[self.selected_node.parent]['nodes'].remove(template.nodes_to_template[self.selected_node])
            del template.nodes_to_template[self.selected_node]
        self.selected_node.remove()
        self.selected_node = None

    def clear_selected_node(self):
        self.selected_node = None
        self.inspector_tab.dirty = 1

    def translate_selected_node(self, event):
        if event.key in directions and hasattr(self.selected_node, 'transform'):
            axis, delta = directions[event.key]
            new_location = getattr(self.selected_node.transform, axis) + delta
            setattr(self.selected_node.transform, axis, new_location)

    def action_play(self, checked):
        self.save_scene_changes()
        self.action_reload()
        self.play = checked
        self.tree_tab.dirty = 1

    def action_reload(self):
        if self.play:
            self.toggle_play.checked = False
            self.toggle_play.dirty = 1
            self.play = False

        self.selected_node = None
        reload(self.user_module)
        self.user_scene, self.user_scene_rect, self.user_surface = self.create_user_scene()
        self.tree_tab.grid.set_tree(self.user_scene)
        print('Engine reload successful')

    def add_node(self, class_name, parent):
        inst_class = template.resolve_class(self.user_scene, class_name)
        if issubclass(inst_class, SpriteNode):
            new_node = inst_class(NodeProperties(parent, 0, 0, 40, 40), self.user_scene.draw_group)
        else:
            new_node = inst_class(NodeProperties(parent, 0, 0, 0, 0))
        if not self.play and getattr(self.user_scene, 'template', False):
            template.register_node(self.user_scene, template.nodes_to_template[parent], new_node)

    def save_scene_changes(self):
        if getattr(self.user_scene, 'template', False):
            scenes_name = template.read_local_json('project_config')['scenes_file']
            project_templates = template.read_local_json(scenes_name)
            project_templates[type(self.user_scene).__name__] = self.user_scene.template
            print('Saving template data:\n' + str(project_templates)[:32] + '...')
            template.write_local_json(scenes_name, project_templates)

    def add_scene_module(self, module_name: str):
        if getattr(self.user_scene, 'template', False):
            modules = self.user_scene.template.get('modules', [])
            modules.append(module_name)
            self.user_scene.template.modules = modules
            self.action_reload()

    def action_show_help(self, page='Introduction'):
        self.help_opened = self.help_tab.enabled = True
        self.scene_tab.enabled = False
        self.help_tab.open_page(page)

    def action_hide_help(self):
        self.help_opened = self.help_tab.enabled = False
        self.scene_tab.enabled = True

class Select(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.create_draw_group((32, 32, 34))
        self.project_path = ''

        interface.Button(NodeProperties(self, 20, 20, 160, 25), self.draw_group, 'Select',
                         self.select_project_path, color=(255, 255, 255))
        interface.Button(NodeProperties(self, 20, 60, 160, 25), self.draw_group, 'Load',
                         self.to_editor, color=(255, 255, 255))

    def select_project_path(self):
        # Create an "Open" dialog box and set next_scene to the path
        from tkinter.filedialog import askdirectory
        from tkinter import Tk
        Tk().withdraw()  # do not show a root window

        try:
            self.project_path = askdirectory()
            # Allow pygame to process internal events to avoid "not responding".
            pygame.event.pump()

            # Open the configuration file to check it is readable.
            with open(self.project_path + '/project_config.json', 'r', encoding='utf-8') as f:
                file_preview = f.read(32)
            print('Read project config:\n' + file_preview.replace('\n', '¬') + '...')
        except OSError as _error:
            print(f'Critical error opening file:\n    {_error}')
            self.project_path = ''

    def to_editor(self):
        user_scenes = self.set_project(self.project_path)
        self.change_scene(Editor, user_scenes, self.project_path)

    def update(self):
        super().update()

    @staticmethod
    def set_project(project_path: str):
        print(project_path)
        sys.path.insert(1, project_path)
        scenes_name = template.read_local_json('project_config')['scenes_file']
        return import_module(scenes_name)
