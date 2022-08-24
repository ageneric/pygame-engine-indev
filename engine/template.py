"""Store and load a tree of node instances."""

import json
import sys
import inspect
from pathlib import Path
from importlib import import_module, reload
import engine.base_node
from engine.base_node import NodeProperties
import engine.interface

NODE_CLASSES = ('Node', 'SpriteNode')
INTERFACE_CLASSES = ('Button', 'Toggle', 'TextEntry', 'GridList', 'Scrollbar')
DATA_NODE = ('x', 'y', 'width', 'height', 'anchor_x', 'anchor_y', 'enabled')
JSON_CAN_SERIALISE_TYPES = (int, bool, float, str, list, tuple, dict)

node_to_template = {}

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
    node_to_template.clear()
    node_to_template[scene] = template

    for name in template.get('modules', []):
        if sys.modules.get(name):
            module = reload(sys.modules[name])  # reload previously imported modules
        else:
            module = import_module(name)  # import new modules
        scene.user_classes[name] = getattr(module, name.split('.')[-1], None)

    if template.get('nodes'):
        load_nodes(scene, template['nodes'], scene)

def load_nodes(scene, tree_template: list, parent):
    """parent is a Scene or Node or subclass of either.
    Loads the template list into the parent's nodes."""
    new_node = None
    for element in tree_template:
        if isinstance(element, list):
            load_nodes(scene, element, new_node)
        else:
            new_node = instantiate(scene, element, parent)

def instantiate(scene, template: dict, parent):
    inst_class = resolve_class(scene, template['class'])
    node_props = NodeProperties(parent, *template['data_node'])
    # Get '*args' and '**kwargs' arguments; replace None with empty
    arguments = template.get('args', None)
    arguments = {} if arguments is None else arguments
    keyword_arguments = template.get('kwargs', None)
    keyword_arguments = {} if keyword_arguments is None else keyword_arguments
    # Get groups argument if used
    groups = template.get('data_groups', None)
    if groups is not None:
        # Groups are stored as their index in the scene groups
        if isinstance(groups, int):  # single group
            groups = scene.groups[groups]
        elif hasattr(groups, '__len__'):  # includes list, tuple
            groups = [scene.groups[group] for group in groups]
        # arguments.insert(0, groups)
        arguments_buffer = {'groups': groups}
        arguments_buffer.update(arguments)
        arguments = arguments_buffer

    new_node = inst_class(node_props, *arguments.values(), **keyword_arguments)
    if template.get('layer', None) is not None:
        new_node.groups()[0].change_layer(new_node, template['layer'])

    node_to_template[new_node] = template
    return new_node

def resolve_class(scene, name):
    # Resolve the class either from a library module or user module
    if name in NODE_CLASSES:
        return getattr(engine.base_node, name)
    elif name in INTERFACE_CLASSES:
        return getattr(engine.interface, name)
    elif name in scene.user_classes:
        return scene.user_classes[name]
    else:
        return NodeClassNotFound

class NodeClassNotFound(engine.base_node.Node):
    def __init__(self, node_props, *args, **kwargs):  # accept any arguments
        super().__init__(node_props)

def register_node(scene, parent_template: dict, new_node):
    """Create a template for the new node and add it to the
    parent template's list of child node templates."""
    transform = new_node.transform
    new_template = {
        'class': type(new_node).__name__,
        'data_node': (transform.x, transform.y, transform.width, transform.height,
                      transform.anchor_x, transform.anchor_y, new_node.enabled)
    }
    # Get ordered list of the constructor parameters without self
    parameters = inspect.signature(new_node.__class__).parameters
    # Store groups as their index in the scene groups
    groups_method = getattr(new_node, 'groups', None)
    if parameters.get('groups') is not None and callable(groups_method):
        new_template['data_groups'] = list(group_indexes(scene, new_node))
    # Store all other parameters that match a current attribute
    for attribute, parameter in parameters.items():
        if attribute not in ('node_props', 'groups', 'args', 'kwargs', 'style') and hasattr(new_node, attribute):
            value = getattr(new_node, attribute)
            # TODO: support non-serializable types
            if (value is None or type(value) in JSON_CAN_SERIALISE_TYPES) and value != parameter.default:
                if parameter.kind == parameter.POSITIONAL_OR_KEYWORD:
                    if not new_template.get('args', False):
                        new_template['args'] = {}
                    new_template['args'][attribute] = value
                elif parameter.kind == parameter.KEYWORD_ONLY:
                    if not new_template.get('kwargs', False):
                        new_template['kwargs'] = {}
                    new_template['kwargs'][attribute] = value

    node_to_template[new_node] = new_template

def group_indexes(scene, node):
    for group in node.groups():
        if group in scene.groups:
            yield scene.groups.index(group)

def update_node(node, attribute: str, scene=None):
    """Update the given node's template. Pass the scene if updating groups."""
    template = node_to_template.get(node, None)
    if template is None:
        return

    arguments = template.get('args', {})
    if attribute == 'groups':
        template['data_groups'] = list(group_indexes(scene, node))
    elif attribute == 'layer':
        template['layer'] = getattr(node, '_layer', None)
    elif attribute in arguments:
        arguments[attribute] = getattr(node, attribute, None)
        template['args'] = arguments
    elif attribute in DATA_NODE:
        data_node = list(template['data_node'])
        if DATA_NODE.index(attribute) < 6 and hasattr(node, 'transform'):
            node = getattr(node, 'transform', {})
        data_node[DATA_NODE.index(attribute)] = getattr(node, attribute, None)
        template['data_node'] = data_node

def get_tree_template(tree, tree_template: list):
    for node in tree.nodes:
        node_template = node_to_template.get(node, None)
        if node_template:
            tree_template.append(node_template)
            if node.nodes:
                layer_template = []
                get_tree_template(node, layer_template)
                if layer_template:
                    tree_template.append(layer_template)
