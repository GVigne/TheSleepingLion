# Utility functions to create the card background
import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, GdkPixbuf

import os
import cairo
import numpy as np

from .card_background_utils import pixbuf_to_array, array_to_pixbuf, rgb_to_lch, lch_to_rgb
from ..utils import get_background_asset

# Preload images: rune, background
RUNES = pixbuf_to_array(GdkPixbuf.Pixbuf.new_from_file(get_background_asset("runes.png")))
BACKGROUND = pixbuf_to_array(GdkPixbuf.Pixbuf.new_from_file(get_background_asset("cardBackground.png")))

# Create mask for background image

bg_image = pixbuf_to_array(GdkPixbuf.Pixbuf.new_from_file(get_background_asset("colorMask.png")))
COLORMASK = (BACKGROUND[:, :, 3] > 0) & (bg_image[:, :, 3] > 0)

# Convert background to Lch space
BACKGROUND = rgb_to_lch(BACKGROUND)

def create_card_background(red: int, green: int, blue: int, background_dimming: float = 0.7) -> GdkPixbuf:
    """
    Given a source color, returns a GdkPixbuf of the backround, with the specified color shade.
    @param red green blue: RGB color code, 0-255 scale
    @param background_dimming The background is dimmer than the rune: multiply the background color
                              by this value ; it is expected to be < 1
    @return a GdkPixbuf
    """
    color = np.array([red, green, blue, 255])
    final_image = BACKGROUND

    # Start with background - supperpose in Lch space
    # Convert color to Lch
    lch_color = rgb_to_lch(np.array([[color]])).flatten()

    final_image[:, :, 1][COLORMASK] = lch_color[1] * background_dimming
    final_image[:, :, 2][COLORMASK] = lch_color[2]

    # Convert back to RGB space
    final_image = lch_to_rgb(final_image)

    # Add the runes
    # Gimp operation: Darken only
    dark = np.minimum(RUNES, color)
    # Gimp operation: Screen
    final_image = (255 - (255 - dark).astype(np.int64) * (255 - final_image).astype(np.int64) / 255).astype(np.uint8)

    return array_to_pixbuf(final_image)


# Example
if __name__ == "__main__":
    background = create_card_background(0, 255, 100)

    # Render background to PDF
    surface = cairo.PDFSurface("background_example.pdf", 2 * background.get_width(), background.get_height())
    cr = cairo.Context(surface)

    Gdk.cairo_set_source_pixbuf(cr, background, 0, 0)
    cr.paint()
    import time
    ts = time.time()
    background = create_card_background(0, 255, 0)
    te = time.time()
    print(te - ts)

    Gdk.cairo_set_source_pixbuf(cr, background, background.get_width(), 0)
    cr.paint()

    surface.finish()

