"""A basic graphical editor to prototype and edit rect-based PyGame layouts."""

# pygame 2.0.1 (SDL 2.0.12, python 3.8.2)
import pygame as pg
import legacy_scenes
from constants import *
from importlib import reload, import_module

print('1/3 Starting: pygame initialisation')
clock = pg.time.Clock()

pg.init()

def main():
    SURF_HEIGHT = 60
    
    print(f'2/3 Starting: screen resolution {display_width}, {display_height}.')
    if pg.version.vernum[0] >= 2:
        screen = pg.display.set_mode((display_width, display_height + SURF_HEIGHT), pg.RESIZABLE)
    else:
        screen = pg.display.set_mode((display_width, display_height + SURF_HEIGHT))

    surf = pg.Surface((display_width, display_height))
    surf_detail = pg.Surface((display_width, SURF_HEIGHT))

    print('3/3 Starting: main loop')
    scene = legacy_scenes.Test(surf, clock)
    scene_detail = legacy_scenes.Detail(surf_detail, clock)

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
            for event in events:
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_LSHIFT:
                        print("reset!")
                        # noinspection PyTypeChecker
                        reload(legacy_scenes)
                        scene = legacy_scenes.Test(surf, clock)
            scene.handle_events(events)

        # Update scene and display --
        scene.update()
        scene.draw()

        # Update detail surf --
        scene_detail.update()
        scene_detail.draw()
        
        screen.blit(surf, (0, 0))
        screen.blit(surf_detail, (0, surf.get_height()))

        pg.display.flip()
        # pg.display.update(rects)

        clock.tick(FPS)


if __name__ == "__main__":
    """import cProfile
    profile = cProfile.Profile()
    profile.enable()"""

    main()

    """profile.disable()
    import pstats
    pstats.Stats(profile).strip_dirs().sort_stats("cumulative").print_stats(20)"""

pg.quit()
