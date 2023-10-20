from pathlib import Path
from gi.repository import Pango

from.abstractGMLlinecontext import AbstractGMLLineContext
from .utils import find_opened_bracket, find_end_bracket, text_to_pango
from .errors import CommandNotFound, MacroNotFound
from .items import TextItem
from .macros import AbstractPositionalMacros

class AbstractParser:
    """
    An abstract class to parse the results of the HavenLexer into AbstractItems.
    Child classes must overload at least the __init__, gml_line_to_items and parse methods.
    """
    def __init__(self, path_to_gml : Path):
        """
        Must be overloaded to populate self.command_tokens and self.macro_tokens
        """
        self.path_to_gml = path_to_gml
        self.command_tokens = {}
        self.macro_tokens = {}

    def parse(self,
              action : str,
              class_color: dict = {"red": 0, "green": 0, "blue": 0},
              additional_aliases: str = "",
              is_top_action: bool = False):
        """
        This method is the highest possible function, which should only be called by an AbstractCard. Parse returns
        a dictionnary with keys being positions and values being AbstractTopmostColumnItems which should be drawn. It also
        returns a list of warnings, ie non-breaking errors.
        This function must be overloaded.

        Implementation-wise, here is how this parser works.
        - Take a raw .gml top or bottom action.
        - Ask the lexer to split it into user-defined lines (lexer.separate_lines)
        - For each line, ask the lexer to split in into lexemes (lexer.input)
        - For each line, identify its position: top, bottom, center... by using AbstractPositionalMacros (self.find_line_position)
        - For each line, transform the lexemes in Items which can be drawn (self.gml_line_to_items).
        """
        pass

    def gml_line_to_items(self):
        """
        Converts a list of lexemes, representing a user-defined line into AbstractItems. Returns a list of
        LineItems, ie a list of objects which should be placed on the AbstractCard.
        This function is recursive, and can be called by each created item.
        This function ignores positional macros, they should be handled in AbstractParser.parse.
        This function must be overloaded, and child classes must define their own API for this method.
        """
        pass

    def find_line_position(self, line: list[str]):
        """
        Sorts the given line splitted into lexemes (ie on of the result of HavenLexer.separate_lines) according
        to its position (topleft, center, center2, bottomright). Only the first positional macro is taken,
        other positional macros are ignored.
        """
        for lexeme in line:
            if self.is_macro(lexeme):
                macro = self.create_macro(lexeme)
                if isinstance(macro, AbstractPositionalMacros):
                    new_position = macro.get_position()
                    if new_position != "center": # The default behavior
                        return new_position
        return "center"

    def is_command(self, text : str):
        """
        Returns true if the given text represents a command.
        """
        return text[0] == "\\"

    def is_macro(self, text : str):
        """
        Returns true if the given text represents a macro.
        """
        return text[0] == "@"

    def create_text(self,
                    text : str,
                    allowed_size : int,
                    gml_context: AbstractGMLLineContext,
                    minimum_one_word: bool = True):
        """
        Try to create a TextItem with the given size. If the text doesn't fit in the given space, fill up the
        space as much as possible, then return the part of the text which doesn't fit.
        If minimum_one_word is False, this function can return None instead of a TextItem if there wasn't enough
        space: this prevents placing a TextItem with an empty text on the card.
        If allowed_size = -1, ignore all size restrictions and put everything on a single line.
        """
        if allowed_size == -1:
            return TextItem([text], gml_context, path_to_gml = self.path_to_gml), ""
        # Try to fit as much text as possible in the give size.
        words = text.split(" ")
        a = len(words)
        b = len(words)
        while True:
            if a == 0: # Not enough space to put even a single word, stop the loop
                break
            pango_text = text_to_pango(" ".join(words[:a]), gml_context)
            pango_width = Pango.units_to_double(pango_text.get_size().width)
            if pango_width > allowed_size:
                b = a
                a = a//2
            else:
                if b-a <= 1:
                    break
                else:
                    a = a + (b - a) //2

        # The default behavior is to put at least one word per line to prevent infinite loop if a single word is too big to fit in a card
        # However, in some rare cases (for example when an image is at the end of a line), we can tolerate an empty word,
        # so that there is no overflow.
        if a == 0:
            if minimum_one_word:
                a = 1
            else:
                # There is no item to place, so return None. Note that " ".join(words[a:] should be equal to text.
                return None, " ".join(words[a:])

        item = TextItem([" ".join(words[:a])], gml_context, path_to_gml = self.path_to_gml)
        return item, " ".join(words[a:])  # Joining on a empty list returns an empty string.

    def create_command(self,
                        text : str,
                        gml_context: AbstractGMLLineContext):
        """
        Converts a string representing a command into the corresponding AbstractItem.
        """
        i = find_opened_bracket(text)
        try:
            command_item = self.command_tokens[text[:i]]
        except Exception:
            raise CommandNotFound(f"The command '{text[:i]}' isn't defined.")
        arguments = []
        while i < len(text) and text[i] == "{":
            # Careful: the result from find_end_bracket is relative to text[i:], not text.
            j = find_end_bracket(text[i:])
            arg = text[i+1:i+j -1] # Exclude both brackets
            arguments.append(arg)
            i +=j
        return command_item(arguments, gml_context, path_to_gml= self.path_to_gml)

    def create_macro(self, text : str):
        """
        Converts a string representing a macro into the corresponding AbstractMacro or AbstractPositionalMacro.
        """
        i = find_opened_bracket(text)
        try:
            macro_item = self.macro_tokens[text[:i]]
        except Exception:
            raise MacroNotFound(f"The macro '{text[:i]}' isn't defined.")
        arguments = []
        while i < len(text) and text[i] == "{":
            # Careful: the result from find_end_bracket is relative to text[i:], not text.
            j = find_end_bracket(text[i:])
            arg = text[i+1:i+j -1] # Exclude both brackets
            arguments.append(arg)
            i += j
        return macro_item(arguments)
