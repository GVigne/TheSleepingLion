import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from ..gloomhavenclass import GloomhavenClass
from ..utils import get_gui_asset

class SelectCardsForExportWidget:
    """
    A wrapper around a widget allowing to select one or multiple cards in checkboxes to export.
    """
    def __init__(self, gloomhavenclass: GloomhavenClass):
        self.gloomhavenclass = gloomhavenclass

        builder = Gtk.Builder()
        builder.add_from_file(get_gui_asset("select_cards_widget.glade"))
        builder.connect_signals(self)
        self.widget = builder.get_object("main_widget") # This is the item which should be inserted in a QBox.
        self.card_box = builder.get_object("card_box")
        self.select_all_cards = builder.get_object("select_all_cards")
        self.select_all_cards.connect("toggled", self.toggle_select_all_cards)

        # By default, select every card for export
        self.select_all_cards.set_active(True)
        for card in self.gloomhavenclass.cards:
            check_button = Gtk.CheckButton(card.name)
            check_button.set_active(True)
            check_button.connect("toggled", self.check_toggle_main_chbox)
            self.card_box.add(check_button)

    def check_toggle_main_chbox(self, button):
        """
        The button "Select/Unselect every card" should be
        - in checked state if at least one card is checked
        - unchecked if no card is checked.
        This callback makes sure that when the last card is unchecked, so is the "main" checkbox.
        """
        for checkbutton in self.card_box.get_children():
            if checkbutton.get_active():
                return
        self.select_all_cards.set_active(False)

    def toggle_select_all_cards(self, button):
        """
        According to the state of the "Select/Unselect every card" button:
        - if it is checked, select every card
        - if it is unchecked, unselect every card
        """
        is_active = self.select_all_cards.get_active()
        for checkbutton in self.card_box.get_children():
            checkbutton.set_active(is_active)

    def get_cards_to_save(self):
        """
        Return a list of Card items representing all the cards the user wishes to export.
        """
        active = []
        for checkbutton in self.card_box.get_children():
            if checkbutton.get_active():
                active.append(checkbutton.get_label())
        return [card for card in self.gloomhavenclass.cards if card.name in active]

    def has_cards_to_save(self):
        """
        Return True if at least one card is selected, False otherwise
        """
        for checkbutton in self.card_box.get_children():
            if checkbutton.get_active():
                return True
        return False
