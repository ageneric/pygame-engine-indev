"""A basic graphical editor to prototype and edit rect-based PyGame layouts."""

# pygame 2.0.1 (SDL 2.0.12, python 3.8.2)
import pygame as pg
import scenes
from constants import *
from importlib import reload

print('1/3 Starting: pygame initialisation')
clock = pg.time.Clock()

pg.init()

def initialise_scenes(surf, surf_detail, first_scene_name, detail_scene_name):
    print(f'Initialising scenes ({first_scene_name}, {detail_scene_name})')
    scene = getattr(scenes, first_scene_name)(surf, clock)
    scene_detail = getattr(scenes, detail_scene_name)(surf_detail, clock)
    scene_detail.set_ref(scene)
    return scene, scene_detail

def main():
    SURF_HEIGHT = 150
    FIRST_SCENE_NAME = 'ExampleHandling'
    DETAIL_SCENE_NAME = 'ExampleDetail'
    
    print(f'2/3 Starting: screen resolution {display_width}, {display_height}')
    if pg.version.vernum[0] >= 2:
        screen = pg.display.set_mode((display_width, display_height + SURF_HEIGHT), pg.RESIZABLE)
    else:
        screen = pg.display.set_mode((display_width, display_height + SURF_HEIGHT))

    surf = pg.Surface((display_width, display_height))
    surf_detail = pg.Surface((display_width, SURF_HEIGHT))

    pg.key.set_repeat(500, 50)

    print('3/3 Starting: main loop')
    scene, scene_detail = initialise_scenes(surf, surf_detail, FIRST_SCENE_NAME, DETAIL_SCENE_NAME)

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
                    # Left shift: reload the scenes module and instantiate the scenes again
                    if event.key == pg.K_LSHIFT:
                        # noinspection PyTypeChecker
                        reload(scenes)
                        scene, scene_detail = initialise_scenes(surf, surf_detail, FIRST_SCENE_NAME, DETAIL_SCENE_NAME)
                    elif event.key == pg.K_TAB:
                        # Tab: toggle the tree tab refresh (temporary)
                        pg.draw.rect(scene_detail.tree_tab.image, (0, 0, 0), (0, 8, 8, 8))
                        scene_detail.tree_tab.enabled = not scene_detail.tree_tab.enabled
            scene.handle_events(events)

        # Update scene and display --
        scene.update()
        rects = scene.draw()

        # Update detail surf --
        scene_detail.update()
        scene_detail.draw()
        
        screen.blit(surf, (0, 0))
        screen.blit(surf_detail, (0, surf.get_height()))

        rects.append(pg.Rect(0, surf.get_height(), display_width, SURF_HEIGHT))
        pg.display.update(rects)

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
