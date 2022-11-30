import subprocess
import sys
from os import name as os_name, getenv
from pathlib import Path

import engine.text as text
import engine.template as template
from engine.base_node import SpriteNode, NodeProps, Anchor, Node
from engine.interface import Style, Button, State, TextEntry
from engine.spritesheet import tint_surface

from other_tab import TabHeading
import project_format

class ProjectFileTab(SpriteNode):
    _layer = 0

    def __init__(self, node_props, group, icon_sheet, ui_style, font_reading, **kwargs):
        super().__init__(node_props, group)
        self.style = Style.from_kwargs(kwargs)
        self.font_reading = font_reading
        self.icons = [icon_sheet.load_image((i, 0, 1, 1), 8) for i in (0, 1)]

        TabHeading(NodeProps(self, 0, 0, self.transform.width, anchor_y=Anchor.bottom),
                   group, 'Project Files', style=self.style)
        self.class_menu = Node(NodeProps(self, 0, 75, enabled=False))

        button_explorer = Button(NodeProps(self, 5, 5, 120, 20), group,
                                 'Show in Explorer', self.open_nt_explorer, style=ui_style)
        if os_name != 'nt':
            button_explorer.state = State.locked
        Button(NodeProps(self, 5, 30, 120, 20), group,
               'Define Class', self.show_class_menu, style=ui_style)
        Button(NodeProps(self, 140, 5, 100, 20), group,
               'Edit Scenes', self.open_scenes, style=ui_style)

        subclass_node = Button(NodeProps(self.class_menu, 5, 0, 80, 20), group,
               'Node', self.new_node_subclass, style=ui_style, background_hovered=(120, 60, 80))
        subclass_sprite_node = Button(NodeProps(self.class_menu, 90, 0, 100, 20), group,
               'SpriteNode', self.new_sprite_node_subclass, style=ui_style, background_hovered=(60, 120, 80))
        self.buttons_subclass = [subclass_node, subclass_sprite_node]
        self.class_name = 'MyClass'
        TextEntry(NodeProps(self.class_menu, 5, 25, 130, 18), group, self.class_name,
                  cursor='|.py', edit_callback=self.edit_class_name, style=ui_style,
                  background=ui_style.get('background_indent'))

    def draw(self):
        super().draw()
        if self._visible and self.dirty > 0:
            self.image.fill(self.style.get('background'))

            if self.class_menu.enabled:
                text.draw(self.image, 'Please select a base class and a Python class name.',
                          (5, 55), self.style.get('color'), self.font_reading)
            elif hasattr(self.parent.user_scene, 'user_classes'):
                # Draw a list of the user classes with icons to left
                user_classes = self.parent.user_scene.user_classes.items()
                for i, (name, module) in enumerate(user_classes):
                    self.image.blit(self.icons[issubclass(module, SpriteNode)], (5, i*14 + 59))
                    text.draw(self.image, f'{name}.py', (19, i*14 + 55))

    def open_nt_explorer(self):
        try:
            path = Path(sys.path[1])
            if path.is_dir():
                explorer_path = Path(getenv('WINDIR')) / 'explorer.exe'
                # Convert directory path to backslashes starting with C:\
                formatted_path = '\\'.join(path.parts).replace('\\\\', '\\', 1)
                subprocess.run([explorer_path, formatted_path])
        except OSError:
            print('Editor warning: could not open project file directory')

    def show_class_menu(self):
        self.class_menu.enabled = not self.class_menu.enabled
        self.dirty = 1

    def edit_class_name(self, class_name):
        self.class_name = class_name
        # Lock buttons if the class name is not valid
        new_state = State.idle if self.class_name.isidentifier() else State.locked
        for button in self.buttons_subclass:
            button.state = new_state
            button.dirty = 1

    def new_sprite_node_subclass(self):
        self.new_node_subclass(True)

    def new_node_subclass(self, is_sprite_node=False):
        if self.class_name is None or not self.class_name.isidentifier():
            return

        parent_class = 'SpriteNode' if is_sprite_node else 'Node'
        group_argument = ', groups' if is_sprite_node else ''
        content = project_format.node_subclass_code
        content = content.format(self.class_name, parent_class, group_argument)

        path = write_local_text(self.class_name + '.py', content)
        open_in_editor(path)
        self.parent.add_scene_module(self.class_name)

    def open_scenes(self):
        scenes_name = template.read_local_json('project_config')['scenes_file']
        open_in_editor((Path(sys.path[1]) / scenes_name).with_suffix('.py'))

def open_in_editor(path):
    if getenv('EDITOR') is not None:
        subprocess.run([getenv('EDITOR'), path])
    else:
        subprocess.Popen(['python', '-m', 'idlelib', path])

def write_local_text(filename, data):
    try:
        path = Path(sys.path[1]) / filename
        if not path.exists():
            with open(path, 'w+') as f:
                f.write(data)
        return path
    except OSError as _error:
        print(f'Critical error writing to file {filename}:\n    {_error}')
        return ''
