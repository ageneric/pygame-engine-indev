import pygame
import sys
from importlib import import_module, reload
from traceback import print_tb
from tkinter.filedialog import askdirectory
from tkinter import Tk
Tk().withdraw()  # do not show a root window

import engine.text as text
import engine.interface as interface
from engine.base_scene import Scene
from engine.base_node import NodeProps, SpriteNode
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
        self.user_scene, self.user_scene_rect, self.user_surface, _error = self.create_user_scene()
        if _error is not None:
            self.show_error(_error, 'load')

        self.selected_node = None
        self.play = False
        self.help_opened = False

        # Define constant graphical settings and load graphics
        scene_tab_x = self.screen_size_x - self.user_scene_rect.width - TAB_PADDING
        tab_style = interface.Style(background_editor=(20, 20, 24),
            background=(48, 48, 50), background_indent=(60, 60, 60),
            tabsize=20, color=C_LIGHT, color_scroll=(104, 104, 104))
        ui_style = interface.Style.from_kwargs(
            dict(style=tab_style, background=(30, 36, 36)))
        menu_bar_style = interface.Style.from_kwargs(
            dict(style=tab_style, background=tab_style.get('background_editor'), imagex=5))
        self.font_reading = pygame.font.SysFont('Calibri', 15)
        self.icon_sheet = TileSpriteSheet('Assets/EditorIcons.png')

        # Initialise the tabs
        self.tree_tab = TreeTab(NodeProps(
            self, TAB_PADDING, 48, scene_tab_x - TAB_PADDING*2, self.screen_size_y // 2 - TAB_PADDING),
            self.draw_group, self.user_scene, self.icon_sheet, ui_style, style=tab_style)
        self.inspector_tab = InspectorTab(NodeProps(
            self, TAB_PADDING, 68 + self.screen_size_y // 2, scene_tab_x - TAB_PADDING*2,
            self.screen_size_y // 2 - 60 - TAB_PADDING * 2),
            self.draw_group, ui_style, style=tab_style)
        self.scene_tab = SceneTab(NodeProps(
            self, scene_tab_x, 48, self.user_scene_rect.width, 0),
            self.draw_group, self.user_scene.draw_group, self.user_scene, style=tab_style)
        self.project_file_tab = ProjectFileTab(NodeProps(
            self, scene_tab_x, 72 + self.user_scene_rect.height + TAB_PADDING, self.user_scene_rect.width,
            self.screen_size_y - self.user_scene_rect.height - TAB_PADDING*2 - 72),
            self.draw_group, self.icon_sheet, ui_style, self.font_reading, style=tab_style)
        self.help_tab = HelpTab(NodeProps(
            self, scene_tab_x, 48, self.user_scene_rect.width, self.user_scene_rect.height, enabled=False),
            self.draw_group, self.font_reading, style=tab_style)

        # Initialise the menu bar
        self.toggle_play = interface.Toggle(NodeProps(self, scene_tab_x, 2, 60, 22),
                                            self.draw_group, 'Play', self.action_play, checked=self.play, style=menu_bar_style,
                                            background_checked=(48, 32, 108), image=self.icon_sheet.load_image(pygame.Rect(3, 1, 1, 1), 8))
        self.button_reload = interface.Button(
            NodeProps(self, scene_tab_x - TAB_PADDING, 2, 68, 22, anchor_x=1),
            self.draw_group, '   Reload', self.action_reload, style=menu_bar_style,
            image=self.icon_sheet.load_image(pygame.Rect(0, 2, 1, 1), 8))
        button_save = interface.Button(NodeProps(self, TAB_PADDING, 2, 48, 22),
                                       self.draw_group, 'Save', self.save_scene_changes, style=menu_bar_style)
        self.button_show_help = interface.Button(NodeProps(
            self, self.screen_size_x - TAB_PADDING, 2, 60, 22, anchor_x=1), self.draw_group,
            'Help', lambda: self.action_show_help('Introduction'), style=menu_bar_style,
            image=self.icon_sheet.load_image(pygame.Rect(3, 0, 1, 1), 8))

        self._recent_frames_ms = []  # used by frame speed counter
        self._recent_message = ''  # display error messages

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
        self.toggle_play.transform.x = scene_tab_x
        self.button_reload.transform.x = scene_tab_x - TAB_PADDING

    def update(self):
        super().update()
        if self.play:
            try:
                self.user_scene.update()
            except Exception as _error:
                self.show_error(_error, 'update', '()')
                self.action_play(False, suppress_message=True)

    def draw(self):
        rects = super().draw()

        try:
            user_rects = self.user_scene.draw()
        except Exception as _error:
            self._recent_message = 'draw !!! ' + str(_error)
            user_rects = []
        
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
            if self.scene_tab.debug_show_dirty:
                for rect in user_rects:
                    pygame.draw.rect(self.screen, (min(255, rect.width + rect.height + 160), 60, 160), rect, 1)
                    self.draw_group.repaint_rect(rect)

        # TODO: consider moving this frame counter to an appropriate tab
        rawtime = self.clock.get_rawtime()
        self._recent_frames_ms.append(rawtime)
        if len(self._recent_frames_ms) > 12:
            self._recent_frames_ms.pop(0)
            message = f'{sum(self._recent_frames_ms) * FPS // 12}ms / s ({rawtime}ms / frame)'
        else:
            message = f'{rawtime}ms processing / frame'

        rect = text.draw(self.screen, message, (62, 5), color=C_LIGHT_ISH, font=self.font_reading)
        self.draw_group.repaint_rect(rect)
        rect = text.draw(self.screen, self._recent_message, (self.toggle_play.transform.x + 68, 5),
                         color=C_LIGHT_ISH, font=self.font_reading)
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
                elif event.key == pygame.K_o and event.mod & pygame.KMOD_CTRL:
                    self.scene_tab.debug_show_dirty = not self.scene_tab.debug_show_dirty

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
        
        try:
            self.user_scene.handle_events(pygame_events)
        except Exception as _error:
            self.show_error(_error, 'event', '() or Scene.handle_events()')
            self.action_play(False, suppress_message=True)

    def create_user_scene(self):
        """Returns scene instance, scene rect, scene surface, error."""
        configuration = template.read_local_json('project_config')
        user_scene_width = configuration['display_width']
        user_scene_height = configuration['display_height']

        scene_tab_x = self.screen_size_x - user_scene_width - TAB_PADDING
        scene_rect = pygame.Rect(scene_tab_x, 48, user_scene_width, user_scene_height)
        surface = pygame.Surface(scene_rect.size)

        user_scene_class = getattr(self.user_module, configuration['entry_scene'])
        try:
            return user_scene_class(surface, self.clock), scene_rect, surface, None
        except Exception as _error:
            return Scene(surface, self.clock), scene_rect, surface, _error

    def set_selected_node(self, node):
        self.selected_node = node
        self.inspector_tab.set_selected(self.selected_node, self.user_scene)

    def clear_selected_node(self):
        self.selected_node = None
        self.inspector_tab.set_selected(self.selected_node, self.user_scene)

    def remove_selected_node(self):
        if not self.play and getattr(self.user_scene, 'template', False) and self.selected_node in template.node_to_template:
            del template.node_to_template[self.selected_node]
        self.selected_node.remove()
        self.clear_selected_node()

    def translate_selected_node(self, event):
        if event.key in directions and hasattr(self.selected_node, 'transform'):
            axis, delta = directions[event.key]
            new_location = getattr(self.selected_node.transform, axis) + delta
            setattr(self.selected_node.transform, axis, new_location)
            if not self.play and getattr(self.user_scene, 'template', False):
                template.update_node(self.selected_node, axis)

    def action_play(self, checked: bool, suppress_message=False):
        if checked:
            self.save_scene_changes()
        else:
            self.action_reload(suppress_message)
        self.play = checked
        self.tree_tab.dirty = 1

    def action_reload(self, suppress_message=False):
        if self.play:
            self.toggle_play.checked = False
            self.toggle_play.dirty = 1
            self.play = False

        self.selected_node = None
        reload(self.user_module)
        self.user_scene, self.user_scene_rect, self.user_surface, _error = self.create_user_scene()
        if _error is None:
            self.tree_tab.grid.set_tree(self.user_scene)
            self.inspector_tab.set_selected(self.selected_node, self.user_scene)
            if not suppress_message:
                self._recent_message = 'Reloaded scene'
                print(self._recent_message)
        else:
            self.show_error(_error, 'reload')

    def show_error(self, error, context='', after_context=''):
        self._recent_message = f'{context} !!! {error} (see console)'
        print(f'Hit {str(type(error).__name__)} ({error}) in {context}{after_context}:')
        print_tb(error.__traceback__)

    def add_node(self, class_name, parent):
        inst_class = template.resolve_class(self.user_scene, class_name)
        if issubclass(inst_class, SpriteNode):
            new_node = inst_class(NodeProps(parent, 0, 0, 40, 40), self.user_scene.draw_group)
        else:
            new_node = inst_class(NodeProps(parent, 0, 0, 0, 0))
        if not self.play and getattr(self.user_scene, 'template', False) and parent in template.node_to_template:
            template.register_node(self.user_scene, template.node_to_template[parent], new_node)

    def save_scene_changes(self):
        if getattr(self.user_scene, 'template', False):
            scenes_name = template.read_local_json('project_config')['scenes_file']
            project_templates = template.read_local_json(scenes_name)
            self.user_scene.template['nodes'] = []
            template.get_tree_template(self.user_scene, self.user_scene.template['nodes'])
            project_templates[type(self.user_scene).__name__] = self.user_scene.template
            template.write_local_json(scenes_name, project_templates)
            self._recent_message = 'Template data saved: ' + str(project_templates)[:32] + '...'
            print(self._recent_message)

    def add_scene_module(self, module_name: str):
        if getattr(self.user_scene, 'template', False):
            modules = self.user_scene.template.get('modules', [])
            if module_name not in modules:  # check not overwriting old module
                modules.append(module_name)
                self.user_scene.template['modules'] = modules
                self.tree_tab.set_pick_class_options(modules)
            self.save_scene_changes()  # save the updated modules list
            self.action_reload()  # reload scene to import the new module

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
        self.project_path = None

        interface.Button(NodeProps(self, 20, 60, 160, 100), self.draw_group, 'Open Existing Project',
                         self.select_project_path, color=C_LIGHT)
        interface.Button(NodeProps(self, 200, 60, 160, 100), self.draw_group, 'Open Demo Project',
                         self.demo_project, color=C_LIGHT, background=(18, 26, 20))
        self.font = pygame.font.SysFont('Calibri', 24, bold=True)

    def draw(self):
        rects = super().draw()

        text.draw(self.screen, 'Welcome to', (20, 10), color=C_LIGHT_ISH)
        text.draw(self.screen, 'Pygame Engine', (20, 24), color=C_LIGHT_ISH,
                  font=self.font, static=True)
        text.draw(self.screen, 'for Python 3.7+', (176, 30), color=C_LIGHT_ISH)
        text.draw(self.screen, f'Running Pygame {pygame.version.ver}.', (20, 190),
                  color=C_DARK_ISH, static=True)

        if pygame.version.vernum[0] < 2:
            text.draw(self.screen, 'This program has limited support for Pygame version 1.',
                      (20, 210), color=(224, 120, 120))
        if self.project_path == '':
            text.draw(self.screen, f'Action failed. Please check the console.',
                      (20, 230), color=(224, 120, 120))
        return rects

    def handle_events(self, pygame_events):
        super().handle_events(pygame_events)

        for event in pygame_events:
            if event.type == pygame.VIDEOEXPOSE:
                self.resize_draw_group()

    def select_project_path(self):
        # Allow pygame to process internal events to avoid "not responding".
        pygame.event.pump()
        # Create an "Open" dialog box and set project_path to the path
        self.project_path = askdirectory()
        try:
            # Open the configuration file to check it is readable.
            with open(self.project_path + '/project_config.json', 'r', encoding='utf-8') as f:
                file_preview = f.read(32)
            print('Read project config:\n' + file_preview.replace('\n', '¬') + '...')
            self.to_editor()
        except OSError as _error:
            print(f'Critical error opening file:\n    {_error}')
            self.project_path = ''
            print('Please open a directory containing a project_config.json file.')

    def demo_project(self):
        self.project_path = sys.path[0] + '/demo_project'
        self.to_editor()

    def to_editor(self):
        user_scenes = self.set_project(self.project_path)
        self.change_scene(Editor, user_scenes, self.project_path)

    @staticmethod
    def set_project(project_path: str):
        print(project_path)
        sys.path.insert(1, project_path)
        scenes_name = template.read_local_json('project_config')['scenes_file']
        return import_module(scenes_name)
