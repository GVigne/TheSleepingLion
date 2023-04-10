import cairo
from .constants import *
from .items import ColumnItem, LineItem, TextItem
from .commands import *
from .gloomhavenparser import GloomhavenParser
from .gmllinecontext import GMLLineContext
from yaml import safe_dump

class Card:
    """
    A class to represent a Card. Can draw a top and a bottom action, as well as card-specific elements such
    as the initiative, name, level...
    """
    def __init__(self,
                path_to_gml,
                name : str,
                level : str,
                initiative : str,
                ID : str,
                top_text : str,
                bot_text : str,
                color: dict,
                raw_aliases: str =""):
        self.path_to_gml = path_to_gml
        self.name = name
        self.level = level
        self.initiative = initiative
        self.card_ID = ID
        self.top_text = top_text
        self.bot_text = bot_text
        self.color = color # Card color, given by the gloomhaven class. Shouldn't be modified.
        self.raw_aliases = raw_aliases # User-defined aliases

        # The top and bot areas are dictionnaries holding ColumnItems. This pairs ColumnItems to their position
        # on the card (top, bottom, center). They will be filled by self.parse_gml.
        self.top_areas = {"topleft": ColumnItem([], self.path_to_gml),
                          "bottomright": ColumnItem([], self.path_to_gml),
                          "center": []}
        self.bot_areas = {"topleft": ColumnItem([], self.path_to_gml),
                          "bottomright": ColumnItem([], self.path_to_gml),
                          "center": []}

    def parse_gml(self):
        """
        Parse the top text and bottom text.
        Return a list of warnings which should be displayed to the end-user.
        """
        parser = GloomhavenParser(self.path_to_gml)
        column_dict, top_warnings = parser.parse(self.top_text, background_color=self.color, additional_aliases=self.raw_aliases)
        self.top_areas = {"topleft" : column_dict["topleft"],
                          "bottomright" : column_dict["bottomright"],
                        }
        center = [column_dict["center"]]
        if len(column_dict["center2"].items) > 0:
            center.append(column_dict["center2"])
        self.top_areas["center"] = center

        column_dict, bot_warnings = parser.parse(self.bot_text, background_color=self.color, additional_aliases=self.raw_aliases)
        self.bot_areas = {"topleft" : column_dict["topleft"],
                          "bottomright" : column_dict["bottomright"],
                        }
        center = [column_dict["center"]]
        if len(column_dict["center2"].items) > 0:
            center.append(column_dict["center2"])
        self.bot_areas["center"] = center

        return top_warnings + bot_warnings

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

    def draw(self, cr : cairo.Context):
        """
        Draw the card on the given cairo context.
        Warning: self.parse should always be called before calling this function. However, even if the parsing
        fails draw can be called. The result may not be pretty, but it will not break.
        """
        # Name
        name_col = TextItem(self.name, GMLLineContext(font = title_font, font_size = title_font_size))
        cr.save()
        cr.translate(card_width/2 - name_col.get_width()/2, 0) # Center the middle of the line to the middle of the card
        cr.translate(0, 0.08*card_height - name_col.get_height()/2) # Center the name at y = 0.08*card_height
        cr.move_to(0,0)
        name_col.draw(cr)
        # Go back to the original position
        cr.restore()

        # Level
        # TODO: should be in black
        level_col = TextItem(self.level, GMLLineContext(font = title_font, font_size = 0.7*title_font_size))
        cr.save()
        cr.translate(card_width/2 - level_col.get_width()/2, 0) # Center the middle of the line to the middle of the card
        cr.translate(0, 0.1325*card_height - level_col.get_height()/2) # Center the level at y = 0.1325*card_height
        cr.move_to(0,0)
        level_col.draw(cr)
        # Go back to the original position
        cr.restore()

        # Initiative
        init_col = TextItem(self.initiative, GMLLineContext(font = title_font, font_size = 1.6*title_font_size))
        cr.save()
        cr.translate(card_width/2 - init_col.get_width()/2, 0) # Center the middle of the line to the middle of the card
        cr.translate(0, 0.535*card_height - init_col.get_height()/2) # Center the initiative at y = 0.535*card_height
        cr.move_to(0,0)
        init_col.draw(cr)
        # Go back to the original position
        cr.restore()

        # ID
        ID_col = TextItem(self.card_ID, GMLLineContext(font = card_ID_font, font_size = card_ID_font_size, bold = True))
        cr.save()
        cr.translate(card_width/2 - ID_col.get_width()/2 + 0.1*card_width, 0) # Center the middle of the line to the middle of the card +  a small offset
        cr.translate(0, 0.9*card_height - ID_col.get_height()/2) # Center the ID at y = 0.9*card_height
        cr.move_to(0,0)
        ID_col.draw(cr)
        # Go back to the original position
        cr.restore()
        cr.move_to(0,0)

        # Actions
        total_area_width = card_width*0.78
        total_area_height = card_height*0.3

        ## Move on to the top part of the card
        # Draw the top left column
        cr.save()
        cr.translate(0.11*card_width, 0.15*card_height)
        cr.move_to(0,0)
        left_column = self.top_areas["topleft"]
        left_column.draw(cr)
        cr.restore() # Go back to the topleft corner of the card
        ## Now draw the main body of the card. We try to even out the margins between the columns.
        cr.translate(0.11*card_width, 0.17*card_height)
        cr.move_to(0,0)
        pro_rata = 0
        n = len(self.top_areas["center"])
        if n > 0:
            # Divide by n+1 because we want a blank before the first column.
            pro_rata = (total_area_width - sum([da.get_width() for da in self.top_areas["center"]])) / (n+1)
        cr.save()
        for (i, drawing_area) in enumerate(self.top_areas["center"]):
            cr.translate(pro_rata, 0)
            cr.save()
            cr.translate(0,total_area_height/2 - drawing_area.get_height()/2)
            drawing_area.draw(cr) #The drawing area should put the cursor back where it initially was
            cr.restore() # Undo the y-translation
            cr.translate(drawing_area.get_width(), 0)
            cr.move_to(0,0)
        cr.restore()
        ## Finally, the last column on the botright part
        cr.move_to(0,0)
        right_column = self.top_areas["bottomright"]
        cr.save()
        cr.translate(total_area_width - right_column.get_width(), total_area_height - right_column.get_height())
        cr.translate(0, 0.03*card_height)
        right_column.draw(cr)
        cr.restore()
        cr.move_to(0,0)

        ## Move on to the bottom part of the card
        cr.translate(0, 0.42*card_height) #Top of the bot part of the card
        ## Draw a first column item in the topleft part.
        cr.move_to(0,0)
        left_column = self.bot_areas["topleft"]
        cr.save()
        left_column.draw(cr)
        cr.restore()
        cr.move_to(0,0)
        ## Now draw the main body of the card. We try to even out the margins between the columns.
        pro_rata = 0
        n = len(self.bot_areas["center"])
        if n > 0:
            # Divide by n+1 because we want a blank before the first column.
            pro_rata = (total_area_width - sum([da.get_width() for da in self.bot_areas["center"]])) / (n+1)
        cr.save()
        for (i, drawing_area) in enumerate(self.bot_areas["center"]):
            cr.translate(pro_rata, 0)
            cr.save()
            cr.translate(0,total_area_height/2 - drawing_area.get_height()/2)
            drawing_area.draw(cr) #The drawing area should put the cursor back where it initially was
            cr.restore() # Undo the y-translation
            cr.translate(drawing_area.get_width(), 0)
            cr.move_to(0,0)
        cr.restore()
        ## Finally, the last column on the botright part
        cr.move_to(0,0)
        right_column = self.bot_areas["bottomright"]
        cr.save()
        cr.translate(total_area_width - 0.06*card_width - right_column.get_width(),
                    total_area_height - right_column.get_height())
        right_column.draw(cr)
        cr.restore()
        cr.move_to(0,0)

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
        # Keepn only lines which are not empty or full of blanks, but do NOT remove leading or trailing blanks.
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
