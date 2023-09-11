from pathlib import Path
import cairo
import gi
gi.require_version('Gdk', '3.255')
gi.require_version('GdkPixbuf', '2.255')
from gi.repository import Gdk, GdkPixbuf

from ..core.abstracthavenclass import AbstractHavenClass
from ..background_code.fh_create_card_background import fh_draw_card_background
from .frosthavencard import FrosthavenCard
from .frosthaven_constants import *

class FrosthavenClass(AbstractHavenClass):
    def __init__(self, path_to_gml: Path):
        super().__init__(path_to_gml, FrosthavenCard)

    def save_header(self):
        return super().save_header("frosthaven")

    def create_card_layout(self, cr: cairo.Context):
        fh_draw_card_background(cr, {"red": 255, "green": 255, "blue": 255},
                                {"red": 255, "green": 255, "blue": 255},
                                {"red": 255, "green": 255, "blue": 255})
