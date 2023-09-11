from pathlib import Path
from ..core.abstractparser import AbstractParser
from ..core.havenlexer import HavenLexer
from ..core.items import  AbstractItem, ImageCommand, AoECommand, TextItem, LineItem, ColumnItem
from ..core.macros import AbstractMacro, EndMacro, EndLastMacro, TopLeftMacro, BottomRightMacro, Column2Macro
from ..core.utils import list_join

from .frosthaven_aliases import fh_base_aliases
from .frosthaven_items import FHTopmostColumnItem
from .frosthavenlinecontext import FrosthavenLineContext
from .frosthaven_constants import *
from .frosthaven_commands import SecondaryActionBox


class FrosthavenParser(AbstractParser):
    def __init__(self, path_to_gml: Path):
        super().__init__(path_to_gml)
        self.lexer = HavenLexer(fh_base_aliases)
        self.command_tokens = {"\\image": ImageCommand,
                        "\\aoe": AoECommand,
                    }

        self.macro_tokens = {"@end": EndMacro,
                       "@endlast": EndLastMacro,
                       "@topleft": TopLeftMacro,
                       "@bottomright": BottomRightMacro,
                       "@column2": Column2Macro}

    def parse(self,
              action: str,
              class_color: dict = {"red": 0, "green": 0, "blue": 0},
              additional_aliases: str = ""):
        splitted_lines = self.lexer.separate_lines(action, additional_aliases = additional_aliases)

        central_column_items = []
        primary_line = ""
        secondary_lines = []
        for i, (text, had_tabulation) in enumerate(splitted_lines):
            if not had_tabulation:
                # This is a primary line, or we reached the end of instructions: create the associated items
                item = self.create_and_order_items(primary_line, secondary_lines, class_color)
                if item is not None:
                    central_column_items.append(item)
                primary_line = text
                secondary_lines = []
            else:
                # Secondary line - wait until there is a primary line for it to be parsed.
                secondary_lines.append(text)
        if len(secondary_lines) > 0:
            item = self.create_and_order_items(primary_line, secondary_lines, class_color)
            if item is not None:
                central_column_items.append(item)

        first_column = FHTopmostColumnItem(central_column_items, self.path_to_gml)

        other_column = FHTopmostColumnItem([], FrosthavenLineContext(), self.path_to_gml)
        return {"topleft": other_column, "center": first_column, "center2": other_column, "bottomright": other_column}, []

    def create_and_order_items(self,
                                primary_line: str,
                                secondary_lines: list[str],
                                class_color: dict = {"red": 0, "green": 0, "blue": 0}):
        """
        Parse the primary line, then parse all secondary lines using a whitish background.
        Inputs should be raw gml text which hasn't been splitted into lexemes yet.
        """
        primary_lexemes = self.lexer.input(primary_line)
        primary_action = None
        if len(primary_line) > 0:
            primary_action = self.gml_line_to_items(primary_lexemes, FrosthavenLineContext(class_color=class_color))
            # Warning: primary_action is a list of LineItem

        secondary_items = []
        for line in secondary_lines:
            line_lexemes = self.lexer.input(line)
            secondary_items.append(self.gml_line_to_items(line_lexemes, FrosthavenLineContext(class_color=class_color)))
        # Flatten the secondary LineItems
        if len(secondary_items) > 0:
            secondary_items = [e for lines in secondary_items for e in lines]
            secondary_action = SecondaryActionBox([ColumnItem(secondary_items, FrosthavenLineContext())], FrosthavenLineContext())

        all_actions = []
        if primary_action is not None:
            all_actions.append(primary_action[0])
        if len(secondary_items) > 0:
            all_actions.append(secondary_action)
        all_actions = list_join(all_actions, TextItem(" ", FrosthavenLineContext()))
        return LineItem(all_actions, FrosthavenLineContext())

    def gml_line_to_items(self,
                          gml_line : str | list[str],
                          gml_context: FrosthavenLineContext,
                          ongoing_line : list[AbstractItem] = None,
                          width : int = fh_card_width*0.78,
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
        blank = TextItem([" "], FrosthavenLineContext(font_size=gml_context.font_size))
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
                    if gml_context.font_size == fh_big_font_size:
                        blank = TextItem([" "], FrosthavenLineContext(font_size=fh_big_font_size))

                splitted_gml.pop(0)
                result = []
                for line in lines:
                    result.append(FrosthavenLineContext(list_join(line, blank), gml_context, self.path_to_gml))
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
            result.append(LineItem(list_join(line, blank), gml_context, self.path_to_gml))
        return result