import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk
from pathlib import Path
from yaml import safe_dump

from .abstract_tab import AbstractTab
from ..constants import card_width, card_height
from ..gloomhavenclass import GloomhavenClass
from ..utils import freeze_event, unfreeze_event
from ..backupFileHandler import BackupFileHandler
from .card_tab import get_text_from_view

class CharacterTab(AbstractTab, GObject.Object):
    @GObject.Signal
    def rgba_changed(self):
        pass
    @GObject.Signal
    def path_to_icon_changed(self):
        pass

    def __init__(self, path_to_glade, tab_name = "Class attributes"):
        builder = Gtk.Builder()
        builder.add_from_file(path_to_glade)
        AbstractTab.__init__(self, builder, tab_name)
        GObject.GObject.__init__(self)

        self.class_icon = builder.get_object("choose_class_icon")
        self.class_name = builder.get_object("class_name")
        self.aliases_box = builder.get_object("custom_aliases_view")

        color_box = builder.get_object("color_box")
        self.color_chooser = Gtk.ColorChooserWidget()
        self.color_chooser.connect("notify", self.rgba_modified)
        self.color_chooser.set_hexpand(True)

        color_box.add(self.color_chooser)
        self.color_chooser.show()

    def update_custom_character(self, custom_character: GloomhavenClass, backup: BackupFileHandler):
        """
        Modify the given Gloomhaven class based on the information contained in this tab.
        Return True if at least one field in the tab is different from the information in the GloomhavenClass
        (and therefore if the Gloomhaven class is really modified).
        """
        was_modified = False
        if custom_character.name != self.class_name.get_text().strip():
            custom_character.name = self.class_name.get_text().strip()
            was_modified = True

        rgba_object = self.color_chooser.get_rgba()
        # Convert to integers between 0 and 255
        red = int(rgba_object.red *255)
        green = int(rgba_object.green *255)
        blue = int(rgba_object.blue *255)
        color_modified = custom_character.update_color(red, green, blue)
        was_modified = was_modified or color_modified

        ui_path_to_icon = self.class_icon.get_filename()
        class_path_to_icon = backup.get_absolute_path(custom_character.path_to_icon)
        if ui_path_to_icon is not None and class_path_to_icon != ui_path_to_icon:
            custom_character.path_to_icon = backup.get_relative_path(ui_path_to_icon)
            was_modified = True

        ui_aliases = get_text_from_view(self.aliases_box).strip()
        if ui_aliases != custom_character.raw_aliases:
            custom_character.update_user_aliases(ui_aliases)
            was_modified = True

        return was_modified

    def load_custom_character(self, custom_character: GloomhavenClass, backup: BackupFileHandler):
        """
        Modify the tab to reflect the given Gloomhaven class.
        """
        self.class_name.set_text(custom_character.name)
        # Note: we could have used GObject.freeze_notify(), but then all signals which were stopped are still
        # handed out when the unfreeze happens. We want to suppress the signal entirely.
        freeze_event(self.color_chooser, self.rgba_modified)
        self.color_chooser.set_rgba(Gdk.RGBA(custom_character.color["red"]/255, custom_character.color["green"]/255,
                                             custom_character.color["blue"]/255, 1))
        unfreeze_event(self.color_chooser, "notify", self.rgba_modified)
        if custom_character.path_to_icon is not None and len(custom_character.path_to_icon) >0:
            # Apparently, set_filename can't take None value. However, get_filename can return None...
            self.class_icon.set_filename(backup.get_absolute_path(custom_character.path_to_icon))

        self.aliases_box.get_buffer().set_text(custom_character.raw_aliases)

    def rgba_modified(self, widget, param):
        # Unfortunately, color-activated is only available in Gtk 4.0. Here, we try to recreate the signal meaning
        # "the user changed some sort of RGB value."
        if param.name == "rgba":
            self.emit("rgba_changed")

    def load_icon(self, *args):
        self.emit("path_to_icon_changed")
