import pygame
from .template import load_nodes, read_local_json

class Scene:
    """Each scene manages the screen, updated and drawn
    once per frame. To switch scene, the new scene flag
    is set to the next scene (detect this in main loop).
    """
    is_origin = 'Scene'

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock

        self.nodes = []
        self.group_draw = None
        self.groups = []
        self.flag_new_scene = None
        self.flag_new_scene_args = []
        self.background_color = None
        self.background_surf = None
        self.event_handlers = {}

    def update(self):
        for child in self.nodes:
            if child.enabled:
                child.update()

    def draw(self):
        for child in self.nodes:
            child.draw()
        # Use the draw group to draw all sprites if used
        if self.group_draw is not None:
            return self.group_draw.draw(self.screen)
        else:
            return None

    def add_event_handler(self, node, additional_types=None):
        """The event types to register the node for are its
        event_handler attribute if present plus the additional_types."""
        event_types = getattr(node, 'event_handler', [])
        if additional_types:
            event_types = event_types + additional_types

        for event_type in event_types:
            handler_list = self.event_handlers.get(event_type, None)
            if handler_list is None:
                self.event_handlers[event_type] = [node]
            elif node not in handler_list:
                handler_list.append(node)

    def remove_event_handler(self, node, additional_types=None):
        """The event types to de-register the node from are its
        event_handler attribute if present plus the additional_types."""
        event_types = getattr(node, 'event_handler', [])
        if additional_types:
            event_types = event_types + additional_types

        for event_type in event_types:
            if node in self.event_handlers[event_type]:
                self.event_handlers[event_type].remove(node)
            else:
                print(f'Engine warning: could not find {node} when removing '
                      'its event handler. It may have been deleted already.')

    def handle_events(self, pygame_events):
        for event in pygame_events:
            # Redraw screen when restored or resized (minimization clears screen)
            if hasattr(self, 'group_draw') and event.type == pygame.VIDEOEXPOSE:
                self.resize_draw_group()
            # Pass events to event handlers using the event method
            event_handler_nodes = self.event_handlers.get(event.type, None)
            if event_handler_nodes:
                for node in event_handler_nodes:
                    if node.enabled:
                        node.event(event)

    def create_draw_group(self, background_color):
        """Sets self.group_draw to a new LayeredDirty group and fills
        the background surface with the given color.
        Set background_color to None for a transparent background."""
        self.background_color = background_color
        self.background_surf = pygame.Surface(self.screen_size)
        if self.group_draw is None:
            self.group_draw = pygame.sprite.LayeredDirty()
        if self.background_color is not None:
            self.background_surf.fill(self.background_color)
            self.group_draw.clear(self.screen, self.background_surf)
        self.groups.append(self.group_draw)

    def resize_draw_group(self):
        if not isinstance(self.background_surf, pygame.Surface):
            return
        self.background_surf = pygame.Surface(self.screen_size, 0, self.background_surf)
        if self.background_color is not None:
            self.background_surf.fill(self.background_color)
            self.group_draw.clear(self.screen, self.background_surf)
        self.group_draw.repaint_rect(self.screen.get_rect())

    def change_scene(self, new_scene, *args):
        self.flag_new_scene = new_scene
        self.flag_new_scene_args = args

    # Helper methods to get the current window size
    @property
    def screen_width(self) -> int:
        return self.screen.get_width()

    @property
    def screen_height(self) -> int:
        return self.screen.get_height()

    @property
    def screen_size(self) -> (int, int):
        return self.screen.get_size()

    # Generic user scene initialisation
    def load_template(self):
        scenes_name = read_local_json('project_config')['scenes_file']
        project_templates = read_local_json(scenes_name)

        template = project_templates.get(type(self).__name__, {})
        if not template:
            print(f'Engine warning: Scene data not found for {self}.')
        # Initialise groups based on the template 'groups' key
        groups = template.get('groups', [])
        if len(groups) > 0:
            # Group 0 is Scene.group_draw and its fill colour is specified
            # Is the LayeredDirty used for drawing sprites
            self.create_draw_group(groups[0])
            # Further groups are used for collisions; their names are specified
            for group_name in groups[1:]:
                new_group = pygame.sprite.Group()
                self.groups.append(new_group)
                setattr(self, group_name, new_group)

        load_nodes(self, template)
        self.template = template
