from pathlib import Path
import cairo
from math import pi

from ..core.abstractGMLlinecontext import AbstractGMLLineContext
from ..core.items import AbstractItem

class SecondaryActionBox(AbstractItem):
    """
    A class to represent the whitish box around the secondary effects of an action (ex: a status effect linked
    to an attack).
    This class is meant for the developper, not the end-user
    """
    @staticmethod
    def BoxAdditionalWidth():
        return 45

    def __init__(self,
                arguments: list[AbstractItem],
                gml_context: AbstractGMLLineContext,
                path_to_gml: Path | None = None):
        super().__init__(arguments, gml_context, path_to_gml)
        self.secondary_action = arguments[0]

    def get_width(self):
        return self.secondary_action.get_width() + 2*SecondaryActionBox.BoxAdditionalWidth()

    def get_height(self):
        return self.secondary_action.get_height()

    def draw(self, cr: cairo.Context):
        # Draw the whitish background
        cr.save()
        cr.move_to(SecondaryActionBox.BoxAdditionalWidth(), 0)
        cr.set_source_rgba(1,1,1,0.4)
        cr.set_line_width(0)
        cr.line_to(self.get_width() - SecondaryActionBox.BoxAdditionalWidth(), 0)
        # Rightmost arc
        cr.save()
        cr.translate(self.get_width() - SecondaryActionBox.BoxAdditionalWidth(), self.get_height()/2)
        cr.scale(SecondaryActionBox.BoxAdditionalWidth(), self.get_height()/2)
        cr.arc(0, 0, 1, -pi/2, pi/2)
        cr.restore()
        cr.line_to(SecondaryActionBox.BoxAdditionalWidth(), self.get_height())
        # Leftmost arc
        cr.save()
        cr.translate(SecondaryActionBox.BoxAdditionalWidth(), self.get_height()/2)
        cr.scale(SecondaryActionBox.BoxAdditionalWidth(), self.get_height()/2)
        cr.arc(0,0, 1, pi/2, -pi/2)
        cr.restore()
        # Close path and draw
        cr.close_path()
        cr.fill_preserve()
        cr.set_source_rgba(1,1,1,1)
        cr.stroke()
        cr.restore()
        # Draw the inner item
        cr.save()
        cr.translate(SecondaryActionBox.BoxAdditionalWidth(), 0)
        cr.move_to(0,0)
        self.secondary_action.draw(cr)
        cr.restore()
