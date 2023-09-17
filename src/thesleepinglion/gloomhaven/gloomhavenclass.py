import gi
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gdk, GdkPixbuf
from pathlib import Path
import cairo

from ..background_code.create_card_background import create_card_background
from ..core.haven_type import Haven
from ..core.abstracthavenclass import AbstractHavenClass
from ..core.svg_wrapper import SVGImage
from ..core.utils import get_background_asset
from ..core.items import TextItem
from .gloomhaven_items import GloomhavenImage, GloomhavenLineItem
from .gloomhavencard import GloomhavenCard
from .gloomhavenlinecontext import GloomhavenLineContext
from .gloomhaven_constants import *


class GloomhavenClass(AbstractHavenClass):
    """
    A character with cards described with Gloomhaven syntax.
    """
    def __init__(self, path_to_gml: Path):
        super().__init__(path_to_gml, GloomhavenCard)
        self.card_background = None # A GdkPixbuf with the correct background color.
        self.redraw_background = True # A flag allowing us to save some computational time (don't always compute the background)

    def save_header(self):
        return super().save_header("gloomhaven")

    def create_card_layout(self, cr: cairo.Context):
        """
        Draw the general layout of a Gloomhaven card:
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

        # The height corresponds to 0.8*1.4*base_font_size. Note that 1.4 scaling comes from the GloomhavenImage.
        crown = SVGImage(get_background_asset("crown.svg", Haven.GLOOMHAVEN), height = 1.12*base_font_size, new_color = self.color)
        cr.save()
        cr.translate(card_width/2 - crown.get_width() /2, 0.105*card_height)
        cr.move_to(0,0)
        crown.draw(cr)
        # Go back to the original position
        cr.restore()

        # Even on real cards, the attack and move image is a bit bigger than their small font counterpart.
        attack = GloomhavenImage(["attack.svg"], GloomhavenLineContext(font_size = 1.05*small_font_size))
        move = GloomhavenImage(["move.svg"], GloomhavenLineContext(font_size = 1.05*small_font_size))
        two = TextItem(["2"], GloomhavenLineContext(font=title_font, font_size = small_font_size))
        blank = TextItem([" "], GloomhavenLineContext(font_size = small_font_size))

        # We need to aline manually the glyphs as they do not have the base font size.
        cr.save()
        cr.translate(0.134*card_width + blank.get_width(), 0.485*card_height)
        cr.move_to(0,0)
        attack.draw(cr)
        cr.translate(attack.get_width() + blank.get_width(), - 0.15*attack.get_height())
        two.draw(cr)
        cr.restore()
        # Same as above
        cr.save()
        cr.translate(0.134*card_width + blank.get_width(), 0.545*card_height)
        move.draw(cr)
        cr.translate(move.get_width() + blank.get_width(), - 0.15*move.get_height())
        two.draw(cr)
        cr.restore() # Go back to the top of the page.

        if len(self.path_to_icon) > 0:
            # The user gave a class icon
            icon = GloomhavenImage([self.path_to_icon],
                                GloomhavenLineContext(font_size =0.8*title_font_size),
                                path_to_gml=self.path_to_gml)
            icon_line = GloomhavenLineItem([icon])
            cr.save()
            cr.translate(0.5*card_width - icon_line.get_width() / 2, 0.9*card_height)
            cr.move_to(0,0)
            icon_line.draw(cr)
            # Go back to the original position
            cr.restore()

    def check_class_errors(self):
        """
        Check for errors in what the user defined at a class level. Return errors and warnings as lists of
        strings (the errors/warnings raised).
        This should ALWAYS be called when parsing the GML file. This is part of the parsing process, and may fail
        just as any other part.
        """
        class_errors, class_warnings = super().check_class_errors()
        if len(self.path_to_icon) >0:
            icon_image = GloomhavenImage([self.path_to_icon], GloomhavenLineContext(), path_to_gml=self.path_to_gml)
            class_warnings += icon_image.warnings
        return class_errors, class_warnings

