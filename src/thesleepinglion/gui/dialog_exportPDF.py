import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import cairo
from pathlib import Path
from math import pi

from ..gloomhavenclass import GloomhavenClass
from ..utils import get_gui_asset
from ..constants import card_height, card_width
from .select_cards_widget import SelectCardsForExportWidget

class ExportDialogPDF:
    def __init__(self, gloomhavenclass: GloomhavenClass):
        self.gloomhavenclass = gloomhavenclass

        builder = Gtk.Builder()
        builder.add_from_file(get_gui_asset("dialog_exportPDF.glade"))
        self.dialog = builder.get_object("dialog")
        self.main_box = builder.get_object("main_box")
        self.one_card_per_page = builder.get_object("one_card_per_page")
        self.a4_page = builder.get_object("a4_page")
        self.one_card_per_file = builder.get_object("one_card_per_file")
        builder.connect_signals(self)

        # For each radio button, if it should create a new folder or not.
        self.buttons_create_folder  = {self.one_card_per_page: False,
                                       self.a4_page: False,
                                       self.one_card_per_file: True}
        # For each radio button, which function should be called to save files to disk.
        self.buttons_save_func  = {self.one_card_per_page: self.save_one_card_per_page,
                                   self.a4_page: self.save_cards_for_printing,
                                   self.one_card_per_file: self.save_one_card_per_file}
        # Insert a widget dedicated to card selection at topmost position
        self.select_cards_widget = SelectCardsForExportWidget(self.gloomhavenclass)
        self.main_box.add(self.select_cards_widget.widget)
        self.main_box.reorder_child(self.select_cards_widget.widget, 0)
        # Set the widget to expand and fill the given space. The "0" corresponds to padding (number of pixels between children)
        self.main_box.set_child_packing(self.select_cards_widget.widget, True, True, 0, Gtk.PackType.START)

        self.dialog.set_title("Export as PDF")
        self.dialog.show_all()

    def accept(self, event, id):
        if id == -3:
            if self.select_cards_widget.has_cards_to_save():
                # The export button was clicked

                # Ask the user for a path to save a file of a folder
                default_name = None
                if len(self.gloomhavenclass.name) > 0:
                    default_name = self.gloomhavenclass.name

                current_button_activated = self.get_activated_radio_button()

                if self.buttons_create_folder[current_button_activated]:
                    # Create a new folder
                    if default_name is None:
                        default_name = "New folder"
                    dlg = Gtk.FileChooserDialog(title = "Save folder as", parent = None,
                                                action = Gtk.FileChooserAction.CREATE_FOLDER)
                else:
                    # Create a new file
                    if default_name is None:
                        default_name = "Untitled"
                    default_name = f"{default_name}.pdf"
                    dlg = Gtk.FileChooserDialog(title = "Save as", parent = None,
                                                action = Gtk.FileChooserAction.SAVE)

                dlg.set_current_name(default_name)
                dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                            Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
                dlg.set_modal(True)
                dlg.set_do_overwrite_confirmation(True)
                response = dlg.run()
                if response == Gtk.ResponseType.OK:
                    # Call the dedicated function corresponding to the active radio button
                    save_func = self.buttons_save_func[current_button_activated]
                    save_func(dlg.get_filename())
                    dlg.destroy()
                else:
                    # Don't close the main window
                    dlg.destroy()
                    return
        # At this point, the user hasn't canceled anything, so the dialog should be closed.
        self.dialog.destroy()

    def get_activated_radio_button(self):
        """
        Returns the currently activated radio button. Didn't manage to implement it properly, so here is an if/else version.
        """
        if self.one_card_per_page.get_active():
            return self.one_card_per_page
        elif self.a4_page.get_active():
            return self.a4_page
        elif self.one_card_per_file:
            return self.one_card_per_file

    def save_one_card_per_page(self, export_path):
        save_path = Path(export_path).with_suffix(".pdf")
        surface = cairo.PDFSurface(save_path, card_width, card_height)
        cr = cairo.Context(surface)
        for card in self.select_cards_widget.get_cards_to_save():
            cr.save()
            self.gloomhavenclass.draw_card(card, cr)
            cr.restore()
            surface.show_page() # Save the page, so that each card is drawn on a separate page.
        surface.finish()

    def save_cards_for_printing(self, export_path):
        """
        Fit 8 cards on an A4 sheet (ie like when printing)
        """
        surface = cairo.PDFSurface(export_path, 595, 842) # A4 is 21/29.7 cm and cairo gives a DPI of 72 pt.
        cr = cairo.Context(surface)

        # 252.28 = 89mm with a DPI of 72 pt
        # Then, multiply by 8.5*7.5 as TSL's cards have a bigger border than standard Gloomhaven cards.
        # This factors makes it so the rune border has the correct size.
        cr.scale(8.5/7.5 * 252.28/card_height, 8.5/7.5 * 252.28/card_height)
        cr.rotate(-pi/2)
        pos = 0
        for card in self.select_cards_widget.get_cards_to_save():
            if pos == 4 :
                # Go back to the top of the page
                cr.translate(4*card_width, card_height)
            elif pos == 8:
                surface.show_page() # Create a new page
                cr.translate(5*card_width, -card_height) # Go back to the top left corner of the page
                pos = 0

            if pos == 0:
                # First card in a page
                cr.translate(-card_width, 0)
            cr.save()
            self.gloomhavenclass.draw_card(card, cr)
            cr.restore()
            cr.translate(-card_width, 0)
            pos += 1
        surface.finish()

    def save_one_card_per_file(self, export_path):
        for card in self.select_cards_widget.get_cards_to_save():
            file_name = (Path(export_path) / card.name).with_suffix(".pdf")
            surface = cairo.PDFSurface(file_name, card_width, card_height)
            cr = cairo.Context(surface)
            self.gloomhavenclass.draw_card(card, cr)
            surface.finish()