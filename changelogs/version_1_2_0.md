# Version 1.2.0 changelog

## New features
Added the following macro:
- `@banner` to display a black banner like the Mindthief's Augments.

Added the following aliases:
- `\invisible`

The `\aoe` command is now sensitive to the context's size and can be made smaller using `@small`.

When defining custom aliases, it is now possible to reference a previously defined custom alias.

## User Interface
- Added a popup when deleting a card to confirm or cancel card deletion.
- Added a File->New option.
- Tabs can be reordered manually as well as sorted by level, initiative or ID.
- Added shortcuts to move through the entries in a tab (CTRL+TAB and CTRL+SHIFT+TAB).
- Added shortcuts to move through tabs (ALT+LEFT/RIGHT ARROW).
- Creation of a short user manual.

## Bugfixes:
- Using the `\multiline` command now adds a blank space before and after the command, so that the column of items isn't immediately next to what comes before and after.
- Adding text after the `\summon` command no longer causes The Sleeping Lion to freeze.
- Custom aliases without arguments are now properly detected when used in the middle of a line.
- Custom aliases without arguments but with similar names no longer get mixed up.

## Packaging
- Fixed a bug where NSIS took a hardcoded version number for the Sleeping Lion instead of taking the one for the current version.