import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

def freeze_event(widget, called_function):
    """
    Freeze and unfreeze allow to temporarily disable an event (simply by disconnecting/reconnecting it). If a
    signal has been frozen, it should manually be unfrozen, else all callbacks won't take place.
    These functions work because widget and called_function are pointers to the associated objects and not their values.
    """
    widget.disconnect_by_func(called_function)

def unfreeze_event(widget, event_name: str, called_function):
    """
    See freeze_event's documentation.
    """
    widget.connect(event_name, called_function)

def gtk_error_message(message_text: str):
    """
    Display a model error message with just the button "Ok".
    """
    dlg = Gtk.MessageDialog(message_type  = Gtk.MessageType.ERROR,
                            buttons = Gtk.ButtonsType.OK)
    dlg.set_markup(message_text)
    dlg.set_modal(True)
    dlg.run()
    dlg.destroy()

def order_card_tabs_by_level(all_tabs: list):
    """
    Sort the given list of CardTabs object according to the ID of the underlying card. A sorted copy is returned,
    the original list is not modifed. Cards will be ordered as such:
    - first cards with a level which is a string other than X, lexicographically ordered
    - level 1 cards
    - level X cards
    - level 2 - 9 cards
    """
    lvl_1 = []
    lvl_X = []
    level_2_9 = []
    others = []
    for tab in all_tabs:
        if tab.card.level == "1":
            lvl_1.append([tab, tab.card.level])
        elif tab.card.level == "X":
            lvl_X.append([tab, tab.card.level])
        else:
            try:
                level_2_9.append([tab,int(tab.card.level)])
            except:
                others.append([tab, tab.card.level])
    level_2_9.sort(key=lambda x:x[1])
    others.sort(key=lambda x:x[1])
    return [x[0] for x in others+lvl_1+lvl_X+level_2_9]

def order_card_tabs_by_initiative(all_tabs: list):
    """
    Sort the given list of CardTabs object according to the initiative of the underlying card. A sorted copy is returned,
    the original list is not modifed.
    - first sort all cards with an iniative which is not an int (lexicographic order)
    - then sort all cards from smallest to highest iniative
    """
    str_init = []
    int_init = []
    for tab in all_tabs:
        try:
            int_init.append([tab,int(tab.card.initiative)])
        except:
            str_init.append([tab, tab.card.initiative])

    int_init.sort(key=lambda x:x[1])
    str_init.sort(key=lambda x:x[1])
    return [x[0] for x in str_init+int_init]

def order_card_tabs_by_id(all_tabs: list):
    """
    Sort the given list of CardTabs object according to the ID of the underlying card. A sorted copy is returned,
    the original list is not modifed.
    - first sort all cards with an ID which is an int
    - then sort all cards using string ordering
    """
    int_ids = []
    str_ids = []
    for tab in all_tabs:
        try:
            int_ids.append([tab,int(tab.card.card_ID)])
        except:
            str_ids.append([tab, tab.card.card_ID])

    int_ids.sort(key=lambda x:x[1])
    str_ids.sort(key=lambda x:x[1])
    return [x[0] for x in int_ids+str_ids]