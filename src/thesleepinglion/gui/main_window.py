import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
import os
from gi.repository import Gtk, Gdk, GObject, GdkPixbuf, PangoCairo

from .character_tab import CharacterTab
from .card_tab import CardTab
from .dialog_exportPDF import ExportDialogPDF
from .dialog_exportPNG import ExportDialogPNG
from .aoe_creator import AoECreator
from ..utils import get_gui_asset, get_doc_asset, show_parsing_errors, show_warning_errors, freeze_event, unfreeze_event, \
                    gtk_error_message, get_gui_images, order_card_tabs_by_id, order_card_tabs_by_level, order_card_tabs_by_initiative
from ..constants import card_height, card_width
from ..gloomhavenclass import GloomhavenClass
from ..backupFileHandler import GMLFileHandler, AoEFileHandler
from ..errors import InvalidGMLFile, CardNameAlreadyExists

class MainWindow(GObject.Object):
    @GObject.Signal
    def custom_character_changed(self):
        pass

    def __init__(self, custom_character: GloomhavenClass, backup_handler: GMLFileHandler, version):
        """
        The Sleeping Lion's main window.
        """
        GObject.GObject.__init__(self)
        # Entries shouldn't highlight the text when they are being focused on, and instead the cursor should be place somewhere
        Gtk.Settings.get_default().set_property("gtk-entry-select-on-focus", False)

        self.current_class = custom_character
        self.backup_handler = backup_handler
        self.card_tabs = []
        self.character_tab = None
        self.zoom_factor = 1

        # A pointer to a temporary directory so that it doesn't go out of scope and gets deleted prematurely.
        # This can and should be safely ignored.
        self.new_file_tmpdir = None

        builder = Gtk.Builder()
        builder.add_from_file(get_gui_asset("main_window.glade"))
        builder.add_from_file(get_gui_asset("about_window.glade"))
        builder.connect_signals(self)

        self.window = builder.get_object("window")
        self.about_dialog = builder.get_object("about_dialog")
        self.error_display = builder.get_object("error_display")
        self.drawing_area = builder.get_object("drawing_area")

        self.window.set_icon(GdkPixbuf.Pixbuf.new_from_file_at_scale(get_gui_images("cropped_icon.png"), -1, -1, True))
        self.about_dialog.set_logo(GdkPixbuf.Pixbuf.new_from_file_at_scale(get_gui_images("full_icon.png"), 700, -1, True))
        self.about_dialog.set_version(f"Version {version}")
        self.window.maximize()

        self.notebook = builder.get_object("notebook")
        self.loading_routine()

        self.sort_cards_combobox = builder.get_object("sort_cards_combobox")
        self.change_tab_sorting_method(None)

        self.connect("custom_character_changed", self.backup_handler.automatic_save)
        self.backup_handler.connect("change_window_title", self.change_window_title)

    def refresh(self, signal):
        """
        Update the current class, if it was modified parse it and draw it.
        """
        needs_parsing, errors = self.update_current_class()

        # Clear error message box if something is going to change
        if len(errors) > 0 or needs_parsing:
            self.error_display.get_buffer().set_text("")
        if len(errors) > 0:
            self.error_display.get_buffer().set_text(errors)

        # Parse and redraw the current class
        if needs_parsing:
            self.parse_current_class()
        self.drawing_area.queue_draw()

    def loading_routine(self):
        """
        Load the current class, parse it, and if the parsing went fine, draw it.
        """
        self.error_display.get_buffer().set_text("")
        self.change_window_title(None) # Force a change in the main window's title.
        self.load_current_class()
        self.parse_current_class()
        self.drawing_area.queue_draw()

    def load_current_class(self):
        """
        Load self.current_class into different tabs. Also delete any existing tabs.
        """
        self.clear()

        self.character_tab = CharacterTab(get_gui_asset("character_tab.glade"))
        self.character_tab.load_custom_character(self.current_class, self.backup_handler)
        # We connect the signal AFTER loading the custom character to avoir rgba_changed being called when
        # loading the character. This would force a parsing.
        self.character_tab.connect("rgba_changed", self.refresh)
        self.character_tab.connect("path_to_icon_changed", self.refresh)

        self.card_tabs = []
        for card in self.current_class.cards:
            new_tab = CardTab(get_gui_asset("card_tab.glade"), card)
            self.card_tabs.append(new_tab)

        if len(self.card_tabs) == 0:
            # Always have at least one tab, even if it is empty.
            card = self.current_class.create_blank_card()
            new_tab = CardTab(get_gui_asset("card_tab.glade"), card)
            self.card_tabs.append(new_tab)

        freeze_event(self.notebook, self.switched_page)
        self.notebook.append_page(self.character_tab.tab_widget, self.character_tab.tab_name_label)
        for card_tab in self.card_tabs:
            self.notebook.append_page(card_tab.tab_widget, card_tab.tab_name_label)
            self.notebook.set_tab_reorderable(card_tab.tab_widget, True)
        self.notebook.set_current_page(0) # By default, focus on the character tab
        unfreeze_event(self.notebook, "switch-page", self.switched_page)

    def update_current_class(self):
        """
        Update and save the current class.
        Return True if the class has been modified and a parsing is required. Doing so allows some signal which
        are automatically emitted not to force the whole parsing and drawing procedure if nothing changed. For example,
        when setting the color in a ColorChooserWidget, the signal "notify" is emitted, then caught by the main window
        and calls refresh. However, nothing really changed in the class, so it shouldn't be redrawn.
        Also returns errors as a string: this string is empty if no error occurred.
        """
        current_tab = self.get_pointer_to_current_tab()
        # Now current_tab is either a CardTab or the CharacterTab
        errors = ""
        was_modified = True # By default, assume something has changed.
        try:
            was_modified = current_tab.update_custom_character(self.current_class, self.backup_handler)
        except CardNameAlreadyExists as e:
            errors = str(e)

        if was_modified:
            self.emit("custom_character_changed") # Notify the backup file handler that the custom classed has been modified.
        return was_modified, errors

    def parse_current_class(self):
        """
        Parse the GML file, and display all errors.
        """
        parsing_errors, parsing_warnings = self.current_class.parse_gml()
        if len(parsing_errors) != 0:
            # We insert rather then setting the text as this could overwrite previous error messages.
            # This should be fine, as parse_gml should only be called after update_current_clas and in refresh.
            self.error_display.get_buffer().insert_at_cursor("\n" + show_parsing_errors(parsing_errors), - 1)
        if len(parsing_warnings) !=0:
            self.error_display.get_buffer().insert_at_cursor("\n" + show_warning_errors(parsing_warnings), - 1)

    def draw(self, widget, cr):
        """
        Draw the custom class on the given cairo context.
        """
        focused_card = None
        current_tab = self.get_pointer_to_current_tab()
        if current_tab!= self.character_tab:
            focused_card = current_tab.card
        # If focused_card is None, then the current tab is the Character tab, and only the background should be displayed.

        # Zoom the cairo context according to the user's input.
        cr.scale(self.zoom_factor, self.zoom_factor)
        self.current_class.draw_card(focused_card, cr)

    def quit_window_clicked(self, button):
        self.window.close() # This will emit the window destroy signal which will get caught by self.window_destroy

    def window_destroy(self, window, event):
        save_as_message = "The current file isn't saved. Do you want to save it?"
        cancel_action = self.safe_to_close_class(save_as_message)
        if cancel_action: # Don't quit the app
            return True # Yes, the signal has been dealt with. No need to propagate it!

        self.backup_handler.close()
        Gtk.main_quit()

    def switched_page(self, notebook, page, page_num):
        self.refresh(None)

    def shortcut_switched_page(self, forward = True):
        """
        Method called when the users uses the shortcut allowing to swap betwen pages.
        If forward is false, go to the previous page
        """
        current_page_id = self.notebook.get_current_page()
        if forward:
            next_page_id = current_page_id + 1
        else:
            next_page_id = current_page_id - 1
        if next_page_id == self.notebook.get_n_pages():
            next_page_id = 0
        freeze_event(self.notebook, self.switched_page)
        self.notebook.set_current_page(next_page_id)
        unfreeze_event(self.notebook, "switch-page", self.switched_page)
        self.refresh(None) # Refresh the card preview

    def tab_reordered(self, notebook, page, page_num):
        """
        This function is called when the notebook's tabs are reordered.
        """
        if page_num == 0:
            # If the user tries to move a tab into the first spot, instead move it to the second one and make
            # sure the Character Tab remains the first tab in the notebook.
            # Warning: this will cause the page_reordered signal to be re-emitted, calling this function once again
            self.notebook.reorder_child(self.character_tab.tab_widget, 0)

    def key_pressed(self, window, event):
        # Simple keystrokes
        if event.keyval == Gdk.KEY_Return:
            self.refresh(None)

        # CONTROL + something
        if event.get_state() & Gdk.ModifierType.CONTROL_MASK:
            if event.keyval == Gdk.KEY_s:
                # Control + S was pressed
                self.save(None)
            elif event.keyval == Gdk.KEY_Tab:
                # Control + SHIFT + TAB was pressed
                current_tab = self.get_pointer_to_current_tab()
                current_tab.tab_move_focus()
                return True # We return True so the signal is not propagated: this makes sure that nothing else happens

        # CONTROL + SHIFT + something
        if event.get_state() & Gdk.ModifierType.CONTROL_MASK:
            if event.get_state() & Gdk.ModifierType.SHIFT_MASK:
                if event.keyval == Gdk.KEY_ISO_Left_Tab:
                    # Control + Tab. Apparently, it's not the same tab as when pressing Ctrl + Tab: identifiers are differnt
                    # This is a bit weird: it's probably not how we should be catching this signal.
                    current_tab = self.get_pointer_to_current_tab()
                    current_tab.tab_move_focus(False)
                    return True # Same as above: return True to make sure this function overrides the default behavior

        # ALT + something
        if event.get_state() & Gdk.ModifierType.MOD1_MASK:
            if event.keyval == Gdk.KEY_Right:
                # Right arrow
                self.shortcut_switched_page()
            elif event.keyval == Gdk.KEY_Left:
                # Left arrow
                self.shortcut_switched_page(False)

    def scroll_event(self, window, event):
        if event.get_state() & Gdk.ModifierType.CONTROL_MASK:
            if event.direction == Gdk.ScrollDirection.UP:
                # Ctrl + mousewheel up
                if self.zoom_factor < 2:
                    self.zoom_factor += 0.1
                # Resize the drawing area so that scrollbars appear
                self.drawing_area.set_size_request(card_width*self.zoom_factor, card_height*self.zoom_factor)
            elif event.direction == Gdk.ScrollDirection.DOWN:
                # Ctrl + mousewheel down
                if self.zoom_factor > 0.5:
                    self.zoom_factor -= 0.1
                # Resize the drawing area so that scrollbars appear
                self.drawing_area.set_size_request(card_width*self.zoom_factor, card_height*self.zoom_factor)

    def add_tab(self, button):
        """
        Add a new tab (= create a new card).
        """
        card = self.current_class.create_blank_card()
        new_tab = CardTab(get_gui_asset("card_tab.glade"), card)
        self.card_tabs.append(new_tab)

        freeze_event(self.notebook, self.switched_page)
        self.notebook.append_page(new_tab.tab_widget, new_tab.tab_name_label)
        self.notebook.set_tab_reorderable(new_tab.tab_widget, True)
        self.notebook.set_current_page(-1) # Focus on the newly created card
        unfreeze_event(self.notebook, "switch-page", self.switched_page)

        self.parse_current_class()
        self.drawing_area.queue_draw()

    def delete_tab(self, button):
        # Fetch the current tab

        current_card_tab = self.get_pointer_to_current_tab()
        if current_card_tab != self.character_tab:
            # Check if it's not "Class attributes". This should be removed, and the button enabled only if not on class attributes
            dlg = Gtk.MessageDialog()
            dlg.add_buttons(Gtk.STOCK_YES, Gtk.ResponseType.YES,
                        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
            dlg.set_markup(f"Are you sure you want to delete the card {current_card_tab.card.name}? This cannot be undone.")
            dlg.set_modal(True)
            response = dlg.run()
            if response == Gtk.ResponseType.YES:
                current_card_tab.delete(self.current_class)
                self.notebook.remove_page(self.notebook.get_current_page())
                self.card_tabs = [ct for ct in self.card_tabs if ct != current_card_tab]
                self.emit("custom_character_changed") # Notify the backup file handler that the custom classed has been modified.
                # Redraw
                self.drawing_area.queue_draw()
            dlg.destroy()

    def change_tab_sorting_method(self, combobox):
        current_tab = self.get_pointer_to_current_tab()
        sorting_method = self.sort_cards_combobox.get_active()

        if sorting_method == 0: # Level
            self.card_tabs = order_card_tabs_by_level(self.card_tabs)
        elif sorting_method == 1: # Initiative
            self.card_tabs = order_card_tabs_by_initiative(self.card_tabs)
        else: # ID
            self.card_tabs = order_card_tabs_by_id(self.card_tabs)

        freeze_event(self.notebook, self.switched_page)
        # First, remove all tabs
        for _ in range(self.notebook.get_n_pages()):
            self.notebook.remove_page(-1)
        # Put them back in the new order
        self.notebook.append_page(self.character_tab.tab_widget, self.character_tab.tab_name_label)
        for card_tab in self.card_tabs:
            self.notebook.append_page(card_tab.tab_widget, card_tab.tab_name_label)
            self.notebook.set_tab_reorderable(card_tab.tab_widget, True)
        # Focus on the tab previously being focused (so the user doesn't see any change)
        for page_id in range(len(self.card_tabs)):
            if  self.notebook.get_nth_page(page_id)== current_tab.tab_widget:
                self.notebook.set_current_page(page_id)
                break
        unfreeze_event(self.notebook, "switch-page", self.switched_page)
        self.refresh(None)

    def save(self, widget):
        """
        For code simplicity, this function should be called whenever the user wants to save the current class.
        Returns a boolean which is True if the user canceled his action. This can only happend when clicking
        "Save as" then "Cancel". If the user followed the save action until the end, return False.
        Most of the time, save's return value should just be ignored. Only use it in the specific case you want to know
        if the user tried to save an unnamed file, then canceled his action.
        """
        if self.backup_handler.no_save_path():
            # Ask the user where he wants to save his file as it is currently a temporary file.
            canceled = self.save_as(None)
            return canceled
        else:
            self.backup_handler.save(self.current_class)
            return False

    def save_as(self, widget):
        """
        Show a popup so the user may choose where to save his file.
        Return a boolean which is True is the user canceled his "Save as" action, and False otherwise.
        Like the save function, save_as's return value should be ignored most of the time.
        """
        dlg = Gtk.FileChooserDialog(title = "Save as", parent = None,
                                           action = Gtk.FileChooserAction.SAVE)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                    Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        dlg.set_modal(True)
        dlg.set_do_overwrite_confirmation(True)
        default_name = "Untitled"
        if len(self.current_class.name) > 0:
            default_name = self.current_class.name
        dlg.set_current_name(f"{default_name}.gml")

        response = dlg.run()
        canceled = True
        if response == Gtk.ResponseType.OK:
            self.backup_handler.new_path(dlg.get_filename())
            self.save(None)
            canceled = False
        dlg.destroy()
        return canceled

    def export_as_pdf(self, button):
        self.refresh(None) # Make sure everything is up to date.
        dialog = ExportDialogPDF(self.current_class)

    def export_as_png(self, button):
        self.refresh(None) # Make sure everything is up to date.
        dialog = ExportDialogPNG(self.current_class)

    def new_file(self, widget):
        """
        Create a blank new gml file in a temporary directory.
        """
        save_as_message = "The current file isn't saved. Do you want to save it before creating a new file?"
        cancel_action = self.safe_to_close_class(save_as_message)
        if cancel_action:
            # At some point, the user said he wanted to abort the "New file" action. Abort everything.
            return

        self.new_file_tmpdir = TemporaryDirectory()
        tmpfile = Path(self.new_file_tmpdir.name) / "Untitled.gml"# A temporary file which will be deleted when the user quits TSL
        tmpfile.with_suffix(".gml").touch() # Create the temporary file.
        self.current_class = self.backup_handler.open_new_file(tmpfile, in_temporary_dir=True)
        self.loading_routine()

    def open(self, widget):
        """
        Close the current class and open a new one.
        """
        save_as_message = "The current file isn't saved. Do you want to save it before opening a new file?"
        cancel_action = self.safe_to_close_class(save_as_message)
        if cancel_action:
            # At some point, the user said he wanted to cancel the action. Abort everything.
            return

        # Now open a dialog so the user may select a file.
        dlg = Gtk.FileChooserDialog(title = "Open", parent = None,
                                           action = Gtk.FileChooserAction.OPEN)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                    Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        filter = Gtk.FileFilter()
        filter.add_pattern("*.gml")
        dlg.set_filter(filter)
        dlg.set_modal(True)
        response = dlg.run()
        if response == Gtk.ResponseType.OK:
            if self.backup_handler.available_backup(dlg.get_filename()):
                # Ask if a backup should be loaded
                backup_dlg = Gtk.MessageDialog()
                backup_dlg.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.NO,
                            Gtk.STOCK_YES, Gtk.ResponseType.YES)
                backup_dlg.set_markup("Something seems to have gone wrong the last you closed this GML file. Do you want to load a backup?")
                backup_dlg.set_modal(True)
                response = backup_dlg.run()
                if response == Gtk.ResponseType.YES:
                    # Load the backup
                    try:
                        self.current_class = self.backup_handler.open_new_file(dlg.get_filename(), load_backup=True)
                        self.loading_routine()
                    except InvalidGMLFile:
                        gtk_error_message(f"The backup for the file {dlg.get_filename()} couldn't be read. Try loading the file directly.")
                else:
                    # This is simply the normal way to open a file. This also means that the backup file will be destroyed;
                    # the user has been warned and chose not to load it, we will assume it is irrelevant
                    try:
                        self.current_class = self.backup_handler.open_new_file(dlg.get_filename())
                        self.loading_routine()
                    except InvalidGMLFile:
                        gtk_error_message(f"The file {dlg.get_filename()} couldn't be read. Make sure it is a .gml file and try again.")
                backup_dlg.destroy()
            else:
                # This is the normal case: load the given file.
                try:
                    self.current_class = self.backup_handler.open_new_file(dlg.get_filename())
                    self.loading_routine()
                except InvalidGMLFile:
                    gtk_error_message(f"The file {dlg.get_filename()} couldn't be read. Make sure it is a .gml file and try again.")
        dlg.destroy()

    def clear(self):
        """
        Reset the mainwindow to its initial state. This more or less comes to building a new instance of MainWindow.
        """
        self.card_tabs = []
        # Since we will then be deleting the character tab, the signal "rgba_changed" should get automatically disconnected.
        # This is just to make sure there really is nothing left of the old character tab.
        if self.character_tab is not None:
            self.character_tab.disconnect_by_func(self.refresh)
        self.character_tab = None

        freeze_event(self.notebook, self.switched_page)
        for _ in range(self.notebook.get_n_pages()):
            self.notebook.remove_page(-1)
        unfreeze_event(self.notebook, "switch-page", self.switched_page)
        # At this point, the notebook is empty.

    def change_window_title(self, filehandler):
        """
        Automatically called by the backup file handler. This is a notification that the window should have
        its title changed.
        """
        self.window.set_title(self.backup_handler.get_window_title())

    def open_about(self, button):
        """
        Show the "About" dialog.
        """
        self.about_dialog.run()
        self.about_dialog.hide()

    def spellweaver_cards(self, button):
        """
        Load the Spellweaver's cards (in the docs/ folder) as a read only file.
        """
        save_as_message = "The current file isn't saved. Do you want to save it before opening the Spellweaver's cards?"
        cancel_action = self.safe_to_close_class(save_as_message)
        if cancel_action:
            # At some point, the user said he wanted to cancel the action. Cancel everything.
            return

        # Open as read-only.
        self.current_class = self.backup_handler.open_new_file(get_doc_asset("Spellweaver.gml"), read_only=True)
        self.loading_routine()

    def demolitionist_cards(self, button):
        """
        Load the Demolitionist's cards (in the docs/ folder) as a read only file.
        """
        save_as_message = "The current file isn't saved. Do you want to save it before opening the Demolitionist's cards?"
        cancel_action = self.safe_to_close_class(save_as_message)
        if cancel_action:
            # At some point, the user said he wanted to cancel this action. Cancel everything.
            return

        self.current_class = self.backup_handler.open_new_file(get_doc_asset("Demolitionist.gml"), read_only=True)
        self.loading_routine()

    def safe_to_close_class(self, save_as_message: str):
        """
        Check if the class is safe to close. If it isn't the case, create a popup asking the user if he wishes to save or
        not the current class.
        Return a boolean: if it is True, the function calling this one MUST immediately stop (ie must immediately "return").
        This is because the users has pressed "Cancel", so the entire action must be canceled, not just the "save as" part.

        This mechanism is really starting to look like a state machine...
        """
        if not self.backup_handler.safe_to_close():
            dlg = Gtk.MessageDialog()
            dlg.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.NO,
                        Gtk.STOCK_YES, Gtk.ResponseType.YES,
                        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
            dlg.set_markup(save_as_message)
            dlg.set_modal(True)
            response = dlg.run()
            canceled = False
            if response == Gtk.ResponseType.CANCEL:
                canceled = True
            elif response == Gtk.ResponseType.YES:
                canceled = self.save(None)
            # If answer is NO, don't do anything. The backup handler knows how to handle this.

            dlg.destroy()

            # At some point, the user has pressed the cancel button (confirmation dialog or in the "Save as" popup").
            # The function calling this one should cancel everything.
            return canceled
        return False # Safe to close, calling function may procede.


    def open_aoe_editor(self, button):
        """
        Note: this looks a lot like TSL's main, when creating a new MainWindow...
        """
        dialog = AoECreator()
        dialog.window.set_modal(True)

    def show_tutorial(self, button):
        if sys.platform == "linux":
            subprocess.call(["xdg-open", get_doc_asset("tutorial.pdf")])
        else:
            os.startfile(get_doc_asset("tutorial.pdf"))

    def show_available_functions(self, button):
        if sys.platform == "linux":
            subprocess.call(["xdg-open", get_doc_asset("available_functions.pdf")])
        else:
            os.startfile(get_doc_asset("available_functions.pdf"))

    def show_user_manual(self, button):
        if sys.platform == "linux":
            subprocess.call(["xdg-open", get_doc_asset("user_manual.pdf")])
        else:
            os.startfile(get_doc_asset("user_manual.pdf"))

    def get_pointer_to_current_tab(self):
        """
        Returns a pointer to the card tab being currently focused on, either a card tab or the "Character tab".
        """
        tab_widget = self.notebook.get_nth_page(self.notebook.get_current_page())
        for tab in self.card_tabs:
            if tab.tab_widget == tab_widget:
                return tab
        return self.character_tab
