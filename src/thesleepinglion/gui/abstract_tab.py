import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class AbstractTab:
    def __init__(self, builder, tab_name):
        """
        Child classes should call set_iteration_order to allow CTRL + (SHIFT) + TAB to move the focus between
        different widgets
        """
        self.tab_widget = builder.get_object("grid")
        self.tab_name_label = Gtk.Label(label=tab_name)
        builder.connect_signals(self)

        self.iteration_order = []

    def set_tab_name(self, tab_name):
        self.tab_name_label.set_text(tab_name)

    def get_tab_name(self):
        return self.tab_name_label.get_text()

    def set_iteration_order(self, order: list):
        """
        Set the order in which the text widget should be iterated through with CTRL + (SHIFT) + TAB
        """
        self.iteration_order = order

    def tab_move_focus(self, forward = True):
        """
        Method called when CTRL+TAB is pressed. Go to the next entry in this tab.
        If forward is False, we instead iterate backwards through the tab.
        """
        if len(self.iteration_order) > 0:
            current_focused = None
            for i, widget in enumerate(self.iteration_order):
                if widget.has_focus():
                    current_focused = i
                    break
            if current_focused is None:
                # No widget is being focused on, so focus on the first one
                next_focus = 0
            else:
                if forward:
                    next_focus = current_focused + 1
                else:
                    next_focus = current_focused - 1
            if next_focus == len(self.iteration_order):
                # Loop back to the first widget
                next_focus = 0

            self.iteration_order[next_focus].grab_focus()
            if isinstance(self.iteration_order[next_focus], Gtk.Entry):
                self.iteration_order[next_focus].set_position(-1)
            else:
                buffer = self.iteration_order[next_focus].get_buffer()
                buffer.place_cursor(buffer.get_end_iter())