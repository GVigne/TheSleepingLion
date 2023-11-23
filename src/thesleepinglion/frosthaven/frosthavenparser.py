from pathlib import Path

from ..core.abstractparser import AbstractParser
from ..core.havenlexer import HavenLexer

from ..core.items import  AbstractItem, AoECommand, TextItem, LineItem, ColumnItem, AbstractParserArguments
from ..core.macros import AbstractMacro, EndMacro, EndLastMacro, TopLeftMacro, BottomRightMacro, Column2Macro
from ..core.utils import list_join

from .frosthaven_aliases import fh_base_aliases
from .frosthaven_items import FrosthavenImage, FHTopmostColumnItem
from .frosthavenlinecontext import FrosthavenLineContext
from .frosthaven_constants import *
from .frosthaven_macros import MandatoryMacro, ConditionalMacro, ConditionalConsumptionMacro, BaseSizeMacro, \
                             BigSizeMacro, TinyImageMacro

class FrosthavenParserArguments(AbstractParserArguments):
    def __init__(self, ongoing_line : list[AbstractItem] = None,
                 width : int = card_drawing_width,
                 ongoing_x: int = 0,
                 ongoing_blank: TextItem | None = None):
        self.ongoing_line = ongoing_line
        self.width = width
        self.ongoing_x = ongoing_x
        self.ongoing_blank = ongoing_blank

