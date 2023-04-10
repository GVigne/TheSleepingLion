import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk
from pathlib import Path
import yaml as yaml

from .abstract_tab import AbstractTab
from ..card import Card
from ..gloomhavenclass import GloomhavenClass
from ..errors import CardNameAlreadyExists
from ..backupFileHandler import BackupFileHandler

def get_text_from_view(view: Gtk.TextView):
    """
    Return the full raw text in a given TextView.
    """
    buffer = view.get_buffer()
    start = buffer.get_start_iter()
    end = buffer.get_end_iter()
    return buffer.get_text(start, end, False)

class CardTab(AbstractTab):

    def __init__(self, path_to_glade, card: Card):
        self.card = card # Pointer towards a card from a GloomhavenClass

        builder = Gtk.Builder()
        builder.add_from_file(path_to_glade)
        AbstractTab.__init__(self, builder, self.card.name)

        self.card_name = builder.get_object("card_name")
        self.level = builder.get_object("level")
        self.initiative = builder.get_object("initiative")
        self.card_ID = builder.get_object("card_ID")
        self.top_action = builder.get_object("top_action")
        self.bottom_action = builder.get_object("bottom_action")

        self.load_custom_character()

    def update_custom_character(self, custom_character: GloomhavenClass, backup: BackupFileHandler):
        """
        Modify the given self.card based on the information contained in this tab. Return True is a field was indeed
        modified and False if nothing is changed (this tab and associated card are synchronized).
        After the modification has been made, may raise a CardNameAlreadyExists exception.
        """
        was_modified = False
        if self.card.level != self.level.get_text().strip():
            self.card.level = self.level.get_text().strip()
            was_modified = True
        if self.card.initiative != self.initiative.get_text().strip():
            self.card.initiative = self.initiative.get_text().strip()
            was_modified = True
        if self.card.card_ID != self.card_ID.get_text().strip():
            self.card.card_ID = self.card_ID.get_text().strip()
            was_modified = True

        top_modified = self.card.replace_text(get_text_from_view(self.top_action), True)
        bot_modified = self.card.replace_text(get_text_from_view(self.bottom_action), False)
        was_modified = was_modified or top_modified or bot_modified

        ui_name = self.card_name.get_text()
        valid_name = custom_character.valid_rename(ui_name, self.card)
        if ui_name != self.card.name: # User requested that some change be made for this card's name.
            self.card.name = valid_name
            was_modified = True
            # valid_name is the reference. Display it.
            self.card_name.set_text(valid_name)
            self.tab_name_label.set_text(valid_name)
            if valid_name != ui_name:
                # Something went wrong and name isn't valid. Instead, the gloomhaven class gave a valid one.
                raise CardNameAlreadyExists(f"{ui_name} is not a valid name: perhaps it is already the name of an existing card. A card was renamed into {valid_name} instead.")
        return was_modified


    def load_custom_character(self, backup: BackupFileHandler = None):
        """
        Modify the tab to show information from self.card.
        """
        self.card_name.set_text(self.card.name)
        self.tab_name_label.set_text(self.card.name)
        self.level.set_text(self.card.level)
        self.initiative.set_text(self.card.initiative)
        self.card_ID.set_text(self.card.card_ID)
        self.top_action.get_buffer().set_text(self.card.top_text)
        self.bottom_action.get_buffer().set_text(self.card.bot_text)

    def delete(self, custom_character: GloomhavenClass):
        """
        Delete the card.
        """
        custom_character.delete_card(self.card)
