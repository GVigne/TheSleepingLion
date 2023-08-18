from .abstractGMLlinecontext import AbstractGMLLineContext
from .errors import MismatchNoArguments

class AbstractMacro:
    """
    An abstract class to represent macros. Macros modify an instance of AbstractGMLLineContext to influence
    the following items which will be created. This is done through the change_context method which must
    be overloaded.
    """
    def __init__(self, arguments : list[str] =  []):
        self.arguments = arguments

    def change_context(self, gmllinecontext: AbstractGMLLineContext):
        pass

class EndLastMacro(AbstractMacro):
    def __init__(self, arguments: list[str] = []):
        super().__init__(arguments)
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@endlast' macro doesn't take arguments, but {len(arguments)} were given.")

    def change_context(self, gmllinecontext: AbstractGMLLineContext):
        gmllinecontext.clear_last_effect()

class EndMacro(AbstractMacro):
    def __init__(self, arguments: list[str] = []):
        super().__init__(arguments)
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '@end' macro doesn't take arguments, but {len(arguments)} were given.")

    def change_context(self, gmllinecontext: AbstractGMLLineContext):
        gmllinecontext.clear()

class AbstractPositionalMacros:
    """
    Positional macros don't interact with the context, but do interact with the parser. This is done through
    the get_position methods which must be overloaded and must return a string among the following: topleft, bottomright, center2
    """
    def __init__(self, macro_name, arguments: list[str] = []):
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '{macro_name}' macro doesn't take arguments, but {len(arguments)} were given.")

    def get_position(self):
        pass

class TopLeftMacro(AbstractPositionalMacros):
    def __init__(self, arguments: list[str] = []):
        super().__init__("@topleft", arguments)

    def get_position(self):
        return "topleft"

class BottomRightMacro(AbstractMacro):
    def __init__(self, arguments: list[str] = []):
        super().__init__("@bottomright", arguments)

    def get_position(self):
        return "bottomright"

class Column2Macro(AbstractMacro):
    def __init__(self, arguments: list[str] = []):
        super().__init__("@column2", arguments)

    def get_position(self):
        return "center2"