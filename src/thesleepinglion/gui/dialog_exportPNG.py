import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
import cairo
from pathlib import Path

from ..gloomhavenclass import GloomhavenClass
from ..utils import get_gui_asset
from ..constants import card_height, card_width
from .select_cards_widget import SelectCardsForExportWidget

class ExportDialogPNG:
    def __init__(self, gloomhavenclass: GloomhavenClass):
        self.gloomhavenclass = gloomhavenclass

        builder = Gtk.Builder()
        builder.add_from_file(get_gui_asset("dialog_exportPNG.glade"))
        builder.connect_signals(self)
        self.dialog = builder.get_object("dialog")
        self.main_box = builder.get_object("main_box")

        # Insert a widget dedicated to card selection at topmost position
        self.select_cards_widget = SelectCardsForExportWidget(self.gloomhavenclass)
        self.main_box.add(self.select_cards_widget.widget)
        self.main_box.reorder_child(self.select_cards_widget.widget, 0)
        # Set the widget to expand and fill the given space. The "0" corresponds to padding (number of pixels between children)
        self.main_box.set_child_packing(self.select_cards_widget.widget, True, True, 0, Gtk.PackType.START)

        self.dialog.set_title("Export as PNG")
        self.dialog.show_all()

    def accept(self, event, id):
        if id == -3:
            if self.select_cards_widget.has_cards_to_save():
                # The export button was clicked

                # Ask the user for a path to save a file of a folder
                default_name = "New folder"
                if len(self.gloomhavenclass.name) > 0:
                    default_name = self.gloomhavenclass.name

                dlg = Gtk.FileChooserDialog(title = "Save folder as", parent = None,
                                            action = Gtk.FileChooserAction.CREATE_FOLDER)
                dlg.set_current_name(default_name)
                dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                    Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
                dlg.set_modal(True)
                dlg.set_do_overwrite_confirmation(True)
                response = dlg.run()
                if response == Gtk.ResponseType.OK:
                    self.save_cards_per_file(dlg.get_filename())
                    dlg.destroy()
                else:
                    # Don't close the main window
                    dlg.destroy()
                    return
        # At this point, the user hasn't canceled anything, so the dialog should be closed.
        self.dialog.destroy()

    def save_cards_per_file(self, export_path):
        # A dirty way to articially increase image resolution: we scale the entier context up.
        artifical_resolution = 3
        for card in self.select_cards_widget.get_cards_to_save():
            file_name = (Path(export_path) / card.name).with_suffix(".png")
            surface = cairo.ImageSurface(cairo.FORMAT_RGB24, artifical_resolution*card_width, artifical_resolution*card_height)
            surface.set_device_scale(artifical_resolution, artifical_resolution)

            cr = cairo.Context(surface)
            self.gloomhavenclass.draw_card(card, cr)
            surface.write_to_png(file_name)