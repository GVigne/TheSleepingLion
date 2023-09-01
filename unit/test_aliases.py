import pytest
from thesleepinglion.gloomhaven.gloomhavenlexer import GloomhavenLexer
from thesleepinglion.gloomhaven.gloomhaven_aliases import base_aliases

def test_aliases():
    """
    Test all the aliases in the standard library.
    """
    lexer = GloomhavenLexer()
    for alias in base_aliases:
        splitted = alias.split(" = ")
        pattern, replacement = splitted[0], splitted[1]
        pattern =pattern.replace("$x$", "2")
        replacement = replacement.replace("$x$", "2")
        assert lexer.include_aliases(pattern) == replacement

def test_longer_aliases():
    """
    A test implying many different aliases.
    """
    lexer = GloomhavenLexer()
    text = "Perform \\attack{3} on a adjacent enemy. \\poison, \\immobilize an enemy at \\range{5}"
    true_text = "Perform Attack \\image{attack.svg} 3 on a adjacent enemy. POISON \\image{poison.svg}, IMMOBILIZE \\image{immobilize.svg} an enemy at Range \\image{range.svg} 5"
    assert lexer.include_aliases(text) == true_text
