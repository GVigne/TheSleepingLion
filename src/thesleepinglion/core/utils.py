import gi
gi.require_version('PangoCairo', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import PangoCairo, Gtk

from cairosvg.surface import PDFSurface
from cairosvg.parser import Tree
from cairosvg.helpers import node_format

import cairo as cairo
from enum import Enum, auto
from pathlib import Path
from pkg_resources import resource_filename
from .errors import ImageNotFound, BracketError, AoeFileNotFound
from ..gloomhaven.gmllinecontext import GMLLineContext

class Haven(Enum):
    """
    Use this enum when you want to make the difference between a Gloomhaven-specific behavior, a Frosthaven-specific
    behavior, or something which behaves the same for both syntaxes.
    """
    GLOOMHAVEN = auto()
    FROSTHAVEN = auto()
    COMMON = auto()

def get_asset(filename, haven_type: Haven):
    """
    Get the path to an asset (here, PNG or SVG file) in the assets/haven_type/ folder.
    """
    if haven_type == Haven.COMMON:
        return resource_filename("thesleepinglion.assets.common", filename)
    elif haven_type == Haven.GLOOMHAVEN:
        return resource_filename("thesleepinglion.assets.gloomhaven", filename)
    else:
        return resource_filename("thesleepinglion.assets.frosthaven", filename)

def get_aoe_asset(filename, haven_type: Haven):
    """
    Get the path to an asset (here, AOE file) in the assets/haven_type/aoe/ folder.
    """
    if haven_type == Haven.COMMON:
        return resource_filename("thesleepinglion.assets.common.aoe", filename)
    elif haven_type == Haven.GLOOMHAVEN:
        return resource_filename("thesleepinglion.assets.gloomhaven.aoe", filename)
    else:
        return resource_filename("thesleepinglion.assets.frosthaven.aoe", filename)

def get_background_asset(filename, haven_type: Haven):
    """
    Get the path to an asset (here, PNG or SVG file) in the background_assets/haven_type folder.
    There are no common background asset, so don't call this function with haven_type = Haven.COMMON
    """
    if haven_type == Haven.GLOOMHAVEN:
        return resource_filename("thesleepinglion.background_assets.gloomhaven", filename)
    elif haven_type == Haven.FROSTHAVEN:
        return resource_filename("thesleepinglion.background_assets.frosthaven", filename)

def get_gui_asset(filename):
    """
    Get the path to an asset (here, .glade file) in the from the gui/ folder.
    """
    return resource_filename("thesleepinglion.gui", filename)

def get_gui_images(filename):
    """
    Get the path to an asset (here, PNG file) in the gui/gui_images/ folder.
    """
    return resource_filename("thesleepinglion.gui.gui_images", filename)

def get_doc_asset(filename):
    """
    Get the path to an asset (here, PDF or GML file) in the docs/ folder.
    """
    return resource_filename("thesleepinglion.docs", filename)

def get_image(gml_path : Path|None, filepath : str|None, haven_type: Haven):
    """
    Given a path to a file, try to interpret it as:
        - a relative path (from the path to the GML file) to a user-specific image
        - if the above fails, the name of an image in the assets/haven_type folder
        - if the above fails, the name of an image in the assets/common folder
    If everything fails, throw an ImageNotFound error.
    """
    if filepath is None:
        # Can't find an image if there is nothing to find.
        raise ImageNotFound

    # Check if the image is a custom image
    if gml_path is not None:
        user_image = gml_path.parent / filepath
        if user_image.is_file():
            return str(user_image)
    # Check if the image if in the haven_type/folder
    asset_path = get_asset(filepath, haven_type)
    if Path(asset_path).is_file():
        return asset_path
    # Check if the image if in the common/folder
    asset_path = get_asset(filepath, Haven.COMMON)
    if Path(asset_path).is_file():
        return asset_path

    raise ImageNotFound(f"No image was found with the path {filepath}")

def get_aoe(gml_path : Path|None, filepath : str|None, haven_type: Haven):
    """
    Behaves just like get_image, only with aoe files.
    """
    if filepath is None:
        # Can't find an AOE if there is nothing to find.
        raise AoeFileNotFound

    # Check if the image is a custom image
    if gml_path is not None:
        user_image = gml_path.parent / filepath
        if user_image.is_file():
            return str(user_image)
    # Check if the image if in the haven_type/folder
    asset_path = get_aoe_asset(filepath, haven_type)
    if Path(asset_path).is_file():
        return asset_path
    # Check if the image if in the common/folder
    asset_path = get_aoe_asset(filepath, Haven.COMMON)
    if Path(asset_path).is_file():
        return asset_path

    raise AoeFileNotFound(f"No AoE was found with the path {filepath}")

def text_to_pango(text : str, gml_context: GMLLineContext):
    """
    Return a pango layout corresponding to the given text.
    """
    # Create a dummy context, required to create the pango item.
    dummy_context = cairo.Context(cairo.PDFSurface(None, -1, -1))
    layout = PangoCairo.create_layout(dummy_context)

    markup = '<span '
    if gml_context.bold:
        markup += 'weight = "bold"'
    markup += 'font ="'+ gml_context.font + " " + str(gml_context.font_size) + '">' + text + '</span>'
    layout.set_markup(markup)

    # Note: the following is REQUIRED for Windows 11. Seems to work on Windows 10 and Linux (probably
    # means there is no scaling for those distributions), but we'll get weird results without this. Cairo
    # probably has some sort of additional scaling on Windows 11.
    # By default, the resolution is set at -1: this minus one probably has different meaning for Windows 10 and 11.
    PangoCairo.context_set_resolution(layout.get_context(), 96)
    return layout

def find_opened_bracket(text : str):
        """
        Given a string, return an int i such that text[i] = "{".
        If no curly bracket was found, or if the first word ended prematurely, return an int i marking the end
        of the first word (ie text[i] is a whitespace and text[:i] is the first word in text)
        """
        for i,v in enumerate(text):
            if v == "{":
                return i
            elif v == " ": # End of the first word -> act as if no curly bracket was found.
                break
        # No bracket found
        first_word = text.split(" ")[0]
        return len(first_word)

def find_end_bracket(text : str):
    """
    Given a text starting with an opened bracket, find the associated closed bracket, skipping any brackets in between. Return the index such that text[i] = "}".
    Ex: {Move 3} Attack 2-> 6
        {Move \image{move.jpg} 6} Attack -> 23
        {Move \image{move.jpg 6} -> Error
    Raise BracketError exception if there is a mismatch in brackets.
    """
    #Done naively. If this is an issue, use the find_...._bracket functions.
    i = 0
    depth_level = 0
    while i < len(text):
        if text[i] == "}":
            depth_level -=1
        elif text[i] == "{":
            depth_level +=1
        if depth_level ==0:
            break
        i +=1
    if depth_level ==0:
        return i + 1
    else:
        raise BracketError("The numbers of opening and closing brackets don't match.")

def find_end_macro(text : str):
    """
    Given a text starting with an "@", return the index such that text[:i] is the macro.
    Warning: a macro can have arguments or not, so this needs to be taken into account.
    TODO : currently, a whitespace is the end of macro. However, a macro is completely transparent, so this
    whitespace should also be taken into account.
    TODO: currently, the stop condition a whitespace. If a macro has spaces in one of its arguments,
    then this will fail.
    """
    i = 0
    while i < len(text) and text[i] !=" " and text[i] !="{":
        i +=1
    # Now we have the "base" part of the macro. We only need to check if it has arguments or not
    if i < len(text) and text[i] == "{":
        while i < len(text) and text[i] == "{":
            # Careful: the result from find_end_bracket is relative to text[i:], not text.
            i += find_end_bracket(text[i:])
    return i

def show_parsing_errors(errors: dict[str|None, str|list]):
    """
    Return a text displaying the errors pretily.
    errors is a dictionnary with keys being the card names and values being the error message.
    errors may also contains the key None which corresponds to errors at a global Gloomhaven class scale:
    in this case, only the errors for the Gloomhaven class will be displayed. This is because they can be quite
    harmful, and that some card errors may simply come from a higher level error (example: wrong alias definition)
    """
    pretty_text = ""
    # Gloomhaven class errors
    if None in errors:
        pretty_text += "The following errors have occurred when parsing the class:\n"
        for err_msg in errors[None]:
            pretty_text = pretty_text + err_msg + "\n"
        pretty_text += "Please correct them before editing cards."
        return pretty_text

    # Card-specific errors
    for i, (card_name, err_msg) in enumerate(errors.items()):
        if card_name is not None:
            pretty_text += f"An error has occurred when parsing the card {card_name}:\n"
            pretty_text = pretty_text + err_msg + "\n"
    # Crude way to remove the last \n. We could do that by getting errors's values and using "\n".join().
    pretty_text = pretty_text[0:-1]
    return pretty_text

def show_warning_errors(warnings: dict[list]):
    """
    Return a text displaying warnings prettily.
    warnings is a dictionnary with keys being the card names and values being a list of warning. It can also contain
    the key None, which corresponds to warnings at a global Gloomhaven class scale.
    """
    pretty_text = ""
    if None in warnings:
        pretty_text += "Warning! The Gloomhaven class has the following anomalies:\n"
        for warning in warnings[None]:
            pretty_text += warning + "\n"
    for i, (card_name, warning_list) in enumerate(warnings.items()):
        if card_name is not None:
            pretty_text += f"Warning! The card {card_name} has the following anomalies:\n"
            for warning in warning_list:
                pretty_text = pretty_text + warning + "\n"
    # Crude way to remove the last \n.
    pretty_text = pretty_text[0:-1]
    return pretty_text

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

def list_join(input: list, pattern):
    """
    Equivalent of join but for a list: places pattern inbetween every element of the input list.
    """
    res = []
    for i, elem in enumerate(input):
        res.append(elem)
        if i != (len(input)-1):
            res.append(pattern)
    return res

def alias_text_to_alias_list(raw_aliases: str):
    """
    Conversion from raw alias text to a splitted list of aliases.
    For convenience, every conversion from the GML text to a lexer-friendly format should be made through here.
    """
    aliases = raw_aliases.strip().split("\n")
    return [alias for alias in aliases if alias] # Remove empty lines

def check_aliases_integrity(raw_aliases: str):
    """
    Check if the aliases described in the given raw text are well-defined of nor. Return a list of error messages
    describing the errors for every alias.
    This check is not precise at all for now, it's just here to prevent a few bugs.
    """
    aliases = alias_text_to_alias_list(raw_aliases)

    errors = []
    for alias in aliases:
        if "=" not in alias:
            errors.append(f"The definition of the following alias is incorrect as it does not contain an equal sign: {alias}")
    return errors

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
    Sort the given list CardTabs object according to the ID of the underlying card. A sorted copy is returned,
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
    Sort the given list CardTabs object according to the initiative of the underlying card. A sorted copy is returned,
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
    Sort the given list CardTabs object according to the ID of the underlying card. A sorted copy is returned,
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