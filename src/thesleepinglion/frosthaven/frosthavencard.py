import cairo

from ..core.abstractcard import AbstractCard
from ..core.items import TextItem
from .frosthaven_items import FHTopmostColumnItem
from .frosthavenlinecontext import FrosthavenLineContext
from .frosthaven_constants import *
from .frosthavenparser import FrosthavenParser

class FrosthavenCard(AbstractCard):
    """
    A card using Frosthaven format.
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
        super().__init__(path_to_gml, name, level, initiative, ID, top_text, bot_text, class_color)
        self.top_areas = {"topleft": FHTopmostColumnItem([], FrosthavenLineContext(), self.path_to_gml),
                          "bottomright": FHTopmostColumnItem([], FrosthavenLineContext(), self.path_to_gml),
                          "center": []}
        self.bot_areas = {"topleft": FHTopmostColumnItem([], FrosthavenLineContext(), self.path_to_gml),
                          "bottomright": FHTopmostColumnItem([], FrosthavenLineContext(), self.path_to_gml),
                          "center": []}

    def parse_gml(self, raw_user_aliases: str = ""):
        parser = FrosthavenParser(self.path_to_gml)
        return super().parse_gml(parser, raw_user_aliases)

    def draw(self, cr: cairo.Context):
        # Name
        name_item = TextItem([self.name], FrosthavenLineContext(font = fh_title_font,
                                                                font_size = fh_title_font_size,
                                                                text_color = {"red": 0, "green": 0, "blue": 0}))
        cr.save()
        cr.translate(0.5*fh_card_width - name_item.get_width()/2, 0.09*fh_card_height - name_item.get_height()/2)
        cr.move_to(0,0)
        name_item.draw(cr)
        cr.restore()

        # Level
        level_item = TextItem([self.level], FrosthavenLineContext(font = fh_level_font, font_size = fh_level_font_size,
                                                                  text_color = {"red": 0, "green": 0, "blue": 0}))
        cr.save()
        cr.translate(0.117*fh_card_width - level_item.get_width()/2, 0.09*fh_card_height - level_item.get_height()/2)
        cr.move_to(0,0)
        level_item.draw(cr)
        cr.restore()

        # Initiative
        init_item = TextItem([self.initiative], FrosthavenLineContext(font = fh_init_font, font_size = fh_init_font_size))
        cr.save()
        cr.translate(0.5*fh_card_width - init_item.get_width()/2, 0.53*fh_card_height - init_item.get_height()/2)
        cr.move_to(0,0)
        init_item.draw(cr)
        cr.restore()

        # Card ID
        ID_col = TextItem([self.card_ID], FrosthavenLineContext(font = fh_card_ID_font, font_size = fh_card_ID_font_size, bold = True))
        cr.save()
        cr.translate(0.15*fh_card_width - ID_col.get_width()/2, 0.93*fh_card_height - ID_col.get_height()/2) # Center the ID at y = 0.9*card_height
        cr.move_to(0,0)
        ID_col.draw(cr)
        cr.restore()


        card_drawing_height = 0.35*fh_card_height
        # Top action
        cr.save()
        cr.translate((fh_card_width - card_drawing_width)/2, 0.13*fh_card_height) # Card's top left corner
        cr.move_to(0,0)
        if len(self.top_areas["center"]) > 0: #TODO: add other columns
            cr.translate((card_drawing_width - self.top_areas["center"][0].get_width())/2,
                         (card_drawing_height - self.top_areas["center"][0].get_height())/2)
            cr.move_to(0,0)
            self.top_areas["center"][0].draw(cr)
        cr.restore()
        # Bottomright
        cr.save()
        # Translate to the rightmost corner of the card
        cr.translate((fh_card_width - card_drawing_width)/2 + card_drawing_width, 0.533*fh_card_height)
        right_column = self.top_areas["bottomright"]
        cr.translate(-right_column.get_width(), -right_column.get_height())
        cr.move_to(0,0)
        right_column.draw(cr)
        cr.restore()

        # Bottom action
        cr.save()
        cr.translate((fh_card_width - card_drawing_width)/2, 0.575*fh_card_height)
        cr.move_to(0,0)
        if len(self.bot_areas["center"]) > 0: #TODO: add other columns
            cr.translate((card_drawing_width - self.bot_areas["center"][0].get_width())/2,
                         (card_drawing_height - self.bot_areas["center"][0].get_height())/2)
            cr.move_to(0,0)
            self.bot_areas["center"][0].draw(cr)
        cr.restore()
