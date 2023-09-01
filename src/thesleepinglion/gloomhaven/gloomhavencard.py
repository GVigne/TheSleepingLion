import cairo

from ..core.abstractcard import AbstractCard
from ..core.items import TextItem
from .gloomhaven_items import GHTopmostColumnItem
from .gloomhavenparser import GloomhavenParser
from .gloomhavenlinecontext import GloomhavenLineContext
from .gloomhaven_constants import *

class GloomhavenCard(AbstractCard):
    """
    A card using Gloomhaven format.
    """
    def __init__(self,
                path_to_gml,
                name: str,
                level: str,
                initiative: str,
                ID: str,
                top_text: str,
                bot_text: str,
                class_color: dict,
                raw_user_aliases: str = ""):
        super().__init__(path_to_gml, name, level, initiative, ID, top_text, bot_text, class_color, raw_user_aliases)
        self.top_areas = {"topleft": GHTopmostColumnItem([], None, self.path_to_gml),
                          "bottomright": GHTopmostColumnItem([], None, self.path_to_gml),
                          "center": []}
        self.bot_areas = {"topleft": GHTopmostColumnItem([], None, self.path_to_gml),
                          "bottomright": GHTopmostColumnItem([], None, self.path_to_gml),
                          "center": []}

    def parse_gml(self):
        parser = GloomhavenParser(self.path_to_gml)
        return super().parse_gml(parser)

    def draw(self, cr : cairo.Context):
        """
        Draw the card on the given cairo context.
        Warning: self.parse should always be called before calling this function. However, even if the parsing
        fails draw can be called. The result may not be pretty, but it will not break.
        """
        # Name
        name_col = TextItem([self.name], GloomhavenLineContext(font = title_font, font_size = title_font_size))
        cr.save()
        cr.translate(card_width/2 - name_col.get_width()/2, 0) # Center the middle of the line to the middle of the card
        cr.translate(0, 0.08*card_height - name_col.get_height()/2) # Center the name at y = 0.08*card_height
        cr.move_to(0,0)
        name_col.draw(cr)
        # Go back to the original position
        cr.restore()

        # Level
        # TODO: should be in black
        level_col = TextItem([self.level], GloomhavenLineContext(font = title_font, font_size = 0.7*title_font_size))
        cr.save()
        cr.translate(card_width/2 - level_col.get_width()/2, 0) # Center the middle of the line to the middle of the card
        cr.translate(0, 0.1325*card_height - level_col.get_height()/2) # Center the level at y = 0.1325*card_height
        cr.move_to(0,0)
        level_col.draw(cr)
        # Go back to the original position
        cr.restore()

        # Initiative
        init_col = TextItem([self.initiative], GloomhavenLineContext(font = title_font, font_size = 1.6*title_font_size))
        cr.save()
        cr.translate(card_width/2 - init_col.get_width()/2, 0) # Center the middle of the line to the middle of the card
        cr.translate(0, 0.535*card_height - init_col.get_height()/2) # Center the initiative at y = 0.535*card_height
        cr.move_to(0,0)
        init_col.draw(cr)
        # Go back to the original position
        cr.restore()

        # ID
        ID_col = TextItem([self.card_ID], GloomhavenLineContext(font = card_ID_font, font_size = card_ID_font_size, bold = True))
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
        blank_space_width = TextItem([" "], GloomhavenLineContext()).get_width()

        ## Move on to the top part of the card
        # Draw the top left column
        left_column = self.top_areas["topleft"]
        cr.save()
        cr.translate(0.11*card_width, 0.15*card_height)
        cr.move_to(0,0)
        self.draw_black_banner_background(cr, total_area_width, left_column)
        cr.translate(blank_space_width, 0) # Add some space so top left column isn't immediately next to the card's border
        cr.move_to(0,0)
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
        # Create a list holding the x coordinates of all of the top left corners of the items in self.top_areas[center]
        anchor_points = []
        x = 0
        for (i, drawing_area) in enumerate(self.top_areas["center"]):
            x += pro_rata
            anchor_points.append(x)
            x += drawing_area.get_width()
        # Drawing part
        for (i, drawing_area) in enumerate(self.top_areas["center"]):
            cr.save()
            cr.translate(0,total_area_height/2 - drawing_area.get_height()/2) # Y-translation
            cr.move_to(0,0)
            self.draw_black_banner_background(cr, total_area_width, drawing_area)
            cr.translate(anchor_points[i], 0)
            cr.move_to(0,0)
            drawing_area.draw(cr)
            cr.restore() # Go back to the top left corner of the card
        ## Finally, the last column on the botright part
        cr.move_to(0,0)
        right_column = self.top_areas["bottomright"]
        cr.save()
        # Y-translation
        cr.translate(0, total_area_height - right_column.get_height())
        cr.translate(0, 0.03*card_height) # Get below the initiative level
        self.draw_black_banner_background(cr, total_area_width, right_column)
        # X-translation
        cr.translate(total_area_width - right_column.get_width() - blank_space_width, 0)
        right_column.draw(cr)
        cr.restore()
        cr.move_to(0,0)

        ## Move on to the bottom part of the card
        cr.translate(0, 0.42*card_height) #Top of the bot part of the card
        cr.move_to(0,0)
        ## Draw a first column item in the topleft part.
        left_column = self.bot_areas["topleft"]
        cr.save()
        self.draw_black_banner_background(cr, total_area_width, left_column)
        cr.translate(blank_space_width, 0)
        cr.move_to(0,0)
        left_column.draw(cr)
        cr.restore()
        ## Now draw the main body of the card. We try to even out the margins between the columns.
        pro_rata = 0
        n = len(self.bot_areas["center"])
        if n > 0:
            # Divide by n+1 because we want a blank before the first column.
            pro_rata = (total_area_width - sum([da.get_width() for da in self.bot_areas["center"]])) / (n+1)
        # Create a list holding the x coordinates of all of the top left corners of the items in self.bot_areas[center]
        anchor_points = []
        x = 0
        for (i, drawing_area) in enumerate(self.bot_areas["center"]):
            x += pro_rata
            anchor_points.append(x)
            x += drawing_area.get_width()
        # Drawing part
        for (i, drawing_area) in enumerate(self.bot_areas["center"]):
            cr.save()
            cr.translate(0,total_area_height/2 - drawing_area.get_height()/2) # Y-translation
            cr.move_to(0,0)
            self.draw_black_banner_background(cr, total_area_width, drawing_area)
            cr.translate(anchor_points[i], 0)
            cr.move_to(0,0)
            drawing_area.draw(cr)
            cr.restore() # Go back to the top left corner of the card
        ## Finally, the last column on the botright part
        cr.move_to(0,0)
        right_column = self.bot_areas["bottomright"]
        cr.save()
        # Y-translation
        cr.translate(0, total_area_height - right_column.get_height())
        self.draw_black_banner_background(cr, total_area_width, right_column)
        # X-translation
        # There is a border on the bottom part of the card which isn't there for the top actions, so we need to have an extra offset
        cr.translate(total_area_width - 0.06*card_width - right_column.get_width() - blank_space_width, 0)
        right_column.draw(cr)
        cr.restore()
        cr.move_to(0,0)

    def draw_black_banner_background(self,
                                    cr : cairo.Context,
                                    area_width : int,
                                    column_item: GHTopmostColumnItem):
        """
        Draw a black banner at every position given by the column_item.
        """
        banners = column_item.black_banner_coordinates()
        for banner_info in banners:
            cr.rectangle(0, banner_info["y-position"], area_width, banner_info["height"])
            cr.set_source_rgba(0,0,0,0.5)
            cr.fill()
