import pygame

class Scene:
    """Each scene manages the screen, updated and drawn
    once per frame. To switch scene, the new scene flag
    is set to the next scene (detect this in main loop).
    """
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
            if child.enabled:
                child.draw(0)

        if self.draw_group is not None:
            return self.draw_group.draw(self.screen)

    def add_named_child(self, name: str, node):
        setattr(self, name, node)
        self.add_child(node)

    def add_child(self, node):
        self.nodes.append(node)
        node.parent = self

    def remove_child(self, node):
        self.nodes.remove(node)
        node.parent = None
        if node in self.mouse_handlers:
            self.mouse_handlers.remove(node)

    def handle_events(self, pygame_events):
        pass

    def create_draw_group(self, background_color):
        """Sets self.draw_group to a new LayeredDirty group and fills
        the background surface with the given color.
        Set background_color to None for a transparent background."""
        self.background_color = background_color
        background_surf = pygame.Surface(self.screen_size)
        if self.background_color is not None:
            background_surf.fill(self.background_color)
        self.draw_group = pygame.sprite.LayeredDirty()
        self.draw_group.clear(self.screen, background_surf)
        self.groups.append(self.draw_group)

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
