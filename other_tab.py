import engine.text as text
from engine.base_node import SpriteNode, NodeProperties
from engine.interface import Style


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
                     box_color=background, font=self.style.get('font'), color=self.style.get('color'))

