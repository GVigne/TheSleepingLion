from ..core.errors import MismatchNoArguments
from ..core.macros import AbstractMacro

from .frosthavenlinecontext import FrosthavenLineContext

class MandatoryMacro:
    """
    A macro to control the placement of mandatory boxes. It is neither a PositionalMacro nor an AbstractMacro.
    """
    def __init__(self, arguments: list[str]):
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@mandatory' macro doesn't take arguments, but {len(arguments)} were given.")