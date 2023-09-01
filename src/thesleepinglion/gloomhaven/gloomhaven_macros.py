from ..core.errors import MismatchNoArguments, InvalidArgumentType
from ..core.macros import AbstractMacro
from .gloomhaven_constants import *
from .gloomhavenlinecontext import GloomhavenLineContext

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

    def change_context(self, gloomhavenContext: GloomhavenLineContext):
        gloomhavenContext.new_context_effects(text_color = {"red": self.red, "green": self.green, "blue": self.blue})

class SmallSizeMacro(AbstractMacro):
    def __init__(self, arguments: list[str] = []):
        super().__init__(arguments)
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@small' macro doesn't take arguments, but {len(arguments)} were given.")

    def change_context(self, gloomhavenContext: GloomhavenLineContext):
        gloomhavenContext.new_context_effects(font_size = small_font_size)

class BaseSizeMacro(AbstractMacro):
    def __init__(self, arguments: list[str] = []):
        super().__init__(arguments)
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@big' macro doesn't take arguments, but {len(arguments)} were given.")

    def change_context(self, gloomhavenContext: GloomhavenLineContext):
        gloomhavenContext.new_context_effects(font_size = base_font_size)

class TitleFontMacro(AbstractMacro):
    """
    Change the the font of the following items into the title font.
    """
    def __init__(self, arguments: list[str] = []):
        super().__init__(arguments)
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@title_font' macro doesn't take arguments, but {len(arguments)} were given.")

    def change_context(self, gloomhavenContext: GloomhavenLineContext):
        gloomhavenContext.new_context_effects(font = title_font)

class BannerMacro(AbstractMacro):
    """
    Create a dark banner like the Mindthief's Augments.
    This macro is unaffected by @end or @endlast macros, as it is global to a GloomhavenLineItem.
    """
    def __init__(self, arguments: list[str] = []):
        super().__init__(arguments)
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@banner' macro doesn't take arguments, but {len(arguments)} were given.")

    def change_context(self, gloomhavenContext: GloomhavenLineContext):
        gloomhavenContext.new_context_effects(banner_background = True)