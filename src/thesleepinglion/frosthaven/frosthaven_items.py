from ..core.items import AbstractImageItem, LineItem, ColumnItem
from .frosthavenlinecontext import FrosthavenLineContext
from .frosthaven_constants import *

class FrosthavenImage(AbstractImageItem):
    def get_default_height(self, gml_context: FrosthavenLineContext):
        return gml_context.image_size

class FHTopmostLineItem(LineItem):
    """
    For now, this class is mostly empty
    """
    @staticmethod
    def promoteLineItem(line_item: LineItem):
        promoted_item = FHTopmostLineItem(line_item.items, FrosthavenLineContext(), line_item.path_to_gml)
        return promoted_item

class FHTopmostColumnItem(ColumnItem):
    """
    For now, this class is mostly empty
    """
    @staticmethod
    def promoteColumnItem(column_item: ColumnItem):
        promoted_item = FHTopmostLineItem(column_item.items, FrosthavenLineContext(), column_item.path_to_gml)
        return promoted_item