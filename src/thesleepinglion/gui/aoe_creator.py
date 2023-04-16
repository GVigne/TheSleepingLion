import gi
gi.require_version('Gtk', '3.0')

from ..hexagonal_grid import HexagonalGrid, HexagonDict
from ..utils import get_gui_asset, gtk_error_message
from ..errors import InvalidAoEFile
from ..backupFileHandler import AoEFileHandler
from gi.repository import Gtk, Gdk, GObject
from pathlib import Path
from tempfile import mkdtemp
from shutil import rmtree

class AoECreator(GObject.Object):
    @GObject.Signal
    def aoe_changed(self):
        pass

    def __init__(self):
        GObject.GObject.__init__(self)

        builder = Gtk.Builder()
        builder.add_from_file(get_gui_asset("aoe_creator.glade"))
        builder.connect_signals(self)

        self.window = builder.get_object("aoe_window")
        self.aoe_drawing_area = builder.get_object("aoe_drawing_area")
        self.red_button = builder.get_object("red_color")
        self.grey_button = builder.get_object("grey_color")
        self.custom_color = builder.get_object("custom_color")

        color_box = builder.get_object("aoe_color")
        self.color_chooser = Gtk.ColorChooserWidget()
        self.color_chooser.connect("notify", self.rgba_modified)
        color_box.add(self.color_chooser)
        self.color_chooser.show()

        self.hexagon_side = 80
        self.drawing_grid = HexagonalGrid(self.hexagon_side)

        # Fixed size hexagon grid used to draw the background. Has hexes with negative coordinates so (0,0) is
        # at the center of the cairo context. It will modified according to user's input.
        self.drawn_hexagons = HexagonDict()
        self.background_x_range = (-3,5)
        self.background_y_range = (-3,5)
        for x in range(self.background_x_range[0], self.background_x_range[1]):
            for y in range(self.background_y_range[0], self.background_y_range[1]):
                self.drawn_hexagons[(x,y)] = {"red": 255, "green": 255, "blue": 255}
        # The origin for the cairo context is a the top left of the screen. For the hexagonal grid, its the
        # coordinates of the top left hexagon. self.drawing_origin is the vector allowing the conversion between both.
        self.drawing_origin = (self.drawing_grid.get_width(self.drawn_hexagons)/2,
                                self.drawing_grid.get_height(self.drawn_hexagons)/2)

        # Make tempfile an attribute of this class so it can be deleted when the AoE creator is closed.
        tmpdir = mkdtemp()
        tmpfile = Path(tmpdir) / "Untitled.aoe"# A temporary file which will be deleted when the user closes the AOE creator
        tmpfile.touch() # Create the temporary file.
        self.tmpdir = tmpdir
        self.aoe_backup_handler = AoEFileHandler(tmpfile)
        self.connect("aoe_changed", self.aoe_backup_handler.automatic_save)
        self.aoe_backup_handler.connect("change_window_title", self.change_window_title)

        self.window.show_all()
        self.window.maximize()

    def aoe_area_clicked(self, window, event):
        x, y = self.drawing_grid.pos_to_coord(event.x-self.drawing_origin[0], event.y-self.drawing_origin[1], self.drawn_hexagons)
        if x < self.background_x_range[0] or x >= self.background_x_range[1] or y < self.background_y_range[0] or y >= self.background_y_range[1]:
            # Out of bounds, do nothing
            return

        color = {"red": 255, "green": 255, "blue": 255}
        if self.red_button.get_active():
            color = {"red": 255, "green": 0, "blue": 0}
        elif self.grey_button.get_active():
            color = {"red": 83, "green": 84, "blue": 86}
        else:
            # custom_color is active
            rgba_object = self.color_chooser.get_rgba()
            # Convert to integers between 0 and 255
            red = int(rgba_object.red *255)
            green = int(rgba_object.green *255)
            blue = int(rgba_object.blue *255)
            color = {"red": red, "green": green, "blue": blue}

        if (x,y) not in self.drawn_hexagons or self.drawn_hexagons[(x,y)] != color:
            # New hexagon, or hexagon with a different color than the one currently selected
            self.drawn_hexagons[(x,y)] = color
        else:
            # The user is clicking on a hexagon which is already of the given color.
            self.drawn_hexagons[(x,y)] = {"red": 255, "green": 255, "blue": 255}

        self.emit("aoe_changed")
        self.aoe_drawing_area.queue_draw()

    def rgba_modified(self, widget, param):
        # Unfortunately, color-activated is only available in Gtk 4.0. Here, we try to recreate the signal meaning
        # "the user changed some sort of RGB value."
        if param.name == "rgba":
            self.custom_color.set_active(True)

    def draw(self, widget, cr):
        cr.translate(self.drawing_origin[0], self.drawing_origin[1])
        cr.move_to(0,0)
        self.drawing_grid.draw(cr, self.drawn_hexagons)

    def change_window_title(self, event):
        """
        Automatically called by the aoe backup handler. This is a notification that the AOE window should have
        its title changed.
        """
        self.window.set_title(self.aoe_backup_handler.get_window_title())

    def save_aoe(self, widget):
        """
        For code simplicity, this function should be called whenever the user wants to save the current AOE.
        """
        if self.aoe_backup_handler.no_save_path():
            # Ask the user where he wants to save his file as it is currently a temporary file.
            self.save_aoe_as(None)
        else:
            self.aoe_backup_handler.save(self.drawn_hexagons)

    def save_aoe_as(self, widget):
        dlg = Gtk.FileChooserDialog(title = "Save as", parent = None,
                                           action = Gtk.FileChooserAction.SAVE)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                    Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        dlg.set_modal(True)
        dlg.set_do_overwrite_confirmation(True)
        dlg.set_current_name(f"Untitled.aoe")

        response = dlg.run()
        if response == Gtk.ResponseType.OK:
            self.aoe_backup_handler.new_path(dlg.get_filename())
            self.save_aoe(None)
        dlg.destroy()

    def open_aoe(self, widget):
        """
        Close the current AOE and open a new one.
        WARNING: this is mostly a code duplicate from the main window.
        """
        if not self.aoe_backup_handler.safe_to_close():
            dlg = Gtk.MessageDialog()
            dlg.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.NO,
                        Gtk.STOCK_YES, Gtk.ResponseType.YES,
                        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
            dlg.set_markup("The current AoE file isn't saved. Do you want to save it before opening a new file?")
            dlg.set_modal(True)
            response = dlg.run()
            if response == Gtk.ResponseType.CANCEL:
                dlg.destroy()
                return
            elif response == Gtk.ResponseType.YES:
                self.save_aoe(None)
            else:
                pass

            dlg.destroy()

        # Now open a dialog so the user may select a file.
        dlg = Gtk.FileChooserDialog(title = "Open", parent = None,
                                           action = Gtk.FileChooserAction.OPEN)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                    Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        filter = Gtk.FileFilter()
        filter.add_pattern("*.aoe")
        dlg.set_filter(filter)
        dlg.set_modal(True)
        response = dlg.run()
        if response == Gtk.ResponseType.OK:
            if self.aoe_backup_handler.available_backup(dlg.get_filename()):
                # Ask if a backup should be loaded
                backup_dlg = Gtk.MessageDialog()
                backup_dlg.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.NO,
                            Gtk.STOCK_YES, Gtk.ResponseType.YES)
                backup_dlg.set_markup("Something seems to have gone wrong the last you closed this .aoe file. Do you want to load a backup?")
                backup_dlg.set_modal(True)
                response = backup_dlg.run()
                if response == Gtk.ResponseType.YES:
                    # Load the backup
                    try:
                        self.drawn_hexagons = self.aoe_backup_handler.open_new_file(dlg.get_filename(), load_backup=True)
                        self.check_hexagons_integrity()
                        self.aoe_drawing_area.queue_draw()
                    except InvalidAoEFile:
                        gtk_error_message(f"The backup for the file {dlg.get_filename()} couldn't be read. Try loading the file directly.")
                else:
                    # This is simply the normal way to open a file. This also means that the backup file will be destroyed;
                    # the user has been warned and chose not to load it, we will assume it is irrelevant
                    try:
                        self.drawn_hexagons = self.aoe_backup_handler.open_new_file(dlg.get_filename())
                        self.check_hexagons_integrity()
                        self.aoe_drawing_area.queue_draw()
                    except InvalidAoEFile:
                        gtk_error_message(f"The file {dlg.get_filename()} couldn't be read. Make sure it is a .aoe file and try again.")
                backup_dlg.destroy()
            else:
                # This is the normal case: load the given file.
                try:
                    self.drawn_hexagons = self.aoe_backup_handler.open_new_file(dlg.get_filename())
                    self.check_hexagons_integrity()
                    self.aoe_drawing_area.queue_draw()
                except InvalidAoEFile:
                    gtk_error_message(f"The file {dlg.get_filename()} couldn't be read. Make sure it is a .aoe file and try again.")
        dlg.destroy()

    def check_hexagons_integrity(self):
        """
        self.drawn_hexagons should always be a hexagonal grid with hexagons in background_x_range and background_y_range:
        unclicked hexagons should be in blank.
        However, when a card is serialized, blank hexagons are removed. Here we add them back and make sure self.draw_hexagon
        is consistent with this window.
        """
        for x in range(self.background_x_range[0], self.background_x_range[1]):
            for y in range(self.background_y_range[0], self.background_y_range[1]):
                if (x,y) not in self.drawn_hexagons:
                    self.drawn_hexagons[(x,y)] = {"red": 255, "green": 255, "blue": 255}

    def aoe_key_pressed(self, window, event):
        # Check if the CONTROL key was pressed at the same time
        if event.get_state() & Gdk.ModifierType.CONTROL_MASK:
            if event.keyval == Gdk.KEY_s:
                # Control + S was pressed
                self.save_aoe(None)

    def aoe_window_destroy(self, window, event):
        if not self.aoe_backup_handler.safe_to_close():
            dlg = Gtk.MessageDialog()
            dlg.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.NO,
                        Gtk.STOCK_YES, Gtk.ResponseType.YES,
                        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
            dlg.set_markup("The current file isn't saved. Do you want to save it?")
            dlg.set_modal(True)
            response = dlg.run()
            if response == Gtk.ResponseType.CANCEL:
                dlg.destroy()
                return True # Yes, the signal has been dealt with. No need to propagate it!
            elif response == Gtk.ResponseType.YES:
                self.save_aoe(None)
            # If answer is NO, don't do anything: the backup file will handle it.

            dlg.destroy()

        self.aoe_backup_handler.close()
        rmtree(self.tmpdir) # Delete temporary directory
        self.window.close()

    def quit_aoe_window_clicked(self, button):
        self.window.close() # This will emit the window destroy signal which will get caught by self.aoe_window_destroy
