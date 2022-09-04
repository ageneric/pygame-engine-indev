# Pygame Engine Help Modules
## Introduction
This is the help interface for Pygame Engine, a program used to build applications and games using Python and the Pygame library. If using scripting, you will code in an Object Oriented style.

To build a graphical interface, start by creating an Instance in the Node Tree. An Instance is a copy of a class that may run scripts or have graphics.

To build games with Python scripting, start by defining a class in the Project Tab. A class is a blueprint for an entity used to create Instances.


You can make a copy of any project by simply duplicating the folder.
The only way to make a new project is to duplicate the blank project folder, in this version. Project folders can be anywhere on your computer.

## Scene
Your project is contained in Scenes. Most projects use one Scene exactly.

The open Scene contains all of the Nodes that currently exist. You can view this in the Tree Tab.

The Scene script is found in project_scenes.py. All Scene scripts are placed in this file.

A Scene script can be used to write game code. For example, this is useful if you are modifying the display, or have global calculations to run. You may move game code into a Node script instead, for better organisation.

To get the Scene from a Node script, for accessing any Scene methods and attributes you may define, use:
`self.scene()`
(where self is a Node)

If the following methods are implemented, they will be called every frame in the following order:
`def handle_events(self, pygame_events): ...`
`def update(self): ...`
`def draw(self): ...`
(where self is a Scene)

To get the top-level Nodes list, use:
`self.nodes`
(where self is a Scene)

Other Scene properties that may be useful are:
`self.groups`
`self.screen_size_x, self.screen_size_y, self.screen_size`
(where self is a Scene)

To change the current Scene during play, use:
`self.change_scene(self, new_scene, *args)`
(where self is a Scene)

## Node
The Node class is the base class of all engine classes. An Instance of the Node class is referred to as a Node.

A Node represents an entity and contains all the data and scripts required for it to perform some purpose. A Node is part of the tree of Nodes. You can view this in the Tree Tab.

A Node has a single parent in the tree of Nodes, which is another Node or a Scene. To get the parent, use:
`self.parent`
(where self is a Node)

A Node has multiple child Nodes that have it as a parent. To get the child Nodes list, use:
`self.nodes`
(where self is a Node)

A Node has a position and rectangular size, which is stored on the transform attribute. To get or set these attributes, use (for example):
`self.transform.x = 10`
(where self is a Node)
All the transform properties are listed below. Setting some properties will change others accordingly.

Position is relative to the parent, increases to the right and left, and is measured in pixels from the anchor point. The properties are:
`> x, y, position`
Size is measured in pixels. Resizing takes place about the anchor point. The properties are:
`> width, height, size`
The anchor point position is set as a proportion of the size, where (0, 0) is left, top and (1, 1) is right, bottom. The properties are:
`> anchor_x, anchor_y, anchor_position`

To get the on-screen rectangle of the Node, instead of its relative position, use:
`self.rect.position`
`self.rect.size`
(where self is a Node)

To check for collisions, either with another Node or a point, use:
`self.rect.colliderect(other.rect)`
`self.rect.collidepoint((x, y))`
(where self and other are Nodes)

If the following methods are implemented, they will be called every frame in the following order:
`def event(self, event): ...`
`def update(self): ...`
`def draw(self): ...`
(where self is a Node)

Nodes can be disabled, which will stop them from updating or drawing. To do this, set its enabled property (for example):
`self.enabled = False`
(where self is a Node)

To remove the Node, use:
`self.remove()`
(where self is a Node)

## SpriteNode
The SpriteNode class is a kind of Node that is suitable for graphics. (It is a subclass of both the Node class and the pygame.sprite.DirtySprite class.)

To change the appearance, first, draw to its image attribute. This is a Pygame surface with size equal to the transform size (for example):
`self.image.fill((0, 0, 255))`
`pygame.draw.rect(self.image, (80, 80, 80), (5, 0, 50, 10))`
(where self is a SpriteNode)
Then, to update the graphic shown on screen for this frame, use:
`self.dirty = 1`
(where self is a SpriteNode)
This property is reset from 1 to 0 every frame. To always update the graphic, set this property to 2.

All Node properties are available, in addition to:
`self.visible # read-only`
`self.groups`
(where self is a SpriteNode)

SpriteNodes support transparency if initialised with an image or fill color with an alpha channel (for example):
`super().__init__(groups, image=your_per_pixel_alpha_image)`
`super().__init__(groups, fill_color=(80, 0, 0, 80))`
(within the constructor of a SpriteNode subclass)

## Text
`text.draw(surface, message: str, position: (int, int), color (optional), font (optional), text_sprite=None, static=False, justify=False) -> pygame.Rect:`
(following import engine.text as text)

Draws (blit) text to the surface at the (x, y) position specified.

Justify - set to True/False to centre in both/neither axes, or pick separately for the (x, y) axes, i.e. set to (True, False) to centre horizontally and not vertically.
Static - set to True to cache the text sprite (for faster drawing).

`text.box(surface, message: str, position: (int, int), width=None, height=None, middle=False, box_color (optional), color (optional), font (optional)) -> pygame.Rect:`
(following import engine.text as text)

Draws (blit) a text box to the surface at the (x, y) position specified.

The width and height, if omitted, fit the text's size. If either is omitted, the text sprite is cached. Set middle = True to centre text.

## Groups
Groups contain multiple sprites (SpriteNodes) and have a range of uses. By default, sprites are always in group 0 (the draw group) and can be added to any number of additional groups.

A scene has a list of groups. This is displayed in the Inspector tab when nothing is selected as the scene groups table. To get this list, use:
`self.groups`
(where self is a Scene)

Group 0 is the draw group, used for drawing all sprites. To get this group, use either:
`self.draw_group`
`self.groups[0]`
(where self is a Scene)

You can create group 1 and onwards to be used for collision checking (for example):
`self.groups.append(pygame.sprite.Group())`
(where self is a Scene)
(within the constructor of a Scene subclass)

Add a sprite to a group by editing its Group IDs in the Inspector.

Collision checking can be done between sprites and groups (for example):
`pygame.sprite.spritecollideany(self, self.scene().groups[1])`
(where self is a SpriteNode)
This returns a single sprite from group 1 that collides with this sprite.

You can check if a sprite is part of a group (for example):
`self.scene().groups[1].has(self)`
(where self is a SpriteNode)
Read the pygame.sprite documentation for more group methods.

To get the Scene from a Node script, for accessing the above Scene methods and attributes, use:
`self.scene()`
(where self is a Node)

# EOF
