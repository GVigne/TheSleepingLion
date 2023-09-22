from pathlib import Path
import cairo
from math import pi, sqrt

from ..core.abstractGMLlinecontext import AbstractGMLLineContext
from ..core.items import AbstractItem, TextItem
from ..core.errors import MismatchNoArguments

from .frosthavenlinecontext import FrosthavenLineContext
from .frosthaven_constants import *

class SecondaryActionBox(AbstractItem):
    """
    A class to represent the whitish box around the secondary effects of an action (ex: a status effect linked
    to an attack).
    This class is meant for the developper, not the end-user
    """
    @staticmethod
    def BoxAdditionalWidth():
        """
        SecondaryActionBox adds some space to the left and right of the action to draw the whitish background.
        Return half the value of the total space added.
        """
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

class MandatoryBox(AbstractItem):
    """
    A class to represent the mandatory boxes around actions. Can be used for top left mandatory boxes, mandatory
    boxes for actions (ie element generation) or bottom right boxes (ex: lost, permanent)
    This class is meant for the developper, not the end user.
    """
    @staticmethod
    def TotalAddedWith():
        """
        Return the total additional width required to draw a mandatory box
        """
        # We need 2 SlantedLineWidth and the exclamation mark before drawing the item, then an additional SlantedLineWidth the right
        return 3*MandatoryBox.SlantedLineWidth() + MandatoryBox.LineWidth() + \
                TextItem(["!"], FrosthavenLineContext(font_size=fh_medium_font_size)).get_width()

    @staticmethod
    def TotalAddedHeight():
        """
        Return the total additional height required to draw a mandatory box
        """
        return 30 # = 2*15, for symmetry

    @staticmethod
    def SlantedLineWidth():
        """
        \
         | <- this width, ie the additional width added by the slanted lines.
        /
        """
        return 25

    @staticmethod
    def LineWidth():
        """
        The width of the line used to draw the mandatory box
        """
        return 4

    def __init__(self,
                arguments: list[AbstractItem],
                gml_context: AbstractGMLLineContext,
                path_to_gml: Path | None = None):
        super().__init__(arguments, gml_context, path_to_gml)
        self.item = arguments[0]
        self.box_color = gml_context.class_color
        self.exclamation = TextItem(["!"], FrosthavenLineContext(text_color = self.box_color,
                                                                 font_size=fh_medium_font_size))

        # Store these as attributes so they aren't recomputed every time we use them
        self.total_added_width = MandatoryBox.TotalAddedWith()

    def get_width(self):
        return self.item.get_width() + self.total_added_width

    def get_height(self):
        return self.item.get_height() + MandatoryBox.TotalAddedHeight()

    def draw(self, cr: cairo.Context):
        # Draw the rectangular box
        cr.save()
        cr.set_source_rgb(self.box_color["red"], self.box_color["green"], self.box_color["blue"])
        cr.set_line_width(MandatoryBox.LineWidth())
        cr.move_to(MandatoryBox.SlantedLineWidth(), 0)
        cr.line_to(self.get_width() - MandatoryBox.SlantedLineWidth(), 0)
        cr.line_to(self.get_width(), MandatoryBox.SlantedLineWidth()) # 45° angle
        cr.line_to(self.get_width(), self.get_height() - MandatoryBox.SlantedLineWidth())
        cr.line_to(self.get_width() - MandatoryBox.SlantedLineWidth(), self.get_height())
        cr.line_to(MandatoryBox.SlantedLineWidth(), self.get_height())
        cr.line_to(0, self.get_height() - MandatoryBox.SlantedLineWidth())
        cr.line_to(0, MandatoryBox.SlantedLineWidth())
        cr.close_path()
        cr.stroke()
        cr.restore()
        # Draw the exclamation mark...
        cr.save()
        cr.translate(0.75*MandatoryBox.SlantedLineWidth(), self.get_height()/2 - self.exclamation.get_height()/2)
        cr.move_to(0,0)
        self.exclamation.draw(cr)
        cr.restore()
        # ... and the line next to it
        cr.save()
        cr.set_source_rgb(self.box_color["red"], self.box_color["green"], self.box_color["blue"])
        cr.set_line_width(MandatoryBox.LineWidth())
        cr.move_to(1.5*MandatoryBox.SlantedLineWidth() + self.exclamation.get_width(), 0)
        cr.line_to(1.5*MandatoryBox.SlantedLineWidth() + self.exclamation.get_width(), self.get_height())
        cr.stroke()
        cr.restore()
        # Draw the item
        cr.save()
        cr.translate(2*MandatoryBox.SlantedLineWidth() + self.exclamation.get_width(), MandatoryBox.TotalAddedHeight()/2)
        cr.move_to(0,0)
        self.item.draw(cr)
        cr.restore()

