# Version 1.1.0 changelog

## New features
Added the following command:
- `\divider_line`

Added the following aliases:
- `push` and `pull`

## User Interface
- Added the option to export cards as PNG files.
- QOL: the "Custom aliases" section can now properly be resized.
- Multiple small fixes: error messages handling and display, AOE creator window resizing, better handling of the "Cancel" action when saving a file.

## Documentation
- Added the Demolitionist's cards as an example.
- Updated README.
- Added technical documentation for converting pixel coordinates to hexagonal coordinates.
- Added instructions to package The Sleeping Lion for Windows.

## Bugfixes:
- Fixed several bugs for aliases with multiple arguments.
- Using a macro to highlight a word in the middle of a text now properly show spaces before and after the word.
- Setting a card's name to an empty field no longer silently deletes the card.
- Clicking on a hexagon in the AOE creator now correctly selects the appropriate hex instead of one of its neighbors.
- When using `\charges` with 3 arguments, the third circle is no longer shifted to the right.
- Updated element generation aliases to always be written using the big font size.
- Command arguments consisting only of macros are now recognised as empty and no longer throw a Python error.
- Fixed a rare bug where a line which should end with an image instead displayed the next word, creating a text overflow.
- Fixed a bug where a few specific AOEs (such as the `skewer` AOE) were shifted, resulting in an overlap of the AOE with the next item, or an overflow.

## Packaging
Setup of a reliable and reproducible method to package and distribute The Sleeping Lion on Windows.