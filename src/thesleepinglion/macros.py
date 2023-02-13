from .constants import *
from .gmllinecontext import GMLLineContext
from .errors import MismatchNoArguments, InvalidArgumentType

class AbstractMacro:
    """
    An abstract class to represent macros.
    """
    def __init__(self, arguments : list[str] =  []):
        self.arguments = arguments

    def change_context(self, gmllinecontext: GMLLineContext):
        """
        The influence this macro has on the following items that will be created.
        """
        return None

    def get_position(self):
        """
        Positional macros are an exception, as they don't interact with the context. This function should
        only be overloaded by positional macros.
        """
        return "center"

class EndMacro(AbstractMacro):
    #TODO this shouldn't be a class but a default behaviour of gml_line_to_items
    def __init__(self, arguments: list[str] = []):
        super().__init__(arguments)
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@end' macro doesn't take arguments, but {len(arguments)} were given.")

    def change_context(self, gmllinecontext: GMLLineContext):
        gmllinecontext.clear()

class EndLastMacro(AbstractMacro):
    def __init__(self, arguments: list[str] = []):
        super().__init__(arguments)
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@endlast' macro doesn't take arguments, but {len(arguments)} were given.")

    def change_context(self, gmllinecontext: GMLLineContext):
        gmllinecontext.clear_last_effect()

class ColorMacro(AbstractMacro):
    """
    Change the the color of the following text items.
    """
    def __init__(self, arguments: list[str] = []):
        super().__init__(arguments)
        if len(arguments) != 3:
            raise MismatchNoArguments(f"The '@color' macro takes 3 arguments, but {len(arguments)} were given.")
        try:
            self.red = int(arguments[0])
            self.green = int(arguments[1])
            self.blue = int(arguments[2])
        except Exception:
            raise InvalidArgumentType("Arguments for the '@color' macro must be integers between 0 and 255.")

    def change_context(self, gmllinecontext: GMLLineContext):
        gmllinecontext.new_context_effects(text_color = {"red": self.red, "green": self.green, "blue": self.blue})

class SmallSizeMacro(AbstractMacro):
    def __init__(self, arguments: list[str] = []):
        super().__init__(arguments)
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@small' macro doesn't take arguments, but {len(arguments)} were given.")

    def change_context(self, gmllinecontext: GMLLineContext):
        gmllinecontext.new_context_effects(font_size = small_font_size)

class BaseSizeMacro(AbstractMacro):
    def __init__(self, arguments: list[str] = []):
        super().__init__(arguments)
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@big' macro doesn't take arguments, but {len(arguments)} were given.")

    def change_context(self, gmllinecontext: GMLLineContext):
        gmllinecontext.new_context_effects(font_size = base_font_size)

class TitleFontMacro(AbstractMacro):
    """
    Change the the font of the following items into the title font.
    """
    def __init__(self, arguments: list[str] = []):
        super().__init__(arguments)
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@title_font' macro doesn't take arguments, but {len(arguments)} were given.")

    def change_context(self, gmllinecontext: GMLLineContext):
        gmllinecontext.new_context_effects(font = title_font)


# Postional macros don't interact with the context, but they do interact with gml_line_to_items!

class TopLeftMacro(AbstractMacro):
    def __init__(self, arguments: list[str] = []):
        super().__init__(arguments)
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@topleft' macro doesn't take arguments, but {len(arguments)} were given.")

    def get_position(self):
        return "topleft"

class BottomRightMacro(AbstractMacro):
    def __init__(self, arguments: list[str] = []):
        super().__init__(arguments)
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@bottomright' macro doesn't take arguments, but {len(arguments)} were given.")

    def get_position(self):
        return "bottomright"

class Column2Macro(AbstractMacro):
    def __init__(self, arguments: list[str] = []):
        super().__init__(arguments)
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@column2' macro doesn't take arguments, but {len(arguments)} were given.")

    def get_position(self):
        return "center2"