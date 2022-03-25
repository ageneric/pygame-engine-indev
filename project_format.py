from pathlib import Path
import sys
import importlib

scene_template_code = """import pygame
from engine.base_scene import Scene

class {1}(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.load_template()
    
    # Called every frame. Optional.
    def update(self):
        super().update()
    
    # Called every frame. Optional.
    def draw(self):
        super().draw()
"""

node_subclass_code = """import pygame
from engine.base_node import Node, SpriteNode, NodeProperties

# Useful properties: self.parent, self.transform, self.enabled, self.rect, self.nodes
# Useful methods: self.scene(), self.remove()
# For SpriteNode use: self.image, self.visible; all pygame.sprite.DirtySprite methods

class {1}({2}):
    def __init__(self, node_props{3}):
        super().__init__(node_props{3})
    
    # Called every frame on every node in tree order. Optional.
    def update(self):
        super().update()
    
    # Called every frame on every node in tree order. Optional.
    def draw(self):
        super().draw()
"""

CONFIG_PATH = '__unused__'

"""
def fill_template(class_name, node_data):
    function_lines = []

    for serial_node in node_data:
        function_lines.append(serial_node)

    template.format(class_name, "\n\t".join(function_lines))
"""

def write_file(file_path, content):
    with open(file_path, "w") as file_script:
        file_script.write(content)


def open_project_directory(file_path: Path):
    # Check the given file path is a directory
    if not file_path.exists() or not file_path.is_dir():
        return None
    # Check there is a config file directly in the directory
    config_path_full = file_path / CONFIG_PATH
    if not config_path_full.exists() or config_path_full.is_dir():
        return None

    try:
        # Open the config file and save it as a list of lines
        with open(config_path_full, "r") as file_script:
            config = file_script.readlines()
        # Get list of files to dynamically import classes from
        return config[0].strip().split("/")
    except FileNotFoundError:
        return None
    except IOError:
        return None

class AddPath:
    def __init__(self, path):
        self.path = str(path)  # convert pathlib.Path to string

    def __enter__(self):
        # When initialised in a with statement, add path to sys.path
        # 1 is after the local module, and before global/library modules
        sys.path.insert(1, self.path)

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            sys.path.remove(self.path)
        except ValueError:
            raise ValueError(f"Could not remove temporary path: {(exc_type, exc_value, traceback)}")


def open_project(file_path: Path, module_paths):
    with AddPath(file_path):
        for module_path in module_paths:
            globals()[str(module_path)[-5:]] = importlib.import_module(str(file_path / module_path))

def invalid_files():
    pass
