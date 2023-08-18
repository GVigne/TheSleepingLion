from enum import Enum, auto

class Haven(Enum):
    """
    Use this enum when you want to make the difference between a Gloomhaven-specific behavior, a Frosthaven-specific
    behavior, or something which behaves the same for both syntaxes.
    """
    GLOOMHAVEN = auto()
    FROSTHAVEN = auto()
    COMMON = auto()
