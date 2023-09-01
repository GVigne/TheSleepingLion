from thesleepinglion.core.abstractGMLlinecontext import AbstractGMLLineContext
from thesleepinglion.core.items import AbstractItem
import cairo
from pathlib import Path

from ..core.items import AbstractItem, LineItem, ColumnItem
from .gloomhavenlinecontext import GloomhavenLineContext

class GloomhavenLineItem(LineItem):
    """
    We overload the base "LineItem" as we need to keep track of the black banner (Mindthief's Augment's black banner)
    throughout the parsing.
    """
    def __init__(self, arguments: list[AbstractItem],
                gml_context: GloomhavenLineContext | None = None,
                path_to_gml: Path | None = None):
        super().__init__(arguments, gml_context, path_to_gml)
        self.banner_background = None
        if gml_context is not None:
            self.banner_background = gml_context.banner_background

class GloomhavenColumnItem(ColumnItem):
    """
    Like LineItem, a column in Gloomhaven format should take into account the black banner when it is drawn
    """
    def __init__(self,
                arguments: list[AbstractItem],
                gml_context: GloomhavenLineContext | None = None,
                path_to_gml: Path | None = None):
        super().__init__(arguments, gml_context, path_to_gml)

    def draw(self, cr: cairo.Context,
                additional_vertical_offset = None):
        """
        additional_vertical_offset is a keyword reserved for subclasses of GloomhavenColumnItem.

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

class GHTopmostLineItem(GloomhavenLineItem):
    """
    For now, this class isn't really used, and could be replace by GloomhavenLineItem. We still keep it for clarity purposes,
    and because we might need it someday.
    """
    @staticmethod
    def promoteLineItem(line_item: GloomhavenLineItem):
        promoted_item = GHTopmostLineItem(line_item.items, None, line_item.path_to_gml)
        promoted_item.banner_background = line_item.banner_background
        return promoted_item

class GHTopmostColumnItem(GloomhavenColumnItem):
    """
    A TopmostColumnItem in Gloomhaven format needs to be able to communicate with a GloomhavenCard in order
    to draw a black banner background.
    """
    @staticmethod
    def promoteColumnItem(column_item: ColumnItem):
        return GHTopmostColumnItem(column_item.items, None, column_item.path_to_gml)

    def __init__(self, arguments: list[AbstractItem],
                gml_context: AbstractGMLLineContext | None,
                path_to_gml: Path | None = None):
        super().__init__(arguments, gml_context, path_to_gml)
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
