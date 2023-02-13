from .constants import *

class GMLLineContext:
    """
    A class to hold the context in a given GML line. Simplifies interactions between macros, commands and
    parser.gml_line_to_items
    This context holds information about the size, color and font for the text, as well as if the text is in bold
    or not. It also holds a stack of all transformations made on this context, so they can be reverted ("undo").
    Macros may interact with the context, modifying these information. Commands should ask the context what the current
    color/size/font... is and act accordingly.
    Note: positional macros should not interact with the context
    """
    @staticmethod
    def CreateFromIndentation(is_small_context: bool):
        """
        Note: path_to_gml MUST be a Path object, not a string.
        """
        font_size = base_font_size
        if is_small_context:
            font_size = small_font_size
        return GMLLineContext(font_size = font_size, is_small_context=is_small_context)

    def __init__(self,
                font: int = card_font,
                font_size: int = base_font_size,
                text_color: dict = {"red": 255, "green": 255, "blue": 255}, # By default, text is in white
                bold: bool = False,
                is_small_context: bool = False):  # is_small_context should never be changed by a macro

        self.font = font
        self.font_size = font_size
        self.text_color = text_color
        self.bold = bold
        self.is_small_context = is_small_context
        if self.is_small_context:
            self.font_size = small_font_size

        self.context_history = [] # A stack of GMLLineContext, representing the previous states of the context.

    def new_context_effects(self,
                            font: int = None,
                            font_size: int = None,
                            text_color: dict = None,
                            bold: bool = None):
        last_context = GMLLineContext(self.font, self.font_size, self.text_color, self.bold, self.is_small_context)
        self.context_history.append(last_context)
        if font is not None:
            self.font = font
        if font_size is not None:
            self.font_size = font_size
        if text_color is not None:
            self.text_color = text_color
        if bold is not None:
            self.bold = bold

    def clear_last_effect(self):
        """
        Revert the context to its previous state (ie the top element of the stack self.context_history).
        Won't do anything if the context history is empty.
        """
        try:
            last_context = self.context_history.pop()
            self.font = last_context.font
            self.font_size = last_context.font_size
            self.text_color = last_context.text_color
            self.bold = last_context.bold
        except IndexError:
            pass

    def clear(self):
        """
        Revert the context to its inital state.
        """
        self.font = card_font
        self.text_color = {"red": 255, "green": 255, "blue": 255}
        self.bold = False

        size = base_font_size
        if self.is_small_context:
            size = small_font_size
        self.font_size = size

        self.context_history = []