class Scene:
    """Each scene manages the screen, updated and drawn
    once per frame. To switch scene, the new scene flag
    is set to the next scene (detect this in main loop).
    """
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock

        self.nodes = []
        self.groups = []
        self.flag_new_scene = None
        self.flag_new_scene_args = []
        self.event_handlers = []

    def update(self):
        for child in self.nodes:
            if child.enabled:
                child.update()

    def draw(self):
        # TODO: screen fill default?
        for child in self.nodes:
            if child.enabled:
                child.draw(self.screen)

        for group in self.groups:
            group.draw(self.screen)

    def add_named_child(self, name: str, node):
        setattr(self, name, node)
        self.add_child(node)

    def add_child(self, node):
        self.nodes.append(node)
        node.parent = self

    def remove_child(self, node):
        self.nodes.remove(node)
        node.parent = None
        if node in self.event_handlers:
            self.event_handlers.remove(node)

    def handle_events(self, pygame_events):
        pass

    def background(self, surface):
        """Fill the given surface with the color of self.background_color.
        The method does nothing if self.background_color is not set."""
        if hasattr(self, 'background_color'):
            surface.fill(self.background_color)

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
