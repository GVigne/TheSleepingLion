import gi
gi.require_version('PangoCairo', '1.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gdk, GdkPixbuf, Pango, PangoCairo
import cairo
from pathlib import Path

from .haven_type import Haven
from .abstractGMLlinecontext import AbstractGMLLineContext
from .utils import text_to_pango, get_image, get_aoe
from .errors import MismatchNoArguments, ImageNotFound, InvalidAoEFile, EmptyArgument
from .svg_wrapper import SVGImage
from .hexagonal_grid import HexagonalGrid, HexagonDict

class AbstractItem:
    """
    Abstract class to represent an item. An item has a rectangular shape and can be drawn onto a cairo context.
    Once an item has been created, it's size cannot be changed: therefore, once an item is created, it knows its width/height,
    which can be accessed via the get_width and get_height functions.
    Most items are meant for the end user: the rule of thumb to add a command is simply to create a new item.

    Child classes must reimplement the get_width, get_height and draw functions, and should overload the __init__ to
    raise a MismatchNoArguments error if the arguments don't correspond to what is expected.
    """
    def __init__(self, arguments : list[str], # can also be a list of AbstractItems
                    gml_context: AbstractGMLLineContext,
                    path_to_gml : Path | None = None):
        self.path_to_gml = path_to_gml # All items know which GML file they depend on.
        self.arguments = arguments
        self.warnings = []

    def get_width(self):
        pass

    def get_height(self):
        pass

    def draw(self, cr : cairo.Context):
        """
        Draw the item on the cairo context. It is not the item's responsability to be placed correctly on
        the context: instead, it draws itself where the cursor currently is.
        If the item needs to translate the context, then it must undo the translation at the end of draw:
        the cursor must be at the same absolute position before and after draw.
        """
        pass

    def get_warnings(self):
        """
        Returns a list of warnings as strings: these are caught errors (ie non-breaking errors) which happened
        somehow when dealing with the item. The warnings are meant to be for the end-user.
        """
        return self.warnings

class TextItem(AbstractItem):
    """
    Represents any type of string rendered on the card.
    This class is meant for the developper, not the end-user.
    """
    def __init__(self, arguments: list[str],
                    gml_context: AbstractGMLLineContext,
                    path_to_gml: Path | None = None):
        super().__init__(arguments, gml_context, path_to_gml)
        self.text = arguments[0]

        self.pango_text = text_to_pango(self.text, gml_context)
        # self.pango_text.set_single_paragraph_mode(True)
        self.red = gml_context.text_color["red"]
        self.green = gml_context.text_color["green"]
        self.blue = gml_context.text_color["blue"]
        self.text_height = Pango.units_to_double(self.pango_text.get_size().height)
        # This font has too much space, this is manually compensated here
        self.needs_scaling = gml_context.font == "Sakkal Majalla Bold"

    def get_text(self):
        return self.text

    def get_width(self):
        return Pango.units_to_double(self.pango_text.get_size().width)

    def get_height(self):
        if self.needs_scaling:
            return 0.72 * self.text_height
        return self.text_height

    def draw(self, cr: cairo.Context):
        cr.save()
        if self.needs_scaling: # Recenter the text if needed
            cr.move_to(0, -(self.text_height - self.get_height()) / 2.0)
        cr.set_source_rgba(self.red / 255, self.green / 255, self.blue / 255) # By default, draw in white
        PangoCairo.update_layout(cr, self.pango_text) # Since we changed the target surface, we need to update the layout
        PangoCairo.show_layout(cr, self.pango_text)
        cr.restore()

class LineItem(AbstractItem):
    """
    Represents a line block which contains different items displayed side by side, centered horizontally.
    This class is meant for the developper, not the end-user.
    """
    def __init__(self, arguments: list[AbstractItem],
                    gml_context: AbstractGMLLineContext,
                    path_to_gml: Path | None = None):
        super().__init__(arguments, gml_context, path_to_gml)
        self.items = arguments # list of AbstractItems

    def get_width(self):
        return sum([item.get_width() for item in self.items])

    def get_height(self):
        try:
            result = max([item.get_height() for item in self.items])
        except ValueError:
            # Trying to take the max of an empty sequence
            result = 0
        return result

    def get_warnings(self):
        all_warnings = []
        for item in self.items:
            all_warnings = all_warnings + item.get_warnings()
        return all_warnings + self.warnings

    def draw(self, cr: cairo.Context):
        mid_height = self.get_height() / 2
        current_x = 0
        cr.save()
        for item in self.items:
            start_y = mid_height - 0.5 * item.get_height()
            cr.save()
            cr.translate(0, start_y)
            cr.move_to(0,0)
            item.draw(cr)
            cr.restore()

            current_x = item.get_width()
            cr.translate(current_x, 0) # Go back to the top of the line
            cr.move_to(0,0)
        cr.restore()

class ColumnItem(AbstractItem):
    """
    Represents a column block which contains different items displayed side by side, centered vertically.
    This class is meant for the developper, not the end-user.
    """
    def __init__(self, arguments: list[AbstractItem],
                    gml_context: AbstractGMLLineContext,
                    path_to_gml: Path | None = None):
        super().__init__(arguments, gml_context, path_to_gml)
        self.items = arguments # list of AbstractItems

    def get_width(self):
        try:
            result = max([item.get_width() for item in self.items])
        except ValueError:
            # Trying to take the max of an empty sequence
            result = 0
        return result

    def get_height(self):
        return sum([item.get_height() for item in self.items])

    def get_warnings(self):
        all_warnings = []
        for item in self.items:
            all_warnings = all_warnings + item.get_warnings()
        return all_warnings + self.warnings

    def draw(self, cr: cairo.Context):
        mid_width = self.get_width() / 2
        current_y = 0
        cr.save()
        for item in self.items:
            cr.translate(0, current_y) # Place the cursor at the correct height at the left of the column
            cr.move_to(0,0)
            cr.save()
            start_x = mid_width - 0.5 * item.get_width()
            cr.translate(start_x, 0)
            cr.move_to(0,0)
            item.draw(cr)
            cr.restore()
            current_y = item.get_height()
        cr.restore() # Go back to the top left of the column

class AbstractTopmostLineItem(LineItem):
    """
    Represents the line at the highest level. This is a way to distinguish between a LineItem whose only job
    is to align objects and the topmost LineItem which will be placed on the card: it's a way to break up a bit
    with the recursive nature of parsing, and allows to pass easily information between items and the Card.

    This class is meant for the developper and must be overloaded. It must provide a promoteLineItem method to
    convert a LineItem into a TopMostLineItem.
    """
    @staticmethod
    def promoteLineItem(line_item: LineItem):
        return AbstractTopmostLineItem(line_item.arguments, None, line_item.path_to_gml)

class AbstractTopmostColumnItem(ColumnItem):
    """
    Represents the column at the highest level, similarly to TopMostLineItem. However, it must only hold
    TopmostLineItem, or some methods may fail.
    """
    @staticmethod
    def promoteColumnItem(column_item: ColumnItem):
        return AbstractTopmostColumnItem(column_item.arguments, None, column_item.path_to_gml)

# How to center an image:
# An image is drawn with a size of 1.4 times the font size. Out of an image of height 110 (font size 100 on Inkscape):
#   - the text baseline (bottom of letter A) is located at 31.3 from the bottom (73.7 from top)
#   - the top of A is at 78.3 from the bottom (21.7 from top)
class ImageCommand(AbstractItem):
    """
    Represents an image rendered on a card.
    This is the most widespread way to show an image. For more precise handling of the image (for example, changing
    the color of a SVG file), use the SVGImage class directly.
    """
    def __init__(self, arguments: list[str],
                    gml_context: AbstractGMLLineContext,
                    path_to_gml: Path | None = None):
        super().__init__(arguments, gml_context, path_to_gml)

        if len(arguments) != 1 and len(arguments) != 2:
            raise MismatchNoArguments(f"The '\\image' command takes 1 mandatory argument and 1 optional argument but {len(arguments)} were given.")
        path_to_image = arguments[0]
        try:
            image_path = get_image(self.path_to_gml, path_to_image, gml_context.haven_type) # May raise the ImageNotFound error.
        except ImageNotFound as e:
            image_path = get_image(self.path_to_gml, "not_found.svg", Haven.COMMON)
            self.warnings.append(str(e))

        user_scaling = 1
        if len(arguments) == 2:
            user_scaling = float(arguments[1])
        default_height = 1.4 * gml_context.font_size  * user_scaling # Height to font height ratio.

        # Load SVG as vector graphic, other files as pixbuf
        if Path(image_path).suffix == ".svg":
            try:
                self.image = SVGImage(image_path, default_height)
            except Exception:
                self.image = SVGImage(get_image(self.path_to_gml, "not_found.svg", Haven.COMMON), default_height)
                self.warnings.append(f"The file {image_path} isn't a readable image (.svg or .png).")
        else:
            try:
                self.image = GdkPixbuf.Pixbuf.new_from_file_at_scale(image_path, -1, default_height, True)
            except Exception:
                self.image = SVGImage(get_image(self.path_to_gml, "not_found.svg", Haven.COMMON), default_height)
                self.warnings.append(f"The file {image_path} isn't a readable image (.svg or .png).")

    def get_width(self):
        return self.image.get_width()

    def get_height(self):
        return self.image.get_height()

    def draw(self, cr: cairo.Context):
        cr.save()
        if isinstance(self.image, GdkPixbuf.Pixbuf):
            Gdk.cairo_set_source_pixbuf(cr, self.image, 0, 0)
            cr.paint()
        else:
            self.image.draw(cr)
        cr.restore()

class AoECommand(AbstractItem):
    """
    Represents an AoE rendered on a card.
    TODO: HexagonalGrid.draw() should take a Haven argument to differentiate between Gloomhaven AoEs and Frosthaven AoEs
    """
    def __init__(self, arguments: list[str],
                    gml_context: AbstractGMLLineContext,
                    path_to_gml: Path | None = None):
        super().__init__(arguments, gml_context, path_to_gml)
        if len(arguments) != 1 :
            raise MismatchNoArguments(f"The '\\aoe' command takes 1 argument {len(arguments)} were given.")

        self.hexagons = HexagonDict()
        # May raise the AoeFileNotFound error. Let's not catch it: an AoE is probably more important than an image
        # so the user really should give a path (can't be ignored like an image.)
        aoe_path = get_aoe(path_to_gml, arguments[0], gml_context.haven_type)
        try:
            self.hexagons = HexagonDict.CreateFromFile(aoe_path)
        except Exception as e:
            raise InvalidAoEFile(f"The .aoe file {arguments[0]} couldn't be read. Please correct it and try again.")
        self.hex_grid = HexagonalGrid(gml_context.font_size)

    def get_width(self):
        return self.hex_grid.get_width(self.hexagons)

    def get_height(self):
        return self.hex_grid.get_height(self.hexagons)

    def draw(self, cr: cairo.Context):
        self.hex_grid.draw(cr, self.hexagons)