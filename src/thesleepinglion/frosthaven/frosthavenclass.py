from pathlib import Path
import cairo
import gi
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gdk, GdkPixbuf

from ..core.abstracthavenclass import AbstractHavenClass
from ..core.utils import color_string_to_dict
from ..core.items import LineItem, TextItem
from ..background_code.fh_create_card_background import fh_generate_card_background
from .frosthavencard import FrosthavenCard
from .frosthaven_constants import *
from .frosthaven_items import FrosthavenImage
from .frosthavenlinecontext import FrosthavenLineContext

class FrosthavenClass(AbstractHavenClass):
    def __init__(self, path_to_gml: Path):
        super().__init__(path_to_gml, FrosthavenCard)
        # 4 different colors can be used to draw a frosthaven card's background.
        # self.color corresponds to the primary color (background). Here we define the three others
        self.title_border_color = {"red": 255, "green": 255, "blue": 255}
        self.border_color = {"red": 255, "green": 255, "blue": 255}
        self.runes_color = {"red": 255, "green": 255, "blue": 255}

        color = color_string_to_dict(self.python_gml["class"].get("title_border_color", ""))
        if color is not None:
            self.title_border_color = color
        color = color_string_to_dict(self.python_gml["class"].get("border_color", ""))
        if color is not None:
            self.border_color = color
        color = color_string_to_dict(self.python_gml["class"].get("runes_color", ""))
        if color is not None:
            self.runes_color = color

        self.background_pixbufs = None # A list GdkPixbuf to build a card's background
        self.redraw_background = True # A flag allowing us to save some computational time (don't always compute the background)

    def save_header(self):
        return super().save_header("frosthaven")

    def save_additional_class_attributes(self):
        col_1  = f'{int(self.title_border_color["red"])}, {int(self.title_border_color["green"])}, {int(self.title_border_color["blue"])}'
        col_2  = f'{int(self.border_color["red"])}, {int(self.border_color["green"])}, {int(self.border_color["blue"])}'
        col_3  = f'{int(self.runes_color["red"])}, {int(self.runes_color["green"])}, {int(self.runes_color["blue"])}'
        return {"title_border_color": col_1, "border_color": col_2, "runes_color": col_3}

    def create_card_layout(self, cr: cairo.Context):
        if self.redraw_background:
            self.background_pixbufs = fh_generate_card_background(self.color, self.title_border_color, self.border_color, self.runes_color)
            self.redraw_background = False
        for pixbuf in self.background_pixbufs:
            Gdk.cairo_set_source_pixbuf(cr, pixbuf.scale_simple(fh_card_width, fh_card_height, GdkPixbuf.InterpType.NEAREST),0,0)
            cr.paint()

        # Add the basic attack two ability
        blank = TextItem([" "], FrosthavenLineContext())
        attack = FrosthavenImage(["attack.svg"], FrosthavenLineContext(image_size=0.875*fh_tiny_image_size))
        two = TextItem(["2"], FrosthavenLineContext())
        basic_attack = LineItem([attack, blank, two])
        cr.save()
        cr.translate(0.15*fh_card_width - basic_attack.get_width()/2, 0.515*fh_card_height - basic_attack.get_height()/2)
        basic_attack.draw(cr)
        cr.restore()
        # Add the basic move two ability
        move = FrosthavenImage(["move.svg"], FrosthavenLineContext(image_size=0.875*fh_tiny_image_size))
        basic_move = LineItem([move, blank, two])
        cr.save()
        cr.translate(0.84*fh_card_width - basic_move.get_width()/2, 0.55*fh_card_height - basic_move.get_height()/2)
        basic_move.draw(cr)
        cr.restore()

        # Class icon
        if len(self.path_to_icon) > 0:
            # The user gave a class icon
            icon = FrosthavenImage([self.path_to_icon],
                                FrosthavenLineContext(font_size =fh_small_image_size),
                                path_to_gml=self.path_to_gml)
            cr.save()
            cr.translate(0.89*fh_card_width - icon.get_width()/2, 0.08*fh_card_height - icon.get_height()/2)
            cr.move_to(0,0)
            icon.draw(cr)
            # Go back to the original position
            cr.restore()