class BottomRightMandatoryBox(MandatoryBox):
    """
    Mandatory box put in the bottom right corner. The bottom line shouldn't be displayed, and side lines
    should have a gradient of color.
    """
    @staticmethod
    def TotalAddedHeight():
        """
        Return the total additional height required to draw a mandatory box
        """
        return 40 # = 2*20, for symmetry

    def draw(self, cr):
        # Draw the rectangular box
        cr.save()
        cr.set_line_width(MandatoryBox.LineWidth())
        # Top horizontal line
        gradient_length = 10
        start = MandatoryBox.SlantedLineWidth()
        end = self.get_width() - MandatoryBox.SlantedLineWidth() - gradient_length
        endgradient = self.get_width()
        cr.save()
        cr.move_to(start, 0)
        cr.line_to(end, 0)
        cr.set_source_rgb(self.box_color["red"], self.box_color["green"], self.box_color["blue"])
        cr.stroke()
        cr.restore()
        cr.save()
        gradient = cairo.LinearGradient(end, 0, endgradient, 0)
        gradient.add_color_stop_rgba(0,self.box_color["red"], self.box_color["green"], self.box_color["blue"], 1)
        gradient.add_color_stop_rgba(1,self.box_color["red"], self.box_color["green"], self.box_color["blue"], 0)
        cr.set_source(gradient)
        cr.move_to(end, 0)
        cr.line_to(endgradient, 0)
        cr.stroke()
        cr.restore()
        # Left vertical line
        start = MandatoryBox.SlantedLineWidth()
        endVertical = 0.6*self.get_height()
        endgradientVertical = self.get_height()
        fadeout = 0.2 # Opacity value for the bottom of the line
        cr.save()
        cr.set_source_rgb(self.box_color["red"], self.box_color["green"], self.box_color["blue"])
        cr.move_to(MandatoryBox.SlantedLineWidth(), 0)
        cr.line_to(0,start) # 45° angle
        cr.stroke()
        cr.restore()
        cr.save()
        gradient = cairo.LinearGradient(0, endVertical, 0, endgradientVertical)
        gradient.add_color_stop_rgba(0,self.box_color["red"], self.box_color["green"], self.box_color["blue"], 1)
        gradient.add_color_stop_rgba(1,self.box_color["red"], self.box_color["green"], self.box_color["blue"], fadeout)
        cr.set_source(gradient)
        cr.move_to(0,MandatoryBox.SlantedLineWidth())
        cr.line_to(0, endgradientVertical)
        cr.stroke()
        cr.restore()
        # Draw the exclamation mark (same as in MandatoryBox)
        cr.save()
        cr.translate(0.75*MandatoryBox.SlantedLineWidth(), self.get_height()/2 - self.exclamation.get_height()/2)
        cr.move_to(0,0)
        self.exclamation.draw(cr)
        cr.restore()
        # ... and the line next to it, with a gradient :)
        x_vertical_line = 1.5*MandatoryBox.SlantedLineWidth() + self.exclamation.get_width()
        cr.save()
        cr.move_to(x_vertical_line, 0)
        cr.set_source_rgb(self.box_color["red"], self.box_color["green"], self.box_color["blue"])
        cr.line_to(x_vertical_line, endVertical)
        cr.stroke()
        cr.restore()
        cr.save()
        gradient = cairo.LinearGradient(x_vertical_line, endVertical, x_vertical_line, endgradientVertical)
        gradient.add_color_stop_rgba(0,self.box_color["red"], self.box_color["green"], self.box_color["blue"], 1)
        gradient.add_color_stop_rgba(1,self.box_color["red"], self.box_color["green"], self.box_color["blue"], fadeout)
        cr.set_source(gradient)
        cr.move_to(x_vertical_line, 0)
        cr.line_to(x_vertical_line, endgradientVertical)
        cr.stroke()
        cr.restore()
        # Draw the item (same as in MandatoryBox)
        cr.save()
        cr.translate(2*MandatoryBox.SlantedLineWidth() + self.exclamation.get_width(), MandatoryBox.TotalAddedHeight()/2)
        cr.move_to(0,0)
        self.item.draw(cr)
        cr.restore()
        cr.restore() # Goes with the cr.save() in the first line

class AbilityLine(AbstractItem):
    """
    In gloomhaven, this was previoulsy named "DividerLine"
    """
    def __init__(self,
                arguments: list[str],
                gml_context: FrosthavenLineContext,
                path_to_gml: Path | None = None):
        super().__init__(arguments, gml_context, path_to_gml)
        if len(arguments) !=0:
            raise MismatchNoArguments(f"The '\\ability_line' takes no arguments but {len(arguments)} were given.")

        self.line_width = 2
        self.line_color = gml_context.class_color
        self.gradient_length = 50

    def get_width(self):
        return 500

    def get_height(self):
        return 100

    def draw(self, cr: cairo.Context):
        cr.save()
        cr.translate(0, self.get_height()/2)
        cr.move_to(0,0)
        cr.set_line_width(self.line_width)
        # Ability line's fadeout to the left
        gradient = cairo.LinearGradient(0, 0, self.gradient_length, 0)
        gradient.add_color_stop_rgba(0,self.line_color["red"], self.line_color["green"], self.line_color["blue"], 0)
        gradient.add_color_stop_rgba(1,self.line_color["red"], self.line_color["green"], self.line_color["blue"], 1)
        cr.set_source(gradient)
        cr.line_to(self.gradient_length, 0)
        cr.stroke()
        # Ability line's full stroke
        cr.set_source_rgb(self.line_color["red"], self.line_color["green"], self.line_color["blue"])
        cr.set_line_width(self.line_width)
        cr.move_to(self.gradient_length, 0)
        cr.line_to(self.get_width() - self.gradient_length, 0)
        cr.stroke()
        # Seconde fadeout
        gradient = cairo.LinearGradient(self.get_width() - self.gradient_length, 0, self.get_width(), 0)
        gradient.add_color_stop_rgba(0,self.line_color["red"], self.line_color["green"], self.line_color["blue"], 1)
        gradient.add_color_stop_rgba(1,self.line_color["red"], self.line_color["green"], self.line_color["blue"], 0)
        cr.set_source(gradient)
        cr.move_to(self.get_width() - self.gradient_length, 0)
        cr.line_to(self.get_width(), 0)
        cr.stroke()
        cr.restore()