class FrosthavenParser(AbstractParser):
    def __init__(self, path_to_gml: Path):
        super().__init__(path_to_gml)
        self.lexer = HavenLexer(fh_base_aliases)
        self.command_tokens = {"\\image": FrosthavenImage,
                        "\\aoe": AoECommand,
                        "\\ability_line": AbilityLine,
                        "\\conditional": BaseConditionalBox,
                        "\\conditional_consumption": ConditionalConsumeBox,
                        "\\exp": FHExpCommand,
                        "\\charges": FHChargesCommand,
                        "\\charges_line": FHOneLineChargesCommand,
                        "\\reduced_column": ReducedColumn
                    }

        self.macro_tokens = {"@end": EndMacro,
                       "@endlast": EndLastMacro,
                       "@topleft": TopLeftMacro,
                       "@bottomright": BottomRightMacro,
                       "@column2": Column2Macro,
                       "@mandatory": MandatoryMacro,
                       "@conditional": ConditionalMacro,
                       "@conditional_consumption": ConditionalConsumptionMacro,
                       "@small": BaseSizeMacro,
                       "@big": BigSizeMacro,
                       "@tiny": TinyImageMacro}

    def parse(self,
              action: str,
              class_color: dict = {"red": 0, "green": 0, "blue": 0},
              additional_aliases: str = "",
              is_top_action: bool = True):
        splitted_lines = self.lexer.separate_lines(action, additional_aliases = additional_aliases)

        # Parse all the lines as combinations of a primary action and secondary actions (which are indented in the GML file)
        all_items = {"topleft": [], "center": [], "center2": [], "bottomright": []}
        primary_line = ""
        secondary_lines = []
        bottomright_is_mandatory = False
        for text, had_tabulation in splitted_lines:
            if not had_tabulation:
                # This is a primary line, or we reached the end of instructions: create the associated items
                item, pos, is_mandatory = self.create_and_order_items(primary_line, secondary_lines, class_color)
                if item is not None:
                    if is_mandatory and pos !="bottomright":
                        item = [LineItem([MandatoryBox([ColumnItem(item)], FrosthavenLineContext(class_color=class_color))])]
                    if pos == "bottomright":
                        bottomright_is_mandatory = bottomright_is_mandatory or is_mandatory
                    all_items[pos] += item
                primary_line = text
                secondary_lines = []
            else:
                # Secondary line - wait until there is a primary line for it to be parsed.
                secondary_lines.append(text)
        if len(primary_line) > 0 or len(secondary_lines) > 0:
            item, pos, is_mandatory = self.create_and_order_items(primary_line, secondary_lines, class_color)
            if item is not None:
                if is_mandatory and pos !="bottomright":
                    item = [LineItem([MandatoryBox([ColumnItem(item)], FrosthavenLineContext(class_color=class_color))])]
                if pos == "bottomright":
                    bottomright_is_mandatory = bottomright_is_mandatory or is_mandatory
                all_items[pos] += item
        center_column = FHTopmostColumnItem(all_items["center"], self.path_to_gml)

        # Wrap the bottomright column in a mandatory box
        bottomright_items = all_items["bottomright"]
        if len(bottomright_items) and bottomright_is_mandatory> 0:
            if is_top_action:
                bottomright_items = [TopActionBRMandatoryBox(bottomright_items, FrosthavenLineContext(class_color=class_color))]
            else:
                bottomright_items = [BotActionBRMandatoryBox(bottomright_items, FrosthavenLineContext(class_color=class_color))]

        botright_column = FHTopmostColumnItem(bottomright_items, self.path_to_gml)

        other_column = FHTopmostColumnItem([], FrosthavenLineContext(), self.path_to_gml)
        return {"topleft": other_column, "center": center_column, "center2": other_column, "bottomright": botright_column}, []

    def create_and_order_items(self,
                                primary_line: str,
                                secondary_lines: list[str],
                                class_color: dict = {"red": 0, "green": 0, "blue": 0}):
        """
        Parse the primary line, then parse all secondary lines using a whitish background. By default, secondary
        lines are parsed using the medium font.
        Inputs should be raw gml text which hasn't been splitted into lexemes yet.
        Returns
        - a list of LineItems, which should be displayed on the card, or None is both primary_line
        and secondary_lines are empty
        - a string representing the position of the group of lines
        - a boolean which is True if the line should be placed in a mandatory box
        """
        position = "center"
        primary_position = "center"
        secondary_positions = []
        is_mandatory = False
        is_conditional = False
        is_conditional_consumption = False
        if len(primary_line)==0 and len(secondary_lines) == 0:
            return None, position, is_mandatory

        primary_action = None
        if len(primary_line) > 0:
            lexemes = self.lexer.input(primary_line)
            primary_position = self.find_line_position(lexemes)
            # Check if a mandatory box should be drawn, and if it is the case, reduce the allowed width for items parsing
            is_mandatory = self.is_specific_action(lexemes, MandatoryMacro)
            is_conditional = self.is_specific_action(lexemes, ConditionalMacro)
            is_conditional_consumption = self.is_specific_action(lexemes, ConditionalConsumptionMacro)
            primary_line_width = card_drawing_width
            if is_mandatory:
                primary_line_width -= MandatoryBox.TotalAddedWith()
            if is_conditional or is_conditional_consumption:
                primary_line_width -= 2*BaseConditionalBox.AdditionalWidth()
            primary_action = self.gml_line_to_items(lexemes,
                                                    FrosthavenLineContext(class_color=class_color),
                                                    FrosthavenParserArguments(width=primary_line_width))

        # Note that primary_action is a list of LineItem. The first ones will be placed on the card, and
        # the secondary actions will be aligned with the last one.
        secondary_lines_width = card_drawing_width - 2*SecondaryActionBox.BoxAdditionalWidth()
        if primary_action is not None:
            secondary_lines_width -= primary_action[-1].get_width()

        secondary_items = []
        for line in secondary_lines:
            lexemes = self.lexer.input(line)
            secondary_positions.append(self.find_line_position(lexemes))
            # Same as above: reduce the allowed width if there is a mandatory box
            is_mandatory = is_mandatory or self.is_specific_action(lexemes, MandatoryMacro)
            is_conditional = is_conditional or self.is_specific_action(lexemes, ConditionalMacro)
            is_conditional_consumption = is_conditional_consumption or self.is_specific_action(lexemes, ConditionalConsumptionMacro)
            if is_mandatory:
                secondary_lines_width -= MandatoryBox.TotalAddedWith()
            if is_conditional or is_conditional_consumption:
                primary_line_width -= 2*BaseConditionalBox.AdditionalWidth()
            secondary_items.append(self.gml_line_to_items(lexemes,
                                                          FrosthavenLineContext(image_size=fh_small_image_size, class_color=class_color),
                                                          FrosthavenParserArguments(width=secondary_lines_width)))
        # Flatten the secondary LineItems
        secondary_action = None
        if len(secondary_items) > 0:
            secondary_items = [e for lines in secondary_items for e in lines]
            secondary_action = SecondaryActionBox([ColumnItem(secondary_items)], FrosthavenLineContext(class_color=class_color))

        # Now check the lines position by consuming the first macro
        position = primary_position
        for pos in secondary_positions:
            if position == "center" and pos !="center":
                position = pos

        blank = TextItem(" ", FrosthavenLineContext())
        result = None
        if primary_action is not None:
            result = primary_action
            if secondary_action is not None:
                # The default case. Add all secondary lines next to the last primary line
                result[-1] = LineItem([result[-1], blank, secondary_action])
        else:
            if secondary_action is not None:
                result = [LineItem([secondary_action])]

        if is_conditional:
            result = [LineItem([BaseConditionalBox(result, FrosthavenLineContext(class_color=class_color), True, self.path_to_gml)])]
        elif is_conditional_consumption:
            result = [LineItem([ConditionalConsumeBox(result, FrosthavenLineContext(class_color=class_color), True, self.path_to_gml)])]
        return result, position, is_mandatory

    def is_specific_action(self, line: list[str], pyth_object: type):
        """
        Similar to self.find_line_position, search the given line of lexemes and return True if it contains
        a specific macro, represented by the given python object (ex: "@mandatory" -> MandatoryMacro)
        """
        for lexeme in line:
            if self.is_macro(lexeme):
                macro = self.create_macro(lexeme)
                if isinstance(macro, pyth_object):
                    return True
        return False

    def gml_line_to_items(self,
                          gml_line: str | list[str],
                          gml_context: FrosthavenLineContext,
                          arguments: FrosthavenParserArguments):
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
        x = arguments.ongoing_x # The space currently taken by the items which have already been parsed.
        lines = []
        current_line = []
        if arguments.ongoing_line is not None:
            current_line = arguments.ongoing_line # Needed for recursion using macros.

        ## This blank will be added inbetween every item in a line.
        ## It's size can be changed if a macro changes the size policy for this GML line
        blank = TextItem([" "], FrosthavenLineContext(font_size=gml_context.font_size))
        if arguments.ongoing_blank is not None:
            blank = arguments.ongoing_blank

        while len(splitted_gml) > 0:
            current_str = splitted_gml[0]
            if self.is_command(current_str):
                item = self.create_command(current_str, gml_context, arguments)
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
                # Update parser's arguments
                arguments.ongoing_line = current_line
                arguments.ongoing_x = x
                arguments.ongoing_blank = blank
                return result + self.gml_line_to_items(splitted_gml, gml_context, arguments)
            else: # current_str is a text
                # Compute the maximum space allowed for this text
                if arguments.width == -1:
                    allowed_width = -1
                else:
                    allowed_width = arguments.width - x

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

            if arguments.width == -1 or item.get_width() < arguments.width - x:
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
            result.append(LineItem(line, gml_context, self.path_to_gml))
        return result

from .frosthaven_commands import SecondaryActionBox, MandatoryBox, TopActionBRMandatoryBox, BotActionBRMandatoryBox, \
                                AbilityLine, BaseConditionalBox, ConditionalConsumeBox, FHExpCommand, FHChargesCommand, \
                                FHOneLineChargesCommand, ReducedColumn