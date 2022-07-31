# engine-pygame
A basic graphical editor to prototype and develop Pygame projects in a fixed
format.

## Usage and Notice
To open the editor, run run_editor.py.

Please note that the demonstration project is run in editing mode, and your
edits will be saved!
- You can make a copy of the demonstration project by simply duplicating the folder.
- Similarly, the only way to make a new project is to duplicate the blank project folder.
- Project folders can be anywhere on your computer.

This version of the editor is distributed for demonstration purposes for
Altrincham Grammar School for Boys. The current version of this editor
will be published and maintained on Github in late Summer 2022 (after
the A-level exams). The editor should be made sufficiently featured for
some educational use.

Once published, it will be available from [my Github page](https://github.com/ageneric).

## engine (library)
A library for using Pygame in an object-oriented style with scenes. It is
designed to utilise the dirty rectangle method for drawing to the screen.
Game objects are Node or SpriteNode instances that belong to a tree.

### Dependencies
All the dependencies of Pygame, and in addition versions:
- CPython >= 3.7

### License
The engine library is distributed under GPL version 3. Please include your
own copy of the license if copying.

The graphical editor can be run to develop projects as permitted by the
license of the engine library (running the editor implies using the library),
with no further restriction on the projects it may be used for.
