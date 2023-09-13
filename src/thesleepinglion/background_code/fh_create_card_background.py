# Utility functions to create the card background
import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, GdkPixbuf
import cairo
import numpy as np
import time

from .card_background_utils import pixbuf_to_array, array_to_pixbuf, rgb_to_lch, lch_to_rgb
from ..core.utils import get_background_asset
from ..core.haven_type import Haven
from ..frosthaven.frosthaven_constants import *

def change_pixbuff_color(asset_name: str, red: int, green: int, blue: int) -> GdkPixbuf:
    """
    Given a source color, returns a GdkPixbuf of the given asset, with the specified color shade.
    red, green and blue are RGB color code on a 0-255 scale

    Note that all assets are assumed to be of size fh_card_width*fh_card_height and should be transparent
    in the areas where the color shade shouldn't be added. Unlike gloomhaven, there is no mask here - we can
    consider that the mask is a white rectangle of size gh_card_width*fh_card_height.
    """
    # Convert background to Lch space
    raw_pixbuff = GdkPixbuf.Pixbuf.new_from_file(get_background_asset(asset_name, Haven.FROSTHAVEN))
    if red == 255 and green == 255 and blue == 255:
        return raw_pixbuff
    raw_asset = pixbuf_to_array(raw_pixbuff)

    COLORMASK = raw_asset[:, :, 3] > 0
    raw_asset = rgb_to_lch(raw_asset)

    color = np.array([red, green, blue, 255])
    final_image = raw_asset

    # Start with background - supperpose in Lch space
    # Convert color to Lch
    lch_color = rgb_to_lch(np.array([[color]])).flatten()

    final_image[:, :, 1][COLORMASK] = lch_color[1]
    final_image[:, :, 2][COLORMASK] = lch_color[2]

    # Convert back to RGB space
    final_image = lch_to_rgb(final_image)

    # Gimp operation: Screen
    final_image = (255 - 255 * (255 - final_image).astype(np.int64) / 255).astype(np.uint8)

    return array_to_pixbuf(final_image)

def fh_generate_card_background(background_color: dict,
                            title_border_color: dict,
                            stone_borders_color: dict,
                            side_runes_color: dict = {"red": 255, "green": 255, "blue": 255}) -> None:
    """
    Return a list of Pixbuffs which make up a card's bacground. They should be displayed in the order they are in the list.
    """
    card_background = change_pixbuff_color("card_background.png", background_color["red"], background_color["green"], background_color["blue"])
    center_runes = change_pixbuff_color("central_runes.png", stone_borders_color["red"], stone_borders_color["green"], stone_borders_color["blue"])
    stone_borders = change_pixbuff_color("card_stone_borders.png", 255, 255, 255)
    title_border = change_pixbuff_color("title_stone_border.png", title_border_color["red"], title_border_color["green"], title_border_color["blue"])
    side_borders = change_pixbuff_color("side_stone_border.png", stone_borders_color["red"], stone_borders_color["green"], stone_borders_color["blue"])
    side_runes = change_pixbuff_color("side_runes.png", side_runes_color["red"], side_runes_color["green"], side_runes_color["blue"])
    return [card_background, center_runes, stone_borders, title_border, side_borders, side_runes]

