import regex as re
from .aliases import base_aliases
from .utils import find_opened_bracket, find_end_bracket, find_end_macro, alias_text_to_alias_list
from .errors import InvalidCustomAlias

class GloomhavenLexer:
    """
    A lexer for The Sleeping Lion. The lexer should do the first interpretation of the text from a GML file
    representing the top/bottom action of a card. Namely, the lexer should be able to:
        - split the raw text representing a top/bottom action into several lines (separate_lines)
        - split a line into lexemes: either a text or commands (input)
    When separating the lines, the lexer should also substitute all aliases.
    """
    def __init__(self):
        pass

    def input(self, text : str):
        """
        Given a GML line, split it into a list of high level objects. This function stops at the first hierarchical level.
        Ex: "Attack \image{attack.svg} 2" -> ["Attack ", "\image{attack.svg}", " 2"]
        Ex: "\command1{\command2{...}} 2" -> ["\command1{\command2{...}}",  " 2"]
        Ex: "\inside{...}{...}" -> ["\inside{...}{...}"]
        Note: this function does not replace aliases with their values. It should only be used on a single line from the
        output of separate_lines.
        """
        if len(text) ==0:
            return []
        if text[0] == "\\":
            # This is a command. Find the bracket ending the command. Reminder: a command can have many arguments!
            i = find_opened_bracket(text)
            while i < len(text) and text[i] == "{":
                # Careful: the result from find_end_bracket is relative to text[i:], not text.
                i += find_end_bracket(text[i:])
        elif text[0] == "@":
            # This is some sort of macro
            i = find_end_macro(text)
        else:
            # This is some sort of text.
            i = self.find_next_command_macro(text)
        return [text[:i].strip()] + self.input(text[i:].strip())

    def separate_lines(self, text : str, additional_aliases: str = ""):
        """
        Given a raw GML text representing a top or bottom action, split it into different lines. Also replace
        any aliases defined in base_aliase and in additional_aliases (user-defined aliases).
        Return a list of tuple. For each tuple:
            -the first element is a string representing the line
            -the second is False if there wasn't any indentation, True if there was one
        This function should always be the first one called on a text extracted from a .gml file.
        """
        res = []
        splitted = text.split("\n")
        for line in splitted:
            if line.strip(): # Make sure the line is not empty or full of blanks
                small = False
                if line.lstrip() != line:
                    # There is some form of indentation
                    small = True
                line = line.strip()
                if line:
                    # Quick check to see if the line isn't empty
                    res.append((line, small))
        return [(self.include_aliases(line, additional_aliases=additional_aliases), indent) for (line, indent) in res]

    def include_aliases(self, text : str, additional_aliases: str = ""):
        """
        Include the aliases in the given text.
        """
        # Add first the user's aliases in case he wants to redefine an alias in the standard library
        all_aliases = alias_text_to_alias_list(additional_aliases) + base_aliases
        for alias in all_aliases:
            raw_pattern, raw_replacement = self.split_alias(alias)
            text = self.replace_alias(raw_pattern, raw_replacement, text)
        return text

    def split_alias(self, alias : str):
        """
        Roughly split the alias into a model pattern and the string it should be replaced by.
        Also make the alias regex-compatible, by inserting escape characters if needed.
        """
        splitted = alias.split("=")
        raw_pattern, raw_replacement = splitted[0].strip(), splitted[1].strip()
        # The Backslash plague. Regexp's "\" has a special meaning, so you need to escape it using another backslash.
        # The same rule applies for Python. So "\" -> "\\" in regexp -> "\\\\" in Python
        raw_pattern = raw_pattern.replace("\\","\\\\")
        return raw_pattern, raw_replacement

    def replace_alias(self, raw_pattern : str, raw_replacement : str, text : str):
        """
        Check if raw_pattern is a pattern found in the given text; if it is, replace it with raw_replacement.
        raw_pattern and raw_replacement should already be regex-compatible (see split_alias).
        Ex: replace_alias("\\\\p{$x$}", "MOVE $x$", "Before \p{4} After") returns "Before MOVE 4 After"

        Step 1 : create a regexp for the general pattern. Also create regexp to extract the user-defined
            variables between dollar signs.
        Step 2 : find the parts of the text matching the general pattern. Iterate through them, applying
            3 and 4.
        Step 3 : iterate through the raw pattern, catching the variable names (names between dollar signs).
            At the same time, catch the variable values.
        Step 4 : create the replacement string by iterating through the raw replacement pattern, and assigning
            each variable its value.
        Step 5 : reconstruct the text by concatenating the untouched parts of the text and the replacement
            strings.
        """
        pattern, extract_variables = self.make_regexp(raw_pattern)
        result = ""
        last = 0
        for match in pattern.finditer(text):
            variable_values = {}
            i = 0
            n_var = 0
            while i < len(raw_pattern):
                if raw_pattern[i] == "$":
                    j = self.find_next_dollar(raw_pattern[i+1:])
                    variable_values[raw_pattern[i+1:i+j+1]] = extract_variables[n_var].search(match.group(0)).group(0)
                    n_var +=1
                    i = i+j+2
                else:
                    i+=1

            to_replace = ""
            last_dollar_position = 0
            i = 0
            while i < len(raw_replacement):
                if raw_replacement[i] == "$":
                    j = self.find_next_dollar(raw_replacement[i+1:])
                    # Get the variable value
                    try:
                        replaced_value = variable_values[raw_replacement[i+1:i+j+1]]
                    except KeyError:
                        # The following lines simply format the error message
                        pretty_pattern = raw_pattern.replace("\\\\", "\\") # Undo what's be done in split_alias
                        raise InvalidCustomAlias(f"The custom alias {pretty_pattern} is invalid. The variable '{raw_replacement[i+1:i+j+1]}' found " \
                                                 "in the right hand side of the alias isn't defined in the left hand side.")
                    # Build the result string
                    to_replace += raw_replacement[last_dollar_position:i] + replaced_value
                    last_dollar_position = i+j+2
                    i = i+j+2
                else:
                    i +=1
            # Add the remaining letters from raw_pattern. Note: if there are no arguments, then last_dollar_position is still 0
            # so the following line copies raw_replacement in its entirety, which is what we cant
            to_replace += raw_replacement[last_dollar_position:i]

            start, end = match.span()
            result = result + text[last:start] + to_replace
            last = end
        return result + text[last:]

    def make_regexp(self, text : str):
        """
        Given a pattern, create a regexp matching it.
        Also create regexp extracting the variables.
        Ex: \command{x}{y} -> Return a regexp matching \command{something..}{something...}
                            -> Return a list with two elements, one extracting x and one extracting y
        """
        res = ""
        extract_variables = []
        i = 0
        while i < len(text):
            if text[i] =="$":
                res += "[^}]*" # Everything but closing parenthesis.
                # Else, \command{x}{y} won't be understood as a something with 2 arguments, but only one.
                # Ie the RE will match \command{     "x}{y"     } and not \command{"x"}{"y"}
                j = self.find_next_dollar(text[i+1:])
                i += j+2
            else:
                res += text[i]
                i +=1
        # Now, build the regexp extracting each variable
        i = 0
        while i < len(res):
            if res[i:i + 5] == "[^}]*":# Everything but closing parenthesis.
                # (?<=...) means the text has ... BEFORE, (?=...) means the text has ... AFTER.
                one_variable = "(?<=" + res[:i] + ").*(?=" + res[i+5:]+ ")"
                extract_variables.append(re.compile(one_variable))
                i = i+5
            else:
                i+=1
        return re.compile(res), extract_variables

    def find_next_dollar(self, text : str):
        """
        Return i such that text[i] is $ symbol.
        """
        for i,glyph in enumerate(text):
            if glyph =="$":
                return i
        return len(text)

    def find_next_command_macro(self, text : str):
        """
        Given a string, return an int i such that text[i] = is the \ character or the @ character.
        Return length(text) if no curly bracket was found.
        """
        for i,v in enumerate(text):
            if v == "\\" or v == "@":
                return i
        return len(text)
