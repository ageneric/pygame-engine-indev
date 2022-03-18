"""A basic graphical editor to develop Pygame projects in a fixed format.
Run this file to start the editor."""

# pygame 2.0.1 (SDL 2.0.12, python 3.8.2)
import pygame as pg
import sys
from importlib import import_module
import editor_scenes
from constants import *

LAST_PROJECT_PATH = "C:/Users/maths/Desktop/Programming/Working/engine-pygame (6)/demo_project/"

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
    sys.path.insert(1, LAST_PROJECT_PATH)
    user_scenes = import_module('project_scenes')
    scene = editor_scenes.Editor(screen, clock, user_scenes, LAST_PROJECT_PATH)

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
    """import cProfile
    profile = cProfile.Profile()
    profile.enable()"""

    main()

    """profile.disable()
    import pstats
    pstats.Stats(profile).strip_dirs().sort_stats("cumulative").print_stats(24)
    pstats.Stats(profile).strip_dirs().sort_stats("tottime").print_stats(24)"""

pg.quit()
