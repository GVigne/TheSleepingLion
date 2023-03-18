
class CommandNotFound(ValueError):
    pass

class MacroNotFound(ValueError):
    pass

class BracketError(ValueError):
    pass

class MismatchNoArguments(ValueError):
    pass

class EmptyArgument(ValueError):
    pass

class InvalidCustomAlias(ValueError):
    pass

class InvalidArgumentType(ValueError):
    pass

class ImageNotFound(ValueError):
    pass

class InvalidGMLFile(ValueError):
    pass

class InvalidAoEFile(ValueError):
    pass

class AoeFileNotFound(ValueError):
    pass

class CardNameAlreadyExists(ValueError):
    pass