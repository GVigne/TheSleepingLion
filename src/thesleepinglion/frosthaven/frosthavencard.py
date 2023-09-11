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
        name_col = TextItem([self.name], FrosthavenLineContext(font = fh_title_font, font_size = fh_title_font_size))
        cr.save()
        cr.translate(fh_card_width/2 - name_col.get_width()/2, 0) # Center the middle of the line to the middle of the card
        cr.translate(0, 0.08*fh_card_height - name_col.get_height()/2) # Center the name at y = 0.08*card_height
        cr.move_to(0,0)
        name_col.draw(cr)
        # Go back to the original position
        cr.restore()

        # Level
        # TODO: should be in black
        level_col = TextItem([self.level], FrosthavenLineContext(font = fh_title_font, font_size = 0.7*fh_title_font_size))
        cr.save()
        cr.translate(fh_card_width/2 - level_col.get_width()/2, 0) # Center the middle of the line to the middle of the card
        cr.translate(0, 0.1325*fh_card_height - level_col.get_height()/2) # Center the level at y = 0.1325*card_height
        cr.move_to(0,0)
        level_col.draw(cr)
        # Go back to the original position
        cr.restore()

        # Initiative
        init_col = TextItem([self.initiative], FrosthavenLineContext(font = fh_title_font, font_size = 1.6*fh_title_font_size))
        cr.save()
        cr.translate(fh_card_width/2 - init_col.get_width()/2, 0) # Center the middle of the line to the middle of the card
        cr.translate(0, 0.535*fh_card_height - init_col.get_height()/2) # Center the initiative at y = 0.535*card_height
        cr.move_to(0,0)
        init_col.draw(cr)
        # Go back to the original position
        cr.restore()

        # Top action
        if len(self.top_areas["center"]) > 0:
            cr.save()
            cr.translate(0.11*fh_card_width, 0.17*fh_card_height)
            cr.translate(fh_card_width*0.78/2 - self.top_areas["center"][0].get_width()/2, 0)
            cr.move_to(0,0)
            self.top_areas["center"][0].draw(cr)
            cr.restore()
