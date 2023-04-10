from gi.repository import Pango
from copy import deepcopy

from .items import LineItem, ColumnItem, TextItem
from .commands import *
from .macros import *
from .errors import CommandNotFound, MacroNotFound
from .constants import *
from .utils import text_to_pango, find_opened_bracket, find_end_bracket
from .gloomhavenlexer import GloomhavenLexer
from .gmllinecontext import GMLLineContext

class GloomhavenParser:
    """
    A parser for The Sleeping Lion. Given commands or lines (as strings), create the associated Items required
    to display a card.
    """
    def __init__(self, path_to_gml : Path):
        self.path_to_gml = path_to_gml
        self.lexer = GloomhavenLexer()
        self.command_tokens = {"\\image": ImageCommand,
                        "\\aoe": AoECommand,
                        "\\dot": EnhancementDotCommand,
                       "\\inside": InsideCommand,
                       "\\exp": ExpCommand,
                       "\\multiline": MultilineCommand,
                       "\\charges": ChargesLossCommand,
                       "\\charges_non_loss": ChargesNonLossCommand,
                       "\\summon": SummonCommand,
                       "\\divider_line": DividerLine
                    }

        self.macro_tokens = {"@end": EndMacro,
                       "@endlast": EndLastMacro,
                       "@title_font": TitleFontMacro,
                       "@color": ColorMacro,
                       "@small": SmallSizeMacro,
                       "@big": BaseSizeMacro,
                       "@topleft": TopLeftMacro,
                       "@bottomright": BottomRightMacro,
                       "@column2": Column2Macro}

    def parse(self,
              action : str,
              background_color: dict = {},
              additional_aliases: str = "",
              action_box_size = 0.775*card_width):
        """
        Given the text representing the a top or bottom action, return a dictionnary with keys being position and
        values being ColumnItems which should be drawn. Also return a list of warnings, ie non-breaking errors.
        This is the highest level function from this parser.

        Implementation-wise, here is how this parser works.
        - Take a raw .gml top or bottom action.
        - Ask the lexer to split it into user-defined lines (lexer.separate_lines)
        - For each line, ask the lexer to split in into lexemes (lexer.input)
        - For each line, identify its position: top, bottom, center... via the use of the associated macros (self.find_line_position)
        - For each line, transform the lexemes in Items which can be drawn (self.gml_line_to_items). This function is recursive
        and can be called by each created item. At this stage, positional macros are ignored, they were taken into account
        in the step before.

        The conversion from lexemes to items is done in a specific way to respect the lines' positions (units are given
        as percentages of the card's width):
        - parse the second column (if it exists), with an allowed width of 0.5.
        - get the width RW of the parsed second column.
        - parse the first column with an allowed width of 1-RW
        - get the width LW of the first column.
        - if LW < 0.5 and RW = 0.5, reparse the second column with and allowed width of 1 - LW
        (Parse the topright and bottomleft columns)
        This ensures that both columns try to expand as much as possible.
        """
        splitted_lines = self.lexer.separate_lines(action, additional_aliases = additional_aliases)
        all_lines = {"center" : [],
                    "center2": [],
                    "bottomright": [],
                    "topleft": []}
        for text, had_tabulation in splitted_lines:
            lexemes = self.lexer.input(text)
            position = self.find_line_position(lexemes)
            all_lines[position].append((lexemes, had_tabulation))
        save_lines_second_column = deepcopy(all_lines["center2"]) # A copy is needed as we will be using list.pop() in gml_lines_to_items

        # First parsing
        second_column_items = []
        for lexemes, had_tabulation in all_lines["center2"]:
            second_column_items += self.gml_line_to_items(lexemes,
                                                          GMLLineContext.CreateFromIndentation(had_tabulation),
                                                          width = 0.5*action_box_size,
                                                          image_color=background_color)
        second_column = ColumnItem(second_column_items, self.path_to_gml)
        first_column_items = []
        for lexemes, had_tabulation in all_lines["center"]:
            first_column_items += self.gml_line_to_items(lexemes,
                                                        GMLLineContext.CreateFromIndentation(had_tabulation),
                                                        width = action_box_size - second_column.get_width(),
                                                        image_color = background_color)
        first_column = ColumnItem(first_column_items, self.path_to_gml)

        # Throw second and column and start again if the first is small
        if first_column.get_width() < 0.45*action_box_size and second_column.get_width() > 0.45*action_box_size: # Small tolerance
            second_column_items = []
            for lexemes, had_tabulation in save_lines_second_column:
                second_column_items += self.gml_line_to_items(lexemes,
                                                            GMLLineContext.CreateFromIndentation(had_tabulation),
                                                            width = action_box_size - first_column.get_width(),
                                                            image_color = background_color)
            second_column = ColumnItem(second_column_items, self.path_to_gml)
        # Now parse top and bottom columns
        items = []
        for lexemes, had_tabulation in all_lines["topleft"]:
            items += self.gml_line_to_items(lexemes,
                                            GMLLineContext.CreateFromIndentation(had_tabulation),
                                            width = action_box_size,
                                            image_color = background_color)
        top_column = ColumnItem(items, self.path_to_gml)
        items = []
        for lexemes, had_tabulation in all_lines["bottomright"]:
            items += self.gml_line_to_items(lexemes,
                                            GMLLineContext.CreateFromIndentation(had_tabulation),
                                            width = action_box_size,
                                            image_color = background_color)
        bot_column = ColumnItem(items, self.path_to_gml)

        all_warnings = []
        for column in [first_column, second_column, bot_column, top_column]:
            all_warnings = all_warnings + column.get_warnings()
        return {"topleft": top_column, "center": first_column, "center2": second_column, "bottomright": bot_column}, all_warnings

    def find_line_position(self, line: list[str]):
        """
        Sort the given line splitted into lexemes (ie on of the result of lexer.separate_lines) according
        to its position (topleft, center, center2, bottomright).
        For each line, only the first positional macro is taken, other positional macros are ignored.
        """
        for lexeme in line:
            if self.is_macro(lexeme):
                macro = self.create_macro(lexeme)
                new_position = macro.get_position()
                if new_position != "center": # The default behavior
                    return new_position
        return "center"

    def is_command(self, text : str):
        """
        Return true if the given text represents a command.
        """
        return text[0] == "\\"

    def is_macro(self, text : str):
        """
        Return true if the given text represents a macro.
        """
        return text[0] == "@"

    def create_command(self,
                        text : str,
                        gml_context: GMLLineContext,
                        image_color: dict = {}):
        """
        Return the command corresponding to the given text.
        """
        i = find_opened_bracket(text)
        try:
            command_item = self.command_tokens[text[:i]]
        except Exception as e:
            raise CommandNotFound(f"The command '{text[:i]}' isn't defined.")
        arguments = []
        while i < len(text) and text[i] == "{":
            # Careful: the result from find_end_bracket is relative to text[i:], not text.
            j = find_end_bracket(text[i:])
            arg = text[i+1:i+j -1] # Exclude both brackets
            arguments.append(arg)
            i +=j
        return command_item(arguments, gml_context, path_to_gml= self.path_to_gml, image_color = image_color)

    def create_text(self,
                    text : str,
                    allowed_size : int,
                    gml_context: GMLLineContext,
                    minimum_one_word: bool = True):
        """
        Try to create a text item with the given size. If the text doesn't fit in the given space, try to
        fill it as much as possible, then return the part of the text which doesn't fit.
        Can return None instead of a text item if there wasn't enough space and minimum_one_word is False, so as
        to prevent empty items being placed in the line.
        If allowed_size = -1, ignore all size restrictions.
        """
        if allowed_size == -1:
            return TextItem(text, gml_context, path_to_gml = self.path_to_gml), ""
        # Try to fit as much text as possible in the give size.
        words = text.split(" ")
        a = len(words)
        b = len(words)
        while True:
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

        item = TextItem(" ".join(words[:a]), gml_context, path_to_gml = self.path_to_gml)
        return item, " ".join(words[a:])  # Joining on a empty list returns an empty string.

    def create_macro(self, text : str):
        i = find_opened_bracket(text)
        try:
            macro_item = self.macro_tokens[text[:i]]
        except Exception as e:
            raise MacroNotFound(f"The macro '{text[:i]}' isn't defined.")
        arguments = []
        while i < len(text) and text[i] == "{":
            # Careful: the result from find_end_bracket is relative to text[i:], not text.
            j = find_end_bracket(text[i:])
            arg = text[i+1:i+j -1] # Exclude both brackets
            arguments.append(arg)
            i +=j
        return macro_item(arguments)

    def gml_line_to_items(self,
                          gml_line : str | list[str],
                          gml_context: GMLLineContext,
                          ongoing_line : list[AbstractItem] = None,
                          width : int = card_width*0.78,
                          ongoing_x: int = 0,
                          image_color: dict = {}, # The class's color: may change the color of some images
                          ):
        """
        Return a list of LineItems corresponding to the given GML line. The input may either be a string (for example,
        an entire line to parse), or a list of string (which have already been splitted by the lexer).
        If width =-1, then fit everything on a single line.
        """
        # TODO: rewrite by splitting all three cases
        if isinstance(gml_line, list):
            # Input was already read by the lexer. This can happen when recursion occurs due to macros
            splitted_gml = gml_line
        else:
            splitted_gml = self.lexer.input(gml_line)
        x = ongoing_x # The space currently taken by the items which have already been parsed.
        lines = []
        current_line = []
        if ongoing_line is not None:
            current_line = ongoing_line # Needed for recursion using macros.

        while len(splitted_gml) > 0:
            current_str = splitted_gml[0]
            if self.is_command(current_str):
                item = self.create_command(current_str, gml_context, image_color=image_color)
            elif self.is_macro(current_str):
                macro = self.create_macro(current_str)
                macro.change_context(gml_context) # Influece the current context

                splitted_gml.pop(0)
                return lines + self.gml_line_to_items(splitted_gml,
                                                      gml_context,
                                                      ongoing_line = current_line,
                                                      width = width,
                                                      ongoing_x = x,
                                                      image_color = image_color)
            else: # current_str is a text
                # Compute the maximum space allowed for this text
                if width == -1:
                    allowed_width = -1
                else:
                    allowed_width = width - x
                # If a macro was used to change part of text, then the lexer will have removed blanks. To prevent text from
                # being immediately next to each other, we re-add it here.
                # For example: ["BIG", "@small", "small", "@endlast", "BIG"] => "BIG small BIG" and not "BIGsmallBIG"
                if len(current_line) > 0 and isinstance(current_line[-1],TextItem):
                    # Text was somehow splitted: it should have a blank inbetween the last text and this one.
                    current_str = " " + current_str

                minimum_one_word = (len(current_line)==0) # If at least one word should be placed in the line or if 0 words can be placed
                item, remain_str = self.create_text(current_str, allowed_width, gml_context, minimum_one_word)
                if remain_str != "":
                    if item is not None:
                        current_line.append(item)
                    lines.append(LineItem(current_line, self.path_to_gml))
                    current_line = []
                    x = 0
                    splitted_gml[0] = remain_str # Reminder: splitted_gml[0] is the current item being parsed
                    continue

            if width == -1 or item.get_width() < width - x:
                current_line.append(item)
            else:
                lines.append(LineItem(current_line, self.path_to_gml))
                current_line = [item]
                x = 0
            x += item.get_width()
            splitted_gml.pop(0)

        if current_line != []:
            lines.append(LineItem(current_line, self.path_to_gml))

        return lines
