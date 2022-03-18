from engine.base_scene import Scene
import engine.template

class ExampleRemote(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.load_template()

class ExampleBlank(Scene):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)

    def update(self):
        super().update()
