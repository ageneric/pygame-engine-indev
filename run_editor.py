"""A basic graphical editor to develop Pygame projects in a fixed format.
Run this file to start the editor."""

# pygame 2.0.1 (SDL 2.0.12, python 3.8.2)
import pygame as pg
from importlib import import_module
import editor
from constants import *

LAST_PROJECT_MODULE = "scenes"
SCENE_NAME = "ExampleHandling"

print('1/3 Starting: pygame initialisation')
clock = pg.time.Clock()

pg.init()

def main():
    print(f'2/3 Starting: screen resolution {display_width}, {display_height}')
    if pg.version.vernum[0] >= 2:
        screen = pg.display.set_mode((display_width, display_height), pg.RESIZABLE)
    else:
        screen = pg.display.set_mode((display_width, display_height))
        print("Editor warning: the editor is designed for use with Pygame 2.")

    pg.key.set_repeat(500, 50)

    print('3/3 Starting: main loop')
    scenes = import_module(LAST_PROJECT_MODULE)
    scene = editor.Editor(screen, clock, getattr(scenes, SCENE_NAME))

    running = True

    while running:
        # Scene switching ---
        if scene.flag_new_scene is not None:
            scene = scene.flag_new_scene(screen, clock, *scene.flag_new_scene_args)

        # Handle events --- (pg.key.get_pressed() for pressed keys)
        if pg.event.get(pg.QUIT):
            running = False
        else:
            events = pg.event.get()
            scene.handle_events(events)

        # Update scene and display --
        scene.update()
        rectangle_list = scene.draw()

        pg.display.update(rectangle_list)
        clock.tick(FPS)


if __name__ == "__main__":
    main()

pg.quit()
