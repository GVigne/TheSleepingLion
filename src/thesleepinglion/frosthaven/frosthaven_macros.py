from ..core.errors import MismatchNoArguments
from ..core.macros import AbstractMacro

from .frosthavenlinecontext import FrosthavenLineContext
from .frosthaven_constants import *

class MandatoryMacro:
    """
    A macro to control the placement of mandatory boxes. It is neither a PositionalMacro nor an AbstractMacro.
    """
    def __init__(self, arguments: list[str]):
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@mandatory' macro doesn't take arguments, but {len(arguments)} were given.")

class BaseSizeMacro(AbstractMacro):
    def __init__(self, arguments: list[str] = []):
        super().__init__(arguments)
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@small' macro doesn't take arguments, but {len(arguments)} were given.")

    def change_context(self, frosthavenContext: FrosthavenLineContext):
        frosthavenContext.new_context_effects(font_size = fh_base_font_size)

class MediumSizeMacro(AbstractMacro):
    def __init__(self, arguments: list[str] = []):
        super().__init__(arguments)
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@medium' macro doesn't take arguments, but {len(arguments)} were given.")

    def change_context(self, frosthavenContext: FrosthavenLineContext):
        frosthavenContext.new_context_effects(font_size = fh_medium_font_size)

class BigSizeMacro(AbstractMacro):
    def __init__(self, arguments: list[str] = []):
        super().__init__(arguments)
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@big' macro doesn't take arguments, but {len(arguments)} were given.")

    def change_context(self, frosthavenContext: FrosthavenLineContext):
        frosthavenContext.new_context_effects(font_size = fh_big_font_size)