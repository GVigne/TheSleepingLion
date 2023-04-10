import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, GdkPixbuf
from yaml import safe_load, safe_dump

from .constants import *
from .gmllinecontext import GMLLineContext
from .background_code.create_card_background import create_card_background
from .commands import ImageCommand
from .svg_wrapper import SVGImage
from .items import LineItem, TextItem
from .errors import ImageNotFound, InvalidGMLFile
from .card import Card
from .utils import get_image, check_aliases_integrity
from pathlib import Path

class GloomhavenClass:
    """
    A class to represent a character in Gloomhaven. This is the main entry point to parse a GML file.
    A GloomhavenClass should be able to extract the different fields of a GML file and give them to other classes
    (ex: the text in top and bottom to a Card).
    """
    @staticmethod
    def CreateFromFile(path_to_gml: Path):
        """
        Note: path_to_gml MUST be a Path object, not a string.
        """
        return GloomhavenClass(path_to_gml)

    def __init__(self, path_to_gml : Path):
        self.path_to_gml = path_to_gml
        self.raw_aliases = "" # Raw text describing the custom aliases
        self.name = None
        self.path_to_icon = None
        self.color = {"red": None, "green": None, "blue": None}
        self.cards = [] # List of Cards
        self.card_background = None # A GdkPixbuf with the correct background color.
        self.redraw_background = True # A flag allowing us to save some computational time (don't always compute the background)

        try:
            with open(self.path_to_gml, "r") as f:
                self.python_gml = safe_load(f)
        except Exception as e:
            raise InvalidGMLFile
        if self.python_gml is None:
            # The file is empty. An empty file is a valid GML file.
            self.python_gml = {}

        if "class" not in self.python_gml:
            # Should we raise a warning for the user? It's not normal for a GML file not to have a class section.
            self.python_gml["class"] = {}
        # Try to get the name, path ... from the class section. If it isn't there (the user didn't specify it)
        # then instead have the names, paths... be empty strings.
        self.name = self.python_gml["class"].get("name", "")
        self.path_to_icon = self.python_gml["class"].get("path_to_icon", "")

        color = self.python_gml["class"].get("color", "")
        try:
           red, green, blue = color.split(",")
           red, green, blue = int(red), int(green), int(blue)
        except Exception as e:
            # Something went wrong, couldn't extract three colors from GML
            red, green, blue = 0,0,0
        self.color["red"], self.color["green"], self.color["blue"] = red, green, blue

        try:
            self.raw_aliases = self.python_gml["aliases"].strip()
        except Exception as e:
            # aliases not found
            pass

        self.cards_from_gml()

    def save(self):
        """
        Save this gloomhaven class at location self.path_to_gml. Overwrite everything there.
        """
        color = f'{int(self.color["red"])}, {int(self.color["green"])}, {int(self.color["blue"])}'
        class_description = {"class" : {"name" : self.name,
                                        "color" : color}}
        if self.path_to_icon is not None and len(self.path_to_icon) > 0:
            # path_to_icon is not empty, it is a path to some image (valid or not)
            class_description["class"]["path_to_icon"] = self.path_to_icon
        with open(self.path_to_gml, 'w') as file:
            # Save the aliases: this is done similarly as in card.save
            tabulation_character = "  "
            splitted = self.raw_aliases.split("\n")
            if len(self.raw_aliases) > 0:
                file.write("aliases: |")
                file.write("\n")
                for line in splitted:
                    file.write(tabulation_character + line.rstrip()) # Don't strip, or you will remove indentation!
                    file.write("\n")

            # We try to prettify the output, so it is still easily readable by a human. Therefore we:
            #   - dump the dictionnary without sorting keys alphabetically (most important key is first)
            #   - add a new line after the class description.
            safe_dump(class_description, file, default_flow_style=False, sort_keys=False)
            file.write("\n")

        for card in self.cards:
            card.save()

    def update_color(self, red: int, green: int, blue: int):
        """
        Set the RGB for the card background to the given values. Return True if the new values are different
        from the old one (and so if something really is modified)

        Internally, if the new values are different from the old one, raise a flag meaning the card background
        should be recomputed.
        """
        if red != self.color["red"] or green != self.color["green"] or blue != self.color["blue"]:
            self.color["red"], self.color["green"], self.color["blue"] = red, green, blue
            self.redraw_background = True
            return True
        return False

    def update_user_aliases(self, new_aliases):
        """
        Change the custom aliases defined by the user.

        Internally, this means propagating the new aliases to the cards.
        """
        self.raw_aliases = new_aliases
        for card in self.cards:
            card.raw_aliases = new_aliases

    def draw_card(self, card : Card|None, cr):
        """
        Draw the required card on the given cairo context.
        If no card with the given name exist (for example, if the cards weren't parsed) or if card_name is None,
        only draw the card background.
        """
        self.create_card_layout(cr) # Build the class-dependent background and draw it on the cairo context.
        if card is not None:
            card.draw(cr)

    def check_class_errors(self):
        """
        Check for errors in what the user defined at a class level. Return errors and warnings as lists of
        strings (the errors/warnings raised).
        This should ALWAYS be called when parsing the GML file. This is part of the parsing process, and may fail
        just as any other part.
        """
        class_warnings = []
        if len(self.path_to_icon) >0:
            icon_image = ImageCommand([self.path_to_icon], GMLLineContext(), path_to_gml=self.path_to_gml)
            class_warnings += icon_image.warnings
        class_errors = check_aliases_integrity(self.raw_aliases)
        return class_errors, class_warnings

    def create_card_layout(self, cr):
        """
        Draw the general layout of a card:
            -background
            -class item
            -crown where the level will be
            -base actions (Move 2 and Attack 2)
            -arrow above the initiative
        """
        if self.redraw_background:
            self.card_background = create_card_background(self.color["red"], self.color["green"], self.color["blue"]) # Dark magic happens, but I have my image
            self.redraw_background = False
        # Either card_background has been generated, or it was already generated, and we reuse it.

        Gdk.cairo_set_source_pixbuf(cr, self.card_background.scale_simple(card_width, card_height, GdkPixbuf.InterpType.NEAREST),0,0)
        cr.paint()

        # The height corresponds to 0.8*1.4*base_font_size. Note that 1.4 scaling comes from the ImageCommand.
        crown = SVGImage(get_image(self.path_to_gml, "crown.svg"), height = 1.12*base_font_size, new_color = self.color)
        cr.save()
        cr.translate(card_width/2 - crown.get_width() /2, 0.105*card_height)
        cr.move_to(0,0)
        crown.draw(cr)
        # Go back to the original position
        cr.restore()

        # Even on real cards, the attack and move image is a bit bigger than their small font counterpart.
        attack = ImageCommand(["attack.svg"], GMLLineContext(font_size = 1.05*small_font_size))
        move = ImageCommand(["move.svg"], GMLLineContext(font_size = 1.05*small_font_size))
        two = TextItem("2", GMLLineContext(font=title_font, font_size = small_font_size))

        # We need to aline manually the glyphs as they do not have the base font size.
        cr.save()
        cr.translate(0.134* card_width, 0.485*card_height)
        cr.move_to(0,0)
        attack.draw(cr)
        cr.translate(attack.get_width(), - 0.15*attack.get_height())
        two.draw(cr)
        cr.restore()
        # Same as above
        cr.save()
        cr.translate(0.134* card_width, 0.545*card_height)
        move.draw(cr)
        cr.translate(move.get_width(), - 0.15*move.get_height())
        two.draw(cr)
        cr.restore() # Go back to the top of the page.

        if len(self.path_to_icon) > 0:
            # The user gave a class icon
            icon = ImageCommand([self.path_to_icon],
                                GMLLineContext(font_size =0.8*title_font_size),
                                path_to_gml=self.path_to_gml)
            icon_line = LineItem([icon])
            cr.save()
            cr.translate(0.5*card_width - icon_line.get_width() / 2, 0.9*card_height)
            cr.move_to(0,0)
            icon_line.draw(cr)
            # Go back to the original position
            cr.restore()

    def valid_rename(self, card_name: str, existing_card: Card|None):
        """
        Return a valid name for a card. This can be the same as card_name.
        - If existing_card is None, return card_name if no card has this name, else pick another one.
        - If existing_card is not None, return card_name if no other card has this name, else pick another one.
        If we should pick another name, it will be something like "Card 42".
        Note: some card names are also blacklisted (already used for fields in GML). Furthermore, a name may not have
        an empty name.
        """
        matching_card = None
        for card in self.cards:
            if card.name == card_name:
                if existing_card is None or card != existing_card:
                    matching_card = card
                    # We assume that there can only be at most one card with the name card_name.
                    break

        blacklisted = ["class", "aliases", "special rules"]
        empty_name =  not card_name.strip() # An empty string evaluates to False

        if matching_card is not None or card_name in blacklisted or empty_name:
            # Replace card_name with something like "Card 1", "Card 2"...
            existing_indices = []
            for card in self.cards:
                try:
                    index = int(card.name.split(" ")[-1])
                    existing_indices.append(index)
                except Exception:
                    pass
            # Ex: if names are ["Fire Orbs", "Card 3", "Card 4"], then card_name should be "Card 1".
            # But if names are ["Fire Orbs", "Card 1", "Card 2"], then card_name should be "Card 3"
            i = 1
            while True:
                if i not in existing_indices:
                    break
                i += 1

            card_name = f"Card {i}"

        return card_name

    def create_blank_card(self):
        """
        Create and return a new blank card (ie it only has a name, chosen by the class).
        """
        card_name = self.valid_rename("Card 1", None)
        card = Card(self.path_to_gml, card_name, "", "", "", "", "", self.color, raw_aliases= self.raw_aliases)
        self.cards.append(card)
        return card

    def cards_from_gml(self):
        """
        Populate self.cards with the correct instances of Card objects. This doesn't do any parsing.
        """
        for i, (card_name, instructions) in enumerate(self.python_gml.items()):
            if card_name !="class" and card_name !="aliases":
                if instructions is None:
                    # If the user only gives the card name, there is no reason for the parser to fail.
                    # For compatibility, treat the instructions as if they are empty.
                    instructions = {}
                # Try to get each field from the GML file: if this fails, have them be empty strings instead
                level = instructions.get("level","")
                card_id = instructions.get("ID","")
                level = str(level)
                card_id = str(card_id)

                initiative = instructions.get("initiative","")
                if isinstance(initiative, float) or isinstance(initiative, int):
                    initiative = f"{initiative:02d}"

                # Convert the name of the card into a string
                try:
                    card_name = str(card_name)
                except Exception as e:
                    card_name = ""

                # We need to deal with 2 cases:
                    # instructions["top"] does not exists
                    # instructions["top"] exists but is empty: in this case, instructions["top"] is None
                top_text = instructions.get("top","")
                if top_text is None:
                    top_text = ""
                # Same for instructions["bottom"]
                bot_text = instructions.get("bottom","")
                if bot_text is None:
                    bot_text = ""
                self.cards.append(Card(self.path_to_gml, card_name, level, initiative,
                                       card_id, top_text, bot_text, self.color, raw_aliases = self.raw_aliases))

    def parse_gml(self):
        """
        Parse the top and bottom actions for every card. Return errors as a dictionnary with keys being the name
        of the cards, and values being the error raised.
        """
        parsing_errors = {}
        all_warnings = {}
        for card in self.cards:
            try:
                warnings = card.parse_gml()
                if len(warnings) > 0:
                    all_warnings[card.name] = warnings
            except Exception as e:
                parsing_errors[card.name] = str(e)
        class_errors, class_warnings = self.check_class_errors()
        if len(class_errors) >0:
            # We can't really use a string here, as it could be the name of a card. It's just a convention
            parsing_errors[None] = class_errors
        if len(class_warnings) >0:
            all_warnings[None] = class_warnings
        return parsing_errors, all_warnings

    def delete_card(self, card: Card):
        """
        Delete the given card
        """
        self.cards = [ca for ca in self.cards if ca != card]

    def set_path_to_gml(self, new_path: Path):
        """
        Set the path to gml file to the new given path.
        """
        self.path_to_gml = new_path
        for card in self.cards:
            card.path_to_gml = new_path
