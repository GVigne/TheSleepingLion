import gi

gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo
import cairo
from .utils import text_to_pango, list_join
from .gmllinecontext import GMLLineContext
from pathlib import Path

class AbstractItem:
    """
    Reminder: after an Item has been created, it's size cannot be changed. Once an Item has been created, it
    knows its width/height: this can be accessed via the get_width and get_height functions.
    Items should only take their height and width into account, and shouldn't worry about additional blanks before
    or after them which should be displayed to have a pretty output.
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
                       path_to_gml : Path | None = None,
                       joining_item: AbstractItem | None = None,
                       gml_context: GMLLineContext | None = None):
        super().__init__(path_to_gml)
        if joining_item is None:
            self.items = items
        else:
            self.items = list_join(items, joining_item)

        # The following is used in TopmostLineItem
        self.banner_background = None
        if gml_context is not None:
            self.banner_background = gml_context.banner_background

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

    def draw(self, cr: cairo.Context,
                additional_vertical_offset = None):
        """
        additional_vertical_offset is a keyword reserved for subclasses of ColumnItem.

        If specified, additional_vertical_offset should be a list of floats with length len(self.items). Each represents
        an extra offset (blank space) which will be inserted immediately before items. The first blank will for example be added
        immediately before the first item.
        """
        mid_width = self.get_width() / 2
        current_y = 0
        cr.save()
        for idx, item in enumerate(self.items):
            if additional_vertical_offset is not None:
                current_y += additional_vertical_offset[idx]
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

class TopmostLineItem(LineItem):
    """
    Represents the line at the highest level. This is a way to distinguish between a LineItem whose only job
    is to align objects and the topmost LineItem which will be placed on the card: it's a way to break up a bit
    with the recursive nature of parsing, and allows to pass easily information between items and the GloomhavenCard
    object.
    Currently, this is only used for the @banner macro (black background).
    """
    @staticmethod
    def promoteLineItem(line_item: LineItem):
        promoted_item = TopmostLineItem(line_item.items,
                               path_to_gml = line_item.path_to_gml,
                               joining_item = None)
        promoted_item.banner_background = line_item.banner_background
        return promoted_item

class TopmostColumnItem(ColumnItem):
    """
    Represents the column at the highest level, similarly to TopMostLineItem.
    Note that a TopMostColumnItem must only hold TopmostLineItem, or some methods may fail.
    """
    @staticmethod
    def promoteColumnItem(column_item: ColumnItem):
        return TopmostColumnItem(column_item.items, column_item.path_to_gml)

    def __init__(self, items: list[AbstractItem], path_to_gml: Path | None = None):
        super().__init__(items, path_to_gml)
        self.banner_additional_padding = 5

    def get_height(self):
        """
        TopmostColumnItem needs to keep some additional space if the lines have a black banner.
        If a line has a black banner, it should spread evenly above and below. However, if multiple lines have a
        black banner, then they should be fused together so an extra offset isn't added in-between banner lines.
        """
        sub_items_height = []
        prev_item_bb = False
        for item in self.items:
            height = item.get_height()
            if self.add_padding_before(item.banner_background, prev_item_bb):
                height += self.banner_additional_padding
            prev_item_bb = bool(item.banner_background) # bool(None) is False
            sub_items_height.append(height)
        # If the last line had a black banner, we need to add yet another black padding underneath it
        if len(self.items) > 0 and self.items[-1].banner_background:
            sub_items_height[-1] = sub_items_height[-1] + self.banner_additional_padding
        return sum(sub_items_height)

    def draw(self, cr: cairo.Context):
        all_offsets = []
        prev_item_bb = False
        for item in self.items:
            offset = 0
            # This is similar to what is done in the draw function
            if self.add_padding_before(item.banner_background, prev_item_bb):
                offset = self.banner_additional_padding
            prev_item_bb = bool(item.banner_background) # bool(None) is False
            all_offsets.append(offset)
        return super().draw(cr, all_offsets)

    def black_banner_coordinates(self):
        """
        Return a list of information enabling the card to draw a black banner at specific location.
        Each information is a dictionnary holding the position on the y axis "y-position" of the top left
        corner and the banner's height "height".
        Coordinates are relative to this item: (0,0) corresponds to the top left corner.
        """
        banners = []
        y = 0
        prev_item_bb = False
        for item in self.items:
            if self.add_padding_before(item.banner_background, prev_item_bb):
                banners.append({"y-position": y, "height": self.banner_additional_padding})
                y += self.banner_additional_padding
            if item.banner_background:
                banners.append({"y-position": y, "height": item.get_height()})
            prev_item_bb = bool(item.banner_background) # bool(None) is False
            y += item.get_height()
        # If the last line item has a black banner, add some extra padding underneath it
        if len(self.items) > 0 and self.items[-1].banner_background:
            banners.append({"y-position": y, "height": self.banner_additional_padding})
        return banners

    def add_padding_before(self, item_bb: bool, prev_item_bb: bool):
        """
        If two adjacent lines have a black banner, they shouldn't overlap, and spacing between them should be
        the same as usual (0 spacing).
        Returns true if a padding for the black banner should be added BEFORE the current item.
        """
        return (not item_bb and prev_item_bb) or (item_bb and not prev_item_bb)

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
