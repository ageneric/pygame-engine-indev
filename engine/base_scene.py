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
            child.draw(self.screen)

        for group in self.groups:
            group.draw(self.screen)

    def add_named_child(self, name: str, node):
        setattr(self, name, node)
        self.add_child(node)

    def add_child(self, node):
        self.nodes.append(node)

    def remove_child(self, node):
        self.nodes.remove(node)
        if node in self.event_handlers:
            self.event_handlers.remove(node)

    def handle_events(self, pygame_events):
        pass

    def change_scene(self, new_scene, *args):
        self.flag_new_scene = new_scene
        self.flag_new_scene_args = args

    # Get current window size (for resizeable displays).
    @property
    def display_size_x(self) -> int:
        return self.screen.get_width()

    @property
    def display_size_y(self) -> int:
        return self.screen.get_height()

    @property
    def display_size(self) -> (int, int):
        return self.screen.get_size()

