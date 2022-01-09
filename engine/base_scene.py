import pygame

class Scene:
    """Each scene manages the screen, updated and drawn
    once per frame. To switch scene, the new scene flag
    is set to the next scene (detect this in main loop).
    """
    is_origin = 0

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock

        self.nodes = []
        self.draw_group = None
        self.groups = []
        self.flag_new_scene = None
        self.flag_new_scene_args = []
        self.background_color = None
        self.mouse_handlers = []

    def update(self):
        for child in self.nodes:
            if child.enabled:
                child.update()

    def draw(self):
        for child in self.nodes:
            child.draw()

        if self.draw_group is not None:
            return self.draw_group.draw(self.screen)
        else:
            return None

    def add_child(self, node):
        """Called internally. To specify the parent of a Node on
        initialisation, set NodeProperties[0]. Do not use this method."""
        self.nodes.append(node)
        node.parent = self

    def remove_child(self, node):
        node.remove()
        if node in self.mouse_handlers:
            self.mouse_handlers.remove(node)

    def mouse_event(self, type, pos, **kwargs):
        pass
    def other_event(self, type, **kwargs):
        pass
    def handle_events(self, pygame_events):
        pass

    def create_draw_group(self, background_color):
        """Sets self.draw_group to a new LayeredDirty group and fills
        the background surface with the given color.
        Set background_color to None for a transparent background."""
        self.background_color = background_color
        self.background_surf = pygame.Surface(self.screen_size)
        if self.background_color is not None:
            self.background_surf.fill(self.background_color)
        if self.draw_group is None:
            self.draw_group = pygame.sprite.LayeredDirty()
        self.draw_group.clear(self.screen, self.background_surf)
        self.groups.append(self.draw_group)

    def resize_draw_group(self):
        self.background_surf = pygame.Surface(self.screen_size, 0, self.background_surf)
        if self.background_color is not None:
            self.background_surf.fill(self.background_color)
        self.draw_group.clear(self.screen, self.background_surf)
        self.draw_group.repaint_rect(self.screen.get_rect())

    def change_scene(self, new_scene, *args):
        self.flag_new_scene = new_scene
        self.flag_new_scene_args = args

    # Helper methods, to get the current window size
    @property
    def screen_size_x(self) -> int:
        return self.screen.get_width()

    @property
    def screen_size_y(self) -> int:
        return self.screen.get_height()

    @property
    def screen_size(self) -> (int, int):
        return self.screen.get_size()
