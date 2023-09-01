from yaml import safe_dump
import cairo

from .abstractparser import AbstractParser

class AbstractCard:
    """
    An abstract class to represent a card. Provides a few methods to interface with the GUI.
    Child classes must overload the draw and parse_gml method. It's also best to overload the __init__ method
    to update self.top_areas and self.bot_areas with the correct instance of AbstractTopMostColumnItems
    """
    def __init__(self,
                path_to_gml,
                name: str,
                level: str,
                initiative: str,
                ID: str,
                top_text: str,
                bot_text: str,
                class_color: dict):
        self.path_to_gml = path_to_gml
        self.name = name
        self.level = level
        self.initiative = initiative
        self.card_ID = ID
        self.top_text = top_text
        self.bot_text = bot_text
        self.class_color = class_color # Given by the Haven class. Shouldn't be modified.

        # The top and bot areas are dictionnaries holding TopmostColumnItems. This pairs AbstractTopMostColumnItems to
        # their position on the card (top, bottom, center).
        self.top_areas = {"topleft": None,
                          "bottomright": None,
                          "center": []}
        self.bot_areas = {"topleft": None,
                          "bottomright": None,
                          "center": []}

    # Virtual methods
    def parse_gml(self, parser: AbstractParser, raw_user_aliases: str =""):
        """
        Parse the top text and bottom text and return a list of warnings which should be displayed to the end-user.
        Child classes must overload this function so that the GUI doesn't have to give an instance of the parser:
        it should simply call AbstractCard.parse_gml()

        A note on user aliases: these are not a member of AbstractCard to reduce duplicates. Instead, they are a member
        of AbstractHavenClass and should ALWAYS be passed as argument to the AbstractCard.parse_gml function. This also means that a
        card can parse itself (ie we can always call card.parse_gml()), but the result might not be same as if it was the
        HavenClass which called the parsing, since user aliases will be ignored.
        Conclusion: always parse through the AbstractHavenClass and NEVER parse a card directly.
        """
        # Populate self.top_areas
        column_dict, top_warnings = parser.parse(self.top_text, class_color=self.class_color, additional_aliases=raw_user_aliases)
        self.top_areas = {"topleft" : column_dict["topleft"],
                          "bottomright" : column_dict["bottomright"],
                        }
        center = [column_dict["center"]]
        if len(column_dict["center2"].items) > 0:
            center.append(column_dict["center2"])
        self.top_areas["center"] = center
        # Populate self.bot_areas
        column_dict, bot_warnings = parser.parse(self.bot_text, class_color=self.class_color, additional_aliases=raw_user_aliases)
        self.bot_areas = {"topleft" : column_dict["topleft"],
                          "bottomright" : column_dict["bottomright"],
                        }
        center = [column_dict["center"]]
        if len(column_dict["center2"].items) > 0:
            center.append(column_dict["center2"])
        self.bot_areas["center"] = center

        return top_warnings + bot_warnings

    def draw(self, cr : cairo.Context):
        """
        Draw the card on the given cairo context. AbstractCard.parse_gml should always be called before calling this method.
        This method must be overloaded by child classes.
        """
        pass

    # Interface with the UI
    def save(self):
        """
        Save this card to the GML file at location self.path_to_gml. Only appends text, doesn't overwrite.
        """
        if len(self.name) !=0: # Sanity check to make sure we don't break the GML file and make it unreadable

            parameters = {}
            if len(self.level) > 0:
                parameters["level"] = self.level
            if len(self.initiative) > 0:
                parameters["initiative"] = self.initiative
            if len(self.card_ID) > 0:
                parameters["ID"] = self.card_ID

            with open(self.path_to_gml, 'a') as file:
                if len(parameters) > 0:
                    # Just cosmetic purposes: don't add empty fields.
                    safe_dump({self.name: parameters}, file, sort_keys=False)
                else:
                    file.write(f"{self.name}:")
                    file.write("\n")

                # We write directly the top and bottom action, because yaml's dumping of multiline strings is
                # wayyyy too inconsistent. Would probably require hacking deep yaml functions, which is not the way to go.
                # Chomping methods (keep (|+) and strip (|-))
                # - if the text is "something" -> becomes "|- something" (should be "| something")
                # - if the text is "something\n" -> becomes "| something" (should be "|- something")
                # Tabulations: breaks everything
                # - "a \n b" is rendered on 2 lines
                # - "a \n \t b" is rendered on 1 line
                # Note: https://stackoverflow.com/questions/8640959/how-can-i-control-what-scalar-form-pyyaml-uses-for-my-data
                # The example replacing BaseRepresenter.represent_scalar = my_represent_scalar could work!
                # However, it means we have to create a custom representer and a custom dumper, which is very internal
                # to yaml: it's probably not a good idea to do this as the internals could change.

                tabulation_character = "  "
                splitted = self.top_text.split("\n")
                if len(self.top_text) > 0:
                    file.write(tabulation_character + "top: |2")
                    file.write("\n")
                    for line in splitted:
                        file.write(2*tabulation_character + line.rstrip()) # Don't strip, or you will remove indentation!
                        file.write("\n")
                splitted = self.bot_text.split("\n")
                if len(self.bot_text) > 0:
                    file.write(tabulation_character + "bottom: |2")
                    file.write("\n")
                    for line in splitted:
                        file.write(2*tabulation_character + line.rstrip()) # Same as above.
                        file.write("\n")

    def replace_text(self, text: str, is_top_text: bool):
        """
        Try to replace the current top (or bottom) text with the given one.
        Returns True if the text was indeed different (ie if text is different from self.top_text), and False if nothing
        was changed.
        This function is the interface between the user's raw input and what will be serialised later on in the GML file.
        Currently, it:
        - removes leading empty lines and trailing white blanks. It does not remove the indentation (if it exists) of the first line.
        - replace tabs by two spaces
        """
        # Keep only lines which are not empty or full of blanks, but do NOT remove leading or trailing blanks.
        stripped_text = "\n".join([line for line in text.split("\n") if line.strip()])
        stripped_text = stripped_text.rstrip() # Remove trailing blanks but keep leading (might be indentation for the first line)
        stripped_text = stripped_text.replace("\t", "  ")

        if is_top_text:
            if stripped_text == self.top_text:
                return False
            else:
                self.top_text = stripped_text
                return True
        else:
            if stripped_text == self.bot_text:
                return False
            else:
                self.bot_text = stripped_text
                return True
