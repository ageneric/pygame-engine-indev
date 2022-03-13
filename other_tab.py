import engine.text as text
from engine.base_node import SpriteNode, NodeProperties
from engine.interface import Style


def string_color(name: str):
    """Generates an arbitrary bright colour from the first six characters."""
    key = map(ord, name.ljust(6, ' '))
    color = []
    for i in range(3):
        c = (16 * next(key) + next(key)) % 256  # use next two values as color
        color.append(c if c > 137 else 247)  # make dark colour channels bright
    return color

class TabHeading(SpriteNode):
    def __init__(self, node_props: NodeProperties, group, message, **kwargs):
        super().__init__(node_props, group)
        self.style = Style.from_kwargs(kwargs)
        self.message = message

    def draw(self):
        super().draw()
        if self._visible and self.dirty > 0:
            style_get = self.style.get
            rect = text.box(self.image, self.message, (0, 0), height=style_get('tabsize'),
                            box_color=style_get('background'), color=style_get('color'),
                            font=style_get('font'))
            self.transform.size = rect.size  # resize to the text box

class SceneTab(SpriteNode):
    _layer = 0

    def __init__(self, node_props: NodeProperties, group, user_scene, **kwargs):
        super().__init__(node_props, group)
        self.style = Style.from_kwargs(kwargs)
        self.user_scene = user_scene

    def draw(self):
        super().draw()
        if self._visible and self.dirty > 0:
            background, tabsize = self.style.get('background'), self.style.get('tabsize')

            text.box(self.image, 'Scene', (0, 0), self.transform.width, tabsize,
                     box_color=background, color=self.style.get('color'), font=self.style.get('font'))
