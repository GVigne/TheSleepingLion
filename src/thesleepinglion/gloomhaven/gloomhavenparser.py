from pathlib import Path
from copy import deepcopy

from ..core.abstractparser import AbstractParser
from ..core.havenlexer import HavenLexer
from ..core.items import AbstractItem, AoECommand, TextItem
from ..core.macros import AbstractMacro, EndMacro, EndLastMacro, TopLeftMacro, BottomRightMacro, Column2Macro
from ..core.utils import list_join
from .gloomhaven_items import GloomhavenImage, GloomhavenColumnItem, GloomhavenLineItem, GHTopmostColumnItem, GHTopmostLineItem
from .gloomhaven_macros import TitleFontMacro, ColorMacro, SmallSizeMacro, BaseSizeMacro, BannerMacro
from .gloomhavenlinecontext import GloomhavenLineContext
from .gloomhaven_aliases import base_aliases
from .gloomhaven_constants import card_width, small_font_size

class GloomhavenParser(AbstractParser):
    """
    A parser for Gloomhaven syntax
    """
    def __init__(self, path_to_gml: Path):
        super().__init__(path_to_gml)
        self.lexer = HavenLexer(base_aliases)
        self.command_tokens = {"\\image": GloomhavenImage,
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
                       "@banner": BannerMacro,
                       "@topleft": TopLeftMacro,
                       "@bottomright": BottomRightMacro,
                       "@column2": Column2Macro}

    def parse(self,
              action: str,
              class_color: dict = {"red": 0, "green": 0, "blue": 0},
              additional_aliases: str = "",
              action_box_size = 0.775*card_width):
        """
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
                                                          GloomhavenLineContext.CreateFromIndentation(had_tabulation, class_color),
                                                          width = 0.5*action_box_size)
        # Promote the LineItem objects
        second_column_items = [GHTopmostLineItem.promoteLineItem(line) for line in second_column_items]
        second_column = GloomhavenColumnItem(second_column_items, self.path_to_gml)
        first_column_items = []
        for lexemes, had_tabulation in all_lines["center"]:
            first_column_items += self.gml_line_to_items(lexemes,
                                                        GloomhavenLineContext.CreateFromIndentation(had_tabulation, class_color),
                                                        width = action_box_size - second_column.get_width())
        # Promote the LineItem objects
        first_column_items = [GHTopmostLineItem.promoteLineItem(line) for line in first_column_items]
        first_column = GloomhavenColumnItem(first_column_items, self.path_to_gml)

        # Throw second and column and start again if the first is small
        if first_column.get_width() < 0.45*action_box_size and second_column.get_width() > 0.45*action_box_size: # Small tolerance
            second_column_items = []
            for lexemes, had_tabulation in save_lines_second_column:
                second_column_items += self.gml_line_to_items(lexemes,
                                                            GloomhavenLineContext.CreateFromIndentation(had_tabulation, class_color),
                                                            width = action_box_size - first_column.get_width())
            # Promote the LineItem objects
            second_column_items = [GHTopmostLineItem.promoteLineItem(line) for line in second_column_items]
            second_column = GloomhavenColumnItem(second_column_items, self.path_to_gml)
        # Now parse the top column ...
        items = []
        for lexemes, had_tabulation in all_lines["topleft"]:
            items += self.gml_line_to_items(lexemes,
                                            GloomhavenLineContext.CreateFromIndentation(had_tabulation, class_color),
                                            width = action_box_size)
        items = [GHTopmostLineItem.promoteLineItem(line) for line in items]
        top_column = GloomhavenColumnItem(items, self.path_to_gml)
        # ... and the bottom column
        items = []
        for lexemes, had_tabulation in all_lines["bottomright"]:
            items += self.gml_line_to_items(lexemes,
                                            GloomhavenLineContext.CreateFromIndentation(had_tabulation, class_color),
                                            width = action_box_size)
        items = [GHTopmostLineItem.promoteLineItem(line) for line in items]
        bot_column = GloomhavenColumnItem(items, self.path_to_gml)

        # Now promote the four columns
        first_column =  GHTopmostColumnItem.promoteColumnItem(first_column)
        second_column = GHTopmostColumnItem.promoteColumnItem(second_column)
        bot_column = GHTopmostColumnItem.promoteColumnItem(bot_column)
        top_column = GHTopmostColumnItem.promoteColumnItem(top_column)

        all_warnings = []
        for column in [first_column, second_column, bot_column, top_column]:
            all_warnings = all_warnings + column.get_warnings()

        return {"topleft": top_column, "center": first_column, "center2": second_column, "bottomright": bot_column}, all_warnings

    def gml_line_to_items(self,
                          gml_line : str | list[str],
                          gml_context: GloomhavenLineContext,
                          ongoing_line : list[AbstractItem] = None,
                          width : int = card_width*0.78,
                          ongoing_x: int = 0,
                          ongoing_blank: TextItem | None = None,
                          ):
        """
        Return a list of LineItems corresponding to the given GML line. The input may either be a string (for example,
        an entire line to parse), or a list of string (which have already been splitted by the lexer).
        If width =-1, then fit everything on a single line.
        This function also adds a blank inbetween every item to have a prettier output.
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

        ## This blank will be added inbetween every item in a line.
        ## It's size can be changed if a macro changes the size policy for this GML line
        blank = TextItem([" "], GloomhavenLineContext(font_size=gml_context.font_size))
        if ongoing_blank is not None:
            blank = ongoing_blank

        while len(splitted_gml) > 0:
            current_str = splitted_gml[0]
            if self.is_command(current_str):
                item = self.create_command(current_str, gml_context)
            elif self.is_macro(current_str):
                macro = self.create_macro(current_str)
                if isinstance(macro, AbstractMacro):
                    # The macro is NOT a positional macro, hence it should influence the line context
                    macro.change_context(gml_context) # Influece the current context
                    if gml_context.font_size == small_font_size:
                        blank = TextItem([" "], GloomhavenLineContext(font_size=small_font_size))

                splitted_gml.pop(0)
                result = []
                for line in lines:
                    result.append(GloomhavenLineItem(list_join(line, blank), gml_context, self.path_to_gml))
                return result + self.gml_line_to_items(splitted_gml,
                                                      gml_context,
                                                      ongoing_line = current_line,
                                                      width = width,
                                                      ongoing_x = x,
                                                      ongoing_blank = blank)
            else: # current_str is a text
                # Compute the maximum space allowed for this text
                if width == -1:
                    allowed_width = -1
                else:
                    allowed_width = width - x

                minimum_one_word = (len(current_line)==0) # If at least one word should be placed in the line or if 0 words can be placed
                item, remain_str = self.create_text(current_str, allowed_width, gml_context, minimum_one_word)
                if remain_str != "":
                    if item is not None:
                        current_line.append(item)
                    lines.append(current_line)
                    current_line = []
                    x = 0
                    splitted_gml[0] = remain_str # Reminder: splitted_gml[0] is the current item being parsed
                    continue

            if width == -1 or item.get_width() < width - x:
                current_line.append(item)
            else:
                lines.append(current_line)
                current_line = [item]
                x = 0
            x += item.get_width() + blank.get_width()
            splitted_gml.pop(0)

        if current_line != []:
            lines.append(current_line)

        # Now, we convert all lines into LineItems with blank inbetween every element
        result = []
        for line in lines:
            result.append(GloomhavenLineItem(list_join(line, blank), gml_context, self.path_to_gml))
        return result


from .gloomhaven_commands import EnhancementDotCommand, InsideCommand, ExpCommand, MultilineCommand, ChargesLossCommand, \
        ChargesNonLossCommand, SummonCommand, DividerLine
