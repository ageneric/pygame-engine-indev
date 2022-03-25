"""Store and load a tree of node instances."""

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
import inspect
from pathlib import Path
from importlib import import_module
import engine.base_node
from engine.base_node import NodeProperties
import engine.interface

NODE_CLASSES = ('Node', 'SpriteNode')
INTERFACE_CLASSES = ('Button', 'Toggle', 'TextEntry', 'GridList')
DATA_NODE = ('x', 'y', 'width', 'height', 'anchor_x', 'anchor_y', 'enabled')

nodes_to_template = {}

def read_local_json(filename: str):
    try:
        with open((Path(sys.path[1]) / filename).with_suffix('.json'), 'r') as f:
            return json.load(f)
    except OSError as _error:
        print(f'Critical error reading from file {filename}:\n    {_error}')
        return {}
    except json.decoder.JSONDecodeError as _error:
        print(f'Critical error reading from file {filename}:\n    {_error}')
        return {}

def write_local_json(filename, data):
    try:
        with open((Path(sys.path[1]) / filename).with_suffix('.json'), 'w+') as f:
            json.dump(data, f, separators=(',', ':'))
    except OSError as _error:
        print(f'Critical error writing to file {filename}:\n    {_error}')

def load_nodes_wrapper(scene, template: dict):
    scene.user_classes = {}
    nodes_to_template.clear()
    nodes_to_template[scene] = template

    for name in template.get('modules', []):
        module = import_module(name)
        scene.user_classes[name] = getattr(module, name.split('.')[-1], None)

    if template.get('nodes'):
        load_nodes(scene, template, scene)

def load_nodes(scene, template: dict, parent):
    """parent is a Scene or Node or subclass of either
    loads the template_list into the parent's nodes."""
    for template_node in template['nodes']:
        new_node = instantiate(scene, template_node, parent)

        if template_node['nodes']:
            load_nodes(scene, template_node, new_node)

def instantiate(scene, template: dict, parent):
    inst_class = resolve_class(scene, template['class'])
    node_props = NodeProperties(parent, *template['data_node'])
    # Get '*args' and '**kwargs' arguments, replace None with empty
    arguments = template.get('args', None)
    arguments = {} if arguments is None else arguments
    keyword_arguments = template.get('kwargs', None)
    keyword_arguments = {} if keyword_arguments is None else keyword_arguments

    groups = template.get('data_groups', None)
    if groups is None:
        new_node = inst_class(node_props, *arguments, **keyword_arguments)
    else:
        if isinstance(groups, int):
            groups = scene.groups[groups]
        elif hasattr(groups, '__len__'):  # includes list, tuple
            groups = [scene.groups[group] for group in groups]
        new_node = inst_class(node_props, groups, *arguments, **keyword_arguments)
    nodes_to_template[new_node] = template
    return new_node

def resolve_class(scene, name):
    # Resolve the class either from a library module or user module
    if name in NODE_CLASSES:
        return getattr(engine.base_node, name)
    elif name in INTERFACE_CLASSES:
        return getattr(engine.interface, name)
    else:
        return scene.user_classes[name]

def register_node(scene, template: dict, new_node):
    transform = new_node.transform
    new_template = {
        'class': type(new_node).__name__,
        'data_node': (transform.x, transform.y, transform.width, transform.height,
                      transform.anchor_x, transform.anchor_y, new_node.enabled),
        'nodes': []
    }
    signature = inspect.signature(new_node.__class__)
    groups_method = getattr(new_node, 'groups', None)
    if signature.parameters.get('groups') is not None and callable(groups_method):
        new_template['data_groups'] = []
        for group in new_node.groups():
            new_template['data_groups'].append(scene.groups.index(group))

    for attribute in signature.parameters:
        if attribute not in ('node_props', 'groups', 'args', 'kwargs'):
            new_template[attribute] = getattr(new_node, attribute, None)

    nodes_to_template[new_node] = new_template
    if not template.get('nodes'):
        template['nodes'] = [new_template]
    else:
        template['nodes'].append(new_template)

def update_node(node, attribute: str):
    print(node, attribute)
    template = nodes_to_template.get(node, None)
    if template is None:
        return

    arguments = template.get('args', {})
    if attribute in arguments:
        arguments[attribute] = getattr(node, attribute, None)
        template['args'] = arguments
    elif attribute == DATA_NODE[-1]:
        template['data_node'][-1] = getattr(node, attribute, None)
    elif attribute in DATA_NODE and hasattr(node, 'transform'):
        data_node_value = list(template['data_node'])
        data_node_value[DATA_NODE.index(attribute)] = getattr(node.transform, attribute)
        template['data_node'] = data_node_value

    print(template)
