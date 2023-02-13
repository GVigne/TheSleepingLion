import gi
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo
import cairo
from .utils import text_to_pango
from .constants import *
from .gmllinecontext import GMLLineContext
from pathlib import Path

class AbstractItem:
    """
    Reminder: after an Item has been created, it's size cannot be changed. Once an Item has been created, it
    knows its width/height: this can be accessed via the get_width and get_height functions.
    """
    def __init__(self, path_to_gml : Path | None = None):
        self.path_to_gml = path_to_gml # All items know which GML file they depend.
        self.warnings = []

    def get_width(self):
        pass

    def get_height(self):
        pass

    def get_warnings(self):
        """
        Returns a list of warnings as strings: these are caught errors (ie non-breaking errors) which happened
        somehow when dealing with the abstract item. The warnings are meant to be for the end-user.
        """
        return self.warnings

    def draw(self, cr : cairo.Context):
        """
        Draw the item on the cairo context. It is not the item's responsability to be placed correctly on
        the context: instead, it draws itself where the cursor currently is.
        If the item needs to translate the context, then it must undo the translation at the end of draw:
        the cursor must be at the same absolute position before and after draw.
        """
        pass

class LineItem(AbstractItem):
    """
    A class to represent a line block. A line block contains different items which will be displayed side
    by side.
    """
    def __init__(self, items : list[AbstractItem],
                       path_to_gml : Path | None = None):
        super().__init__(path_to_gml)
        self.items = items

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
    A class to represent a column block. A column block contains different items which will be displayed
    one under the other.
    """
    def __init__(self, items : list[AbstractItem], path_to_gml : Path | None = None):
        super().__init__(path_to_gml)
        self.items = items

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
            start_x = mid_width - 0.5 * item.get_width()
            cr.save()
            cr.translate(start_x, 0)
            cr.move_to(0,0)
            item.draw(cr)
            cr.restore()

            current_y = item.get_height()
            cr.translate(0, current_y) # Go back to the left of the column
            cr.move_to(0,0)
        cr.restore() # Go back to the top left of the column

class TextItem(AbstractItem):
    """
    A class to represent any type of string rendered on the card.
    """
    def __init__(self,  text : str,
                        gml_context: GMLLineContext,
                        path_to_gml : Path | None = None):
        super().__init__(path_to_gml)
        self.text = text
        self.pango_text = text_to_pango(text, gml_context)
        # self.pango_text.set_single_paragraph_mode(True)
        self.red = gml_context.text_color["red"]
        self.green = gml_context.text_color["green"]
        self.blue = gml_context.text_color["blue"]
        self.height = Pango.units_to_double(self.pango_text.get_size().height)
        # This font has too much space, this is manually compensated here
        self.needs_scaling = gml_context.font == "Sakkal Majalla Bold"

    def get_text(self):
        return self.text

    def get_width(self):
        return Pango.units_to_double(self.pango_text.get_size().width)

    def get_height(self):
        if self.needs_scaling:
            return 0.72 * self.height
        return self.height

    def draw(self, cr: cairo.Context):
        # Recenter if needed
        if self.needs_scaling:
            cr.rel_move_to(0, -(self.height - self.get_height()) / 2.0)
        cr.set_source_rgba(self.red / 255, self.green / 255, self.blue / 255) # By default, draw in white
        PangoCairo.update_layout(cr, self.pango_text) # Since we changed the target surface, we need to update the layout
        PangoCairo.show_layout(cr, self.pango_text)

