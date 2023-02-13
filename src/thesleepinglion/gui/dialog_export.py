import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
import cairo
from pathlib import Path
from math import pi

from ..gloomhavenclass import GloomhavenClass
from ..utils import get_gui_asset
from ..constants import card_height, card_width


class ExportDialog(GObject.Object):
    def __init__(self, gloomhavenclass: GloomhavenClass):
        GObject.GObject.__init__(self)
        builder = Gtk.Builder()
        builder.add_from_file(get_gui_asset("dialog_export.glade"))
        self.dialog = builder.get_object("dialog")
        self.card_box = builder.get_object("card_box")
        self.card_per_page = builder.get_object("card_per_page")
        builder.connect_signals(self)

        self.gloomhavenclass = gloomhavenclass
        for card in self.gloomhavenclass.cards:
            check_button = Gtk.CheckButton(card.name)
            check_button.set_active(True)
            self.card_box.add(check_button)

        self.dialog.show_all()

    def accept(self, event, id):
        if id == -3:
            # The export button was clicked

            # Ask for the path to a file
            dlg = Gtk.FileChooserDialog(title = "Save as", parent = None,
                                        action = Gtk.FileChooserAction.SAVE)
            default_name = "Untitled"
            if len(self.gloomhavenclass.name) > 0:
                default_name = self.gloomhavenclass.name
            dlg.set_current_name(f"{default_name}.pdf")

            dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                        Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
            dlg.set_modal(True)
            dlg.set_do_overwrite_confirmation(True)
            response = dlg.run()
            if response == Gtk.ResponseType.OK:
                self.save_pdf(dlg.get_filename(), self.card_per_page.get_active())
                dlg.destroy()
            else:
                # Don't close the main window
                dlg.destroy()
                return

        self.dialog.destroy()

    def save_pdf(self, export_path: str, one_card_per_page: bool):
        """
        Save the selected cards to pdf format.
        """
        active = []
        for checkbutton in self.card_box.get_children():
            if checkbutton.get_active():
                active.append(checkbutton.get_label())
        to_draw  = [card for card in self.gloomhavenclass.cards if card.name in active]

        if one_card_per_page:
            save_path = Path(export_path).with_suffix(".pdf")
            surface = cairo.PDFSurface(save_path, card_width, card_height)
            cr = cairo.Context(surface)
            for card in to_draw:
                cr.save()
                self.gloomhavenclass.draw_card(card, cr)
                cr.restore()
                surface.show_page() # Save the page, so that each card is drawn on a separate page.
            surface.finish()
        else:
            # Fit 8 cards on an A4 sheet (ie like when printing)
            surface = cairo.PDFSurface(export_path, 595, 842) # A4 is 21/29.7 cm and cairo gives a DPI of 72 pt.
            cr = cairo.Context(surface)

            # 252.28 = 89mm with a DPI of 72 pt
            # Then, multiply by 8.5*7.5 as TSL's cards have a bigger border than standard Gloomhaven cards.
            # This factors makes it so the rune border has the correct size.
            cr.scale(8.5/7.5 * 252.28/card_height, 8.5/7.5 * 252.28/card_height)
            cr.rotate(-pi/2)
            pos = 0
            for card in to_draw:
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
