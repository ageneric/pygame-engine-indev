"""Store and load a tree of node instances."""

NODE_CLASSES = ('Node', 'SpriteNode')
INTERFACE_CLASSES = ('Button', 'Toggle', 'TextEntry', 'GridList')

nodes_to_template = {}

"""
scene_template:
  screen:
    display_width = 400
    display_height = 300
  groups:
    - 'draw_group'
    - 'collision_group'
  group_modes:
    - (0, 0, 0)
  nodes:
    - class = SpriteNode
      data_node:
      data_groups = 0 or :
      args:
      nodes:
"""

import json
import sys
from importlib import import_module
import engine.base_node
from engine.base_node import NodeProperties
import engine.interface

def get_template(name):
    try:
        with open(sys.path[2] + '/project_scenes.json') as f:
            return json.load(f)[name]
    except FileNotFoundError:
        print('File not found!')
        return {}
    except OSError:
        print('Permission denied!')
        return {}

def load_nodes_wrapper(scene, template: dict):
    scene.user_classes = {}
    nodes_to_template.clear()

    for name in template.get('modules'):
        module = import_module(name)
        scene.user_classes[name] = getattr(module, name.split('.')[-1], None)

    load_nodes(scene, template, scene)

def load_nodes(scene, template: dict, parent):
    """parent is a Scene or Node or subclass of either
    loads the template_list into the parent's nodes."""
    for template_node in template['nodes']:
        new_node = instantiate(scene, template_node, parent)

        if template_node['nodes']:
            load_nodes(scene, template_node, new_node)

def instantiate(scene, template: dict, parent):
    # Resolve the class either from a library module or user module
    name = template['class']
    if name in NODE_CLASSES:
        inst_class = getattr(engine.base_node, name)
    elif name in INTERFACE_CLASSES:
        inst_class = getattr(engine.interface, name)
    else:
        inst_class = scene.user_classes[template['class']]

    node_props = NodeProperties(parent, *template['data_node'])
    arguments = template.get('args', [])
    keyword_arguments = template.get('kwargs', {})

    groups = template.get('data_groups', None)
    if groups is None:
        return inst_class(node_props, *arguments, **keyword_arguments)
    else:
        scene_groups = scene.groups['data_groups']
        if isinstance(groups, int):
            groups = scene_groups[groups]
        elif hasattr(groups, '__index__'):  # includes list, tuple
            groups = [scene_groups[group] for group in groups]

        return inst_class(node_props, groups, *arguments, **keyword_arguments)

def register_node(template: dict, new_node):
    transform = new_node.transform
    new_template = {
        'class': new_node.__class__,
        'data_node': (transform.x, transform.y, transform.width, transform.height,
                      transform.anchor_x, transform.anchor_y, new_node.enabled),
        'nodes': []
    }
    # TODO: implement data_groups and args fields

    template['nodes'].append(new_template)

def update_template(tree):
    pass

