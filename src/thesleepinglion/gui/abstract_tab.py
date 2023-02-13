import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class AbstractTab:
    def __init__(self, builder, tab_name):
        self.tab_widget = builder.get_object("grid")
        self.tab_name_label = Gtk.Label(label=tab_name)
        builder.connect_signals(self)

    def set_tab_name(self, tab_name):
        self.tab_name_label.set_text(tab_name)

    def get_tab_name(self):
        return self.tab_name_label.get_text()