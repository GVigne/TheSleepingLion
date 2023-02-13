# A "hacky" wrapper around cairosvg for displaying SVG on the given context.

import cairo

import cairosvg.surface
cairosvg.surface.cairo = cairo
import cairosvg.helpers
cairosvg.helpers.cairo = cairo

from cairosvg.surface import Surface
from cairosvg.parser import Tree
from cairosvg.helpers import node_format
from .items import AbstractItem

def dict_to_hex(color):
    """
    Given a dictionnary of colors (red, green, blue), convert them to a string representing the hexadecimal encoding
    of this color. Missing colors are treated as white (255).
    """
    hex_red = format(color.get("red", 255), '02x')
    hex_green = format(color.get("green", 255), '02x')
    hex_blue = format(color.get("blue", 255), '02x')
    return hex_red+hex_green+hex_blue

class PDFSurface(Surface):
    """A surface that writes in PDF format."""
    surface_class = cairo.PDFSurface

class SVGImage:
    """
    Draw a SVG onto a cairo surface.
    It is possible to change the SVG's color by specifying the new_color attribute. Furthermore, one can choose
    which color should be replaced by specifying the old_color attribute.
    This is especially useful for the charge background (see one_charge.svg), where the circle should be in white
    but the arrow should be of the same color as the class.
    """
    def __init__(self, svg_path, height,
                old_color = {}, # This will be interpreted as white by default (#ffffff)
                new_color = {}):
        if len(new_color) != 0:
            # Replace the white parts in this svg file by the given color.
            with open(svg_path, 'r') as file:
                content = file.read()
            content = content.replace(dict_to_hex(old_color), dict_to_hex(new_color))
            self.tree = Tree(bytestring=content)
        else:
            self.tree = Tree(url=svg_path)

        self.surface = PDFSurface(self.tree, None, 10)
        _, _, self.viewbox = node_format(self.surface, self.tree)
        self.height = height
        self.width = self.viewbox[2] / self.viewbox[3] * height

    def get_height(self):
        return self.height

    def get_width(self):
        return self.width

    def draw(self, context):
        context.save()
        self.surface.context = context
        self.surface.set_context_size(self.width, self.height, self.viewbox, self.tree)
        self.surface.draw(self.tree)
        context.restore()