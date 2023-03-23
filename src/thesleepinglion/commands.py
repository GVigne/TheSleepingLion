import cairo
from pathlib import Path

from .items import AbstractItem, TextItem, LineItem, ColumnItem
from .errors import EmptyArgument, MismatchNoArguments, InvalidAoEFile, ImageNotFound
from .constants import base_font_size, title_font, small_font_size, card_width
from .utils import get_image, get_aoe, list_join
from .hexagonal_grid import HexagonalGrid, HexagonDict
from .gmllinecontext import GMLLineContext

from .svg_wrapper import SVGImage

from gi.repository import Gdk, GdkPixbuf

class AbstractCommand(AbstractItem):
    """
    An abstract class to represent commands.
    """
    def __init__(self, arguments : list[str],
                    gml_context: GMLLineContext,
                    path_to_gml : Path | None = None,
                    image_color: dict = {}):
        """
        gml_context is a set of instructions concerning font, font_size, color...
        Since creating a command and gml_line_to_items call each other (also see the circular import at end of this
        file), it must be given when creating a command.
        However, programatically, if one needs to create a command, one can simply recreate a new context with
        only the relevant parameters. For example, this happens when creating the base action "2 sword"
        (or "2 move") of a card.
        """
        # We don't necessarily store every argument. They are simply summed up here to know what kind of argument
        # can be passed to a command.
        super().__init__(path_to_gml)
        self.arguments = arguments

# How to center an image:
# An image is drawn with a size of 1.4 times the font size. Out of an image of height 110 (font size 100 on Inkscape):
#   - the text baseline (bottom of letter A) is located at 31.3 from the bottom (73.7 from top)
#   - the top of A is at 78.3 from the bottom (21.7 from top)
class ImageCommand(AbstractCommand):
    """
    A class to represent an image rendered on a card.
    This is the most widespread way to show an image. For more precise handling of the image (for example, changing
    the color of a SVG file), use the SVGImage class directly.
    """
    def __init__(self, arguments: list[str],
                    gml_context: GMLLineContext,
                    path_to_gml: Path | None = None,
                    image_color: dict = {}):
        super().__init__(arguments, gml_context, path_to_gml, image_color)
        if len(arguments) != 1 and len(arguments) != 2:
            raise MismatchNoArguments(f"The '\\image' command takes 1 mandatory argument and 1 optional argument but {len(arguments)} were given.")
        if len(arguments[0]) == 0:
            raise EmptyArgument("Argument for the '\\image' command may not be empty.")
        path_to_image = arguments[0]
        try:
            image_path = get_image(self.path_to_gml, path_to_image) # May raise the ImageNotFound error.
        except ImageNotFound as e:
            image_path = get_image(self.path_to_gml, "not_found.svg")
            self.warnings.append(str(e))

        user_scaling = 1
        if len(arguments) == 2:
            user_scaling = float(arguments[1])
        default_height = 1.4 * gml_context.font_size  * user_scaling # Height to font height ratio.

        self.x_offset = TextItem(" ", GMLLineContext(font_size=gml_context.font_size)).get_width()
        # Load SVG as vector graphic, other files as pixbuf
        if Path(image_path).suffix == ".svg":
            try:
                self.image = SVGImage(image_path, default_height)
            except Exception:
                self.image = SVGImage(get_image(self.path_to_gml, "not_found.svg"), default_height)
                self.warnings.append(f"The file {image_path} isn't a readable image (.svg or .png).")
        else:
            try:
                self.image = GdkPixbuf.Pixbuf.new_from_file_at_scale(image_path, -1, default_height, True)
            except Exception:
                self.image = SVGImage(get_image(self.path_to_gml, "not_found.svg"), default_height)
                self.warnings.append(f"The file {image_path} isn't a readable image (.svg or .png).")

    def get_width(self):
        return self.image.get_width() + 2 * self.x_offset # One blank after, one blank before.

    def get_height(self):
        return self.image.get_height()

    def draw(self, cr: cairo.Context):
        cr.save()
        cr.translate(self.x_offset, 0)
        cr.move_to(0,0)
        if isinstance(self.image, GdkPixbuf.Pixbuf):
            Gdk.cairo_set_source_pixbuf(cr, self.image, 0, 0)
            cr.paint()
        else:
            self.image.draw(cr)
        cr.restore()

class EnhancementDotCommand(AbstractCommand):
    """
    A class to represent the default enhancement in Gloomhaven (a dot). This dot always has a fixed size, no matter
    the environment it is in (summon, big or small text)... Hence, this command is just a wrapper around the
    ImageCommand.
    """
    def __init__(self, arguments: list[str],
                    gml_context: GMLLineContext,
                    path_to_gml: Path | None = None,
                    image_color: dict = {}):
        super().__init__(arguments, gml_context, path_to_gml, image_color)
        if len(arguments) != 0:
            raise MismatchNoArguments(f"The '\\dot' command takes no arguments but {len(arguments)} were given.")
        self.image = ImageCommand(["enhancement_dot.svg"], GMLLineContext(font_size = base_font_size), path_to_gml=path_to_gml)

    def get_width(self):
        return self.image.get_width()

    def get_height(self):
        return self.image.get_height()

    def draw(self, cr: cairo.Context):
        self.image.draw(cr)

class InsideCommand(AbstractCommand):
    """
    A class to represent something inside something else (ex: text inside image)
    Note: we assume the text fits inside the image. If this is not the case, too bad: there will be overlap
    """
    def __init__(self, arguments: list[str],
                    gml_context: GMLLineContext,
                    path_to_gml: Path | None = None,
                    image_color: dict = {}):
        super().__init__(arguments, gml_context, path_to_gml, image_color)

        if len(arguments) == 2 and (
            isinstance(arguments[0], AbstractItem) or isinstance(arguments[0], SVGImage)) and (
            isinstance(arguments[1], AbstractItem)):
            # This is a hack to allow developpers to draw one item into another. This is NOT the default way to use InsideCommand
            self.outside = arguments[0]
            self.inside = arguments[1]
        else:
            # This is the default behaviour.
            if len(arguments) != 2:
                raise MismatchNoArguments(f"The '\\inside' command takes exactly 2 arguments but {len(arguments)} were given.")
            if len(arguments[0]) == 0 or len(arguments[1]) == 0:
                raise EmptyArgument("Arguments for the '\\inside' command may not be empty.")

            # Previously, parser.create_command was recursive and could also call create_text with width = -1:
            # worse case scenario, you would have one big fat line as an argument of a command
            # To keep to this philosophy, we call gml_line_to_items with a width of -1, which fits everything on one line
            parser = GloomhavenParser(self.path_to_gml)
            out_gml = parser.gml_line_to_items(arguments[0], gml_context, width = -1)
            in_gml = parser.gml_line_to_items(arguments[1], gml_context, width = -1)
            if len(out_gml) == 0 or len(in_gml) == 0:
                # outside or inside has only macros, so there is no element/item to collect
                raise EmptyArgument("Arguments for the '\\inside' command must be valid gml commands and not only macros.")
            self.outside = out_gml[0]
            self.inside = in_gml[0]

    def get_width(self):
        return self.outside.get_width()

    def get_height(self):
        return self.outside.get_height()

    def draw(self, cr: cairo.Context):
        self.outside.draw(cr)
        cr.save()
        cr.translate(self.outside.get_width()/2 - self.inside.get_width() / 2,
                     self.outside.get_height()/2 - self.inside.get_height() / 2)
        cr.move_to(0,0)
        self.inside.draw(cr)
        cr.restore()

class ExpCommand(AbstractCommand):
    """
    In theory, we can write the experience command as:
        \\exp{$x$} = \\inside{\\image{experience.svg}}{@title_font @small @color{0}{0}{0} $x$}
    However, we sometimes want to change the exp color (for example in the charges command). If exp is an alias,
    then the word 'exp' will never be passeed to the parser, as the lexer will replace it with something else. It's
    easier to create this command, basically just as a wrapper.
    """
    def __init__(self, arguments: list[str],
                    gml_context: GMLLineContext,
                    path_to_gml: Path | None = None,
                    image_color: dict = {}):
        super().__init__(arguments, gml_context, path_to_gml, image_color)
        if len(arguments) != 1:
            raise MismatchNoArguments(f"The '\\exp' command takes only 1 argument but {len(arguments)} were given.")

        # Allow the exp image to be hacked so that it's color may be changed.
        context = GMLLineContext(font_size=1.2*gml_context.font_size)
        exp_image = ImageCommand(["experience.svg"], context,
                                path_to_gml=self.path_to_gml,
                                image_color = image_color)

        font_size_factor = 1
        if gml_context.font_size == base_font_size:
            font_size_factor = 0.8
        context = GMLLineContext(font = title_font,
                                font_size = font_size_factor*gml_context.font_size,
                                text_color={"red": 0, "green": 0, "blue": 0})
        self.exp_value = TextItem(arguments[0], context, path_to_gml=path_to_gml)

        # Hackish way to use the InsideCommand, by bypassing the parsing.
        self.exp_item = InsideCommand([exp_image, self.exp_value], gml_context, path_to_gml=self.path_to_gml)

    def new_image(self, image: ImageCommand|SVGImage):
        """
        Hack to allow to replace the image by another one.
        Since it's a hack, we can replace the GML context by None: it won't be used by the InsideCommand as we
        are already giving it two AbstractItems.
        """
        self.exp_item = InsideCommand([image, self.exp_value], None, path_to_gml=self.path_to_gml)

    def get_width(self):
        return self.exp_item.get_width()

    def get_height(self):
        return self.exp_item.get_height()

    def draw(self, cr: cairo.Context):
        self.exp_item.draw(cr)

class MultilineCommand(AbstractCommand):
    """
    A class which is basically just a wrapper around a Column Item. Allows the user to show elements stacked one
    under the other in the middle of the line (ex: Shield, \\n, Self).
    """
    def __init__(self, arguments: list[str],
                    gml_context: GMLLineContext,
                    path_to_gml: Path | None = None,
                    image_color: dict = {}):
        super().__init__(arguments, gml_context, path_to_gml, image_color)
        if len(arguments) == 0:
            raise MismatchNoArguments((f"The '\\multiline' command takes more than one argument, but 0 were given."))
        if len(arguments[0]) == 0:
            raise EmptyArgument("Arguments for the '\\multiline' command may not be empty.")

        parser = GloomhavenParser(self.path_to_gml)
        self.parsed_arguments = []
        for arg in arguments:
            parsed_arg = parser.gml_line_to_items(arg, gml_context)
            if len(parsed_arg) == 0 :
                # one of the argument has only macros, so there is no element/item to collect
                raise EmptyArgument("Arguments for the '\\multiline' command must be valid gml commands and not only macros.")
            self.parsed_arguments.append(parsed_arg[0])
        self.column = ColumnItem(self.parsed_arguments, self.path_to_gml)

    def get_width(self):
        return self.column.get_width()

    def get_height(self):
        return self.column.get_height()

    def draw(self, cr: cairo.Context):
        self.column.draw(cr)

class OneChargeItem(AbstractCommand):
    """
    A simple wrapper to make the writing of a charges command easier. When drawn, this class will:
        - draw the circle and arrow around the charge. Also draw a white space after.
        - draw something centered in the circle (reminder: the circle is not in the middle of one_charge.svg)
    """
    def __init__(self, arguments: list[str],
                    gml_context: GMLLineContext,
                    path_to_gml: Path | None = None,
                    image_color: dict = {}):
        super().__init__(arguments, gml_context, path_to_gml, image_color)

        one_charge_size_factor = 2.6
        self.one_charge = SVGImage(get_image(self.path_to_gml, "one_charge.svg"),
                                        height = one_charge_size_factor*gml_context.font_size,
                                        old_color={"red":0, "green":0, "blue":0},
                                        new_color=image_color) # Replace the black arrow with an arrow of same color as the class

        self.charge_effect = None # By default, a charge is empty
        if len(arguments) > 0:
            parser = GloomhavenParser(self.path_to_gml)
            charge_effect_lst = parser.gml_line_to_items(arguments[0], gml_context) # List of LineItems
            # charge_effect_lst may be an empty list if the user only gave macros as arguments
            if len(charge_effect_lst) > 0:
                charge_effect = charge_effect_lst[0]
                if isinstance(charge_effect.items[0], ExpCommand):
                    # Hack the ExpCommand's image so that it is of the correct color.
                    # Also slightly increase it's size.
                    charge_effect.items[0].new_image(SVGImage(get_image(self.path_to_gml, "experience.svg"),
                                                                height = 1.1*charge_effect.items[0].get_height(),
                                                                new_color=image_color))
                self.charge_effect = charge_effect

    def get_width(self):
        # Add a white blank after the charge.
        return self.one_charge.get_width()

    def get_height(self):
        return self.one_charge.get_height()

    def get_circle_center(self):
        """
        Return the distance between the left of the "one_charge" image and it's circle's center.
        """
        return 0.42*self.one_charge.get_width()

    def draw(self, cr: cairo.Context):
        cr.save()
        self.one_charge.draw(cr)
        if self.charge_effect is not None:
            # Do a translation on the x-axis of 0.6 and not 0.5 so the effect is centered into the charge (the circle)
            # and not in the image (which is rectangular due to the arrow).
            cr.translate(self.get_circle_center() - 0.5*self.charge_effect.get_width(),
                        self.one_charge.get_height()/2 - self.charge_effect.get_height() / 2)
            cr.move_to(0,0)
            self.charge_effect.draw(cr)
        cr.restore()

class ChargesCommand(AbstractCommand):
    """
    A class to represent X charges of something (ie the next X times you do something, do something else).
    Note: for now, we only allow for up to 6 charges. The layouts considered are the following:
    1,2 charges: 1 line (Inf O O)
    3 charges: Inf 0  0
                    0
    4 charges: Inf  O  O
                  O  O
    5 charges: Inf O  O  O
                    O  O
    6 charges: Inf O  O  O
                  O  O  O

    Implementation: this command is a monolithic block which doesn't entirely depend on the others commands as it
    breaks a bunch of rules: experience should be in the same color as the class, things should be centered in a
    rectangular image...
    """
    def __init__(self, arguments: list[str],
                    gml_context: GMLLineContext,
                    has_loss: bool,
                    path_to_gml: Path | None = None,
                    image_color: dict = {}):
        super().__init__(arguments, gml_context, path_to_gml, image_color)

        if len(arguments) > 6 or len(arguments) == 0:
            raise MismatchNoArguments("The '\\charges' and '\\charges_non_loss' commands take up to 6 arguments "
            f"but {len(arguments)} were given.")

        # Bypass ImageCommand as we do not want always want to put a blank space before and after those images.
        # The 1.4 scaling comes from ImageCommand
        self.infinity = SVGImage(get_image(self.path_to_gml,"infinity.svg"), height = 1.4*base_font_size)
        self.loss_image = None
        if has_loss:
            self.loss_image = SVGImage(get_image(self.path_to_gml,"loss.svg"), height = 1.4*base_font_size)

        # Will be used to get the correct spacing between charges items.
        self.blank = TextItem("  ", GMLLineContext(font_size = base_font_size))
        self.vertical_offset_factor = 0.9 # Factor used to compute the distance between the first and the second line.

        self.parsed_arguments = []
        for (i,arg) in enumerate(self.arguments):
            if len(arg) == 0:
                # Just put the default image
                charge_effect = []
            else:
                charge_effect = [arg]

            one_charge = OneChargeItem(charge_effect, gml_context, self.path_to_gml, image_color=image_color)
            self.parsed_arguments.append(one_charge)

    def get_width(self):
        # Whatever the layout, the first line is always the widest.
        n = len(self.parsed_arguments)
        charge_symbol_width = self.parsed_arguments[0].get_width()

        width = self.infinity.get_width()
        if self.loss_image is not None and n <= 2:
            # Only put loss symbol on the first line if there are less than 2 charges
            width += self.loss_image.get_width()
        if n == 1:
            return width + charge_symbol_width + self.blank.get_width()
        elif n >= 5:
            # 5 or 6 charges => 3 on the first line
            return width + 3*(charge_symbol_width + self.blank.get_width())
        else:
            # 2,3 or 4 charges => 2 on the first line
            return width + 2*(charge_symbol_width + self.blank.get_width())

    def get_height(self):
        # 1,2 arguments -> one line. 3,4,5,6 -> two lines
        charge_symbol_height = self.parsed_arguments[0].get_height()
        if len(self.parsed_arguments) <= 2:
            return charge_symbol_height
        else:
            return (1+self.vertical_offset_factor)* charge_symbol_height

    def draw(self, cr: cairo.Context):
        n =  len(self.parsed_arguments)
        if  n == 3 or n == 4:
            # For 3 or 4 charges, print 2 on the first line
            first_args = self.parsed_arguments[0:2]
        else:
            # Show all charges (if there are 1 or 2 in total) or 3 charges (if there are 5 or 6 in total)
            first_args = self.parsed_arguments[0:3]
        if n == 3 or n == 4:
            snd_args = self.parsed_arguments[2:]
        else:
            snd_args = self.parsed_arguments[3:]
        if self.loss_image is not None:
            if n <=2:
                first_args.append(self.loss_image)
            else:
                snd_args.append(self.loss_image)

        # Note: this is the same x_offset as in OneChargeItem
        first_line = LineItem([self.infinity, self.blank] + list_join(first_args, self.blank))
        cr.save()
        first_line.draw(cr)
        cr.restore()

        if len(snd_args) > 0:
            second_line = LineItem(list_join(snd_args, self.blank))
            cr.save()

            if n == 3 or n == 5 :
                # For 5 charges (or for 3 chages), the layout should be
                # Inf  O  O  O  and not  Inf  O  O  O
                #       O   O                O  O
                # ie the middle of the first charge on the second line should align with the arrow of the first charge.
                # Also note that the first line consists in "Inf, blank, O" and not just "Inf, O".
                cr.translate(self.infinity.get_width() + self.blank.get_width() + self.parsed_arguments[0].get_width() - self.parsed_arguments[0].get_circle_center(),
                        self.vertical_offset_factor*self.parsed_arguments[0].get_height())
            else:
                # For 4 or 6 charges, the  center of the first charge on the second line should be just under
                # the arrow of the infinity symbol
                cr.translate(self.infinity.get_width() - self.parsed_arguments[0].get_circle_center(),
                            self.vertical_offset_factor*self.parsed_arguments[0].get_height())
            second_line.draw(cr)
            cr.restore()

class ChargesLossCommand(ChargesCommand):
    '''
    A lazy wrapper around ChargesCommand, which displays a loss symbol after the charges.
    '''
    def __init__(self, arguments: list[str],
                    gml_context: GMLLineContext,
                    path_to_gml: Path | None = None,
                    image_color: dict = {}):
        super().__init__(arguments, gml_context, True, path_to_gml, image_color)

class ChargesNonLossCommand(ChargesCommand):
    '''
    A lazy wrapper around ChargesCommand, which doesn't display a loss symbol.
    '''
    def __init__(self, arguments: list[str],
                    gml_context: GMLLineContext,
                    path_to_gml: Path | None = None,
                    image_color: dict = {}):
        super().__init__(arguments, gml_context, False, path_to_gml, image_color)

class SummonCommand(AbstractCommand):
    """
    A class to show a summon. Like ChargesCommand, this is just one big block that breaks quite a lot of
    conventions.
    """
    def __init__(self, arguments: list[str],
                    gml_context: GMLLineContext,
                    path_to_gml: Path | None = None,
                    image_color: dict = {}):
        super().__init__(arguments, gml_context, path_to_gml, image_color)

        if len(arguments) != 6 and len(arguments) != 7:
            raise MismatchNoArguments(f"The '\\summon' commands take 6 or 7 arguments, but {len(arguments)} were given.")

        if len(arguments) == 6:
            image_path = get_image(self.path_to_gml, "summon_1_block.png")
        else:
            # 7 arguments = 2 blocks to write in
            image_path = get_image(self.path_to_gml, "summon_2_blocks.png")
        # 0.78*card_width => fits exactly the width of the card (from one colored border to the other)
        self.image =  GdkPixbuf.Pixbuf.new_from_file_at_scale(image_path, 0.78*card_width, -1, True)

        # Note: for those svgs, the 1.4 comes from the ImageCommand. We build them here so we don't have to
        # rebuild them every time we draw.
        colon = TextItem(": ", GMLLineContext(font_size=small_font_size))
        hp_image =[SVGImage(get_image(self.path_to_gml, "heal.svg"), 1.4*base_font_size), colon]
        move_image = [SVGImage(get_image(self.path_to_gml, "move.svg"), 1.4*base_font_size), colon]
        attack_image = [SVGImage(get_image(self.path_to_gml, "attack.svg"), 1.4*base_font_size), colon]
        range_image = [SVGImage(get_image(self.path_to_gml, "range.svg"), 1.4*small_font_size), colon]

        self.parsed_arguments = []
        parser = GloomhavenParser(self.path_to_gml)
        for (i,arg) in enumerate(arguments):
            if len(arg) == 0:
                if i == 0 or i > 4:
                    # Show nothing
                    self.parsed_arguments.append(TextItem("", GMLLineContext(font_size=small_font_size), path_to_gml=self.path_to_gml))
                else:
                    # Show a hyphen for if a summon doens't have a hp/move/attack/range
                    self.parsed_arguments.append(TextItem("-", GMLLineContext(font_size=small_font_size), path_to_gml=self.path_to_gml))
            else:
                if i == 0:
                    parsed_arg = parser.gml_line_to_items(arg, gml_context)
                    if len(parsed_arg) > 0: # This can happen if the user only gave macros and not gml commands
                        self.parsed_arguments.append(parsed_arg[0])
                    else:
                        self.parsed_arguments.append(TextItem("", GMLLineContext(font_size=small_font_size), path_to_gml=self.path_to_gml))
                elif i == 5 or i == 6:
                    # Parse in small the summon's characteristics
                    all_lines = parser.gml_line_to_items(arg, GMLLineContext(font_size=small_font_size),
                                                        width = 0.35*self.image.get_width())
                    self.parsed_arguments.append(ColumnItem(all_lines))
                else:
                    parsed_arg = parser.gml_line_to_items(arg, GMLLineContext(font_size=small_font_size))
                    if len(parsed_arg) > 0: # This can happen if the user only gave macros and not gml commands
                        self.parsed_arguments.append(parsed_arg[0])
                    else:
                        self.parsed_arguments.append(TextItem("-", GMLLineContext(font_size=small_font_size), path_to_gml=self.path_to_gml))

        self.hp_line = LineItem(hp_image + [self.parsed_arguments[1]])
        self.move_line = LineItem(move_image + [self.parsed_arguments[2]])
        self.attack_line = LineItem(attack_image + [self.parsed_arguments[3]])
        self.range_line = LineItem(range_image + [self.parsed_arguments[4]])

    def get_width(self):
        return self.image.get_width()

    def get_height(self):
        return self.image.get_height()

    def draw(self, cr: cairo.Context):
        relative_width = self.get_width()
        relative_height = self.get_height()

        # Background
        Gdk.cairo_set_source_pixbuf(cr, self.image, 0, 0)
        cr.paint()

        # Title: we try to center it. If it overlaps the image, we try to scoot it to the right, allowing
        # for bigger titles.
        cr.save()
        image_size = self.parsed_arguments[0].get_width()/2
        forbidden_space = 0.15*relative_width # Where the summon's image is
        x_translate = 0.5*relative_width - image_size
        if x_translate < forbidden_space:
            x_translate +=  forbidden_space - x_translate
        cr.translate(x_translate, 0.1*relative_height)
        cr.move_to(0,0)
        self.parsed_arguments[0].draw(cr)
        cr.restore()

        # Summon characteristics
        cr.save()
        # Top left of the first line: this is where the HP should be displayed
        cr.translate(0.225*relative_width, 0.4*relative_height)
        cr.move_to(0,0)
        # HP
        cr.save() # The associated restore will go back to the top left of the first line.
        self.hp_line.draw(cr)
        # Move
        cr.translate(0.25*relative_width, 0)
        cr.move_to(0,0)
        self.move_line.draw(cr)
        cr.restore()
        # Go down to the top left of the second line, where the attack should be displayed
        cr.save()
        cr.translate(0,0.275*relative_height)
        cr.move_to(0,0)
        # Attack
        self.attack_line.draw(cr)
        cr.restore()
        # Currently we are at the top left of the first line. We should now display range.
        # However, we should be careful as range is the only image in small, so it kind of messes up the layout.
        cr.translate(0.25*relative_width, 0.4*relative_height - self.range_line.get_height() /2) # Center at 0.4 time the height
        cr.move_to(0,0)
        self.range_line.draw(cr)

        cr.restore()

        # Summon special moves
        if len(self.parsed_arguments) == 6:
            # Center the text with regards to the available height
            cr.save()
            cr.translate(0.85*relative_width - self.parsed_arguments[5].get_width()/2,
                        0.625*relative_height - self.parsed_arguments[5].get_height()/2)
            cr.move_to(0,0)
            self.parsed_arguments[5].draw(cr)
            cr.restore()
        else:
            # First line
            cr.save()
            cr.translate(0.85*relative_width - self.parsed_arguments[5].get_width()/2, 0.4*relative_height)
            self.parsed_arguments[5].draw(cr)
            cr.move_to(0,0)
            cr.restore()
            # Second line
            cr.save()
            cr.translate(0.85*relative_width - self.parsed_arguments[6].get_width()/2, 0.7*relative_height)
            self.parsed_arguments[6].draw(cr)
            cr.move_to(0,0)
            cr.restore()

class AoECommand(AbstractCommand):
    def __init__(self, arguments: list[str],
                    gml_context: GMLLineContext,
                    path_to_gml: Path | None = None,
                    image_color: dict = {}):
        super().__init__(arguments, gml_context, path_to_gml, image_color)
        if len(arguments) != 1 :
            raise MismatchNoArguments(f"The '\\aoe' command takes 1 argument {len(arguments)} were given.")

        self.hexagons = HexagonDict()
        # May raise the AoeFileNotFound error. Let's not catch it: an AoE is probably more important than an image
        # so the user really should give a path (can't be ignored like an image.)
        aoe_path = get_aoe(path_to_gml, arguments[0])
        try:
            self.hexagons = HexagonDict.CreateFromFile(aoe_path)
        except Exception as e:
            raise InvalidAoEFile(f"The .aoe file {arguments[0]} couldn't be read. Please correct it and try again.")
        self.hex_grid = HexagonalGrid(base_font_size)

    def get_width(self):
        return self.hex_grid.get_width(self.hexagons)

    def get_height(self):
        return self.hex_grid.get_height(self.hexagons)

    def draw(self, cr: cairo.Context):
        self.hex_grid.draw(cr, self.hexagons)

class DividerLine(AbstractCommand):
    """
    In Jaws of the Lion, a divider line is a line of 9 white points. However, they aren't as high as normal
    text, so that's why we create a dedicated command and not just an alias.
    """
    def __init__(self, arguments: list[str],
                    gml_context: GMLLineContext,
                    path_to_gml: Path | None = None,
                    image_color: dict = {}):
        super().__init__(arguments, gml_context, path_to_gml, image_color)
        if len(arguments) !=0:
            raise MismatchNoArguments(f"The '\\divider_line' takes no arguments but {len(arguments)} were given.")

        divider_message = (". "*9).strip() # Add strip to remove last blank
        self.dotted_line = TextItem(divider_message, GMLLineContext(font_size=small_font_size),self.path_to_gml)

        self.height_percentage = 0.5 # Factor reducing the apparent width of this item (ie width as seen by the parser)
        # Reducing the apparent width isn't enough since text is written at the bottom of its bounding box,
        # and can therefore overlap text underneath.
        self.offset_percentage = 0.45 # Factor to reposition vertically the divider line

    def get_width(self):
        return self.dotted_line.get_width()

    def get_height(self):
        return self.height_percentage*self.dotted_line.get_height()

    def draw(self, cr: cairo.Context):
        cr.save()
        cr.translate(0, -self.offset_percentage*self.dotted_line.get_height())
        cr.move_to(0,0)
        self.dotted_line.draw(cr)
        cr.restore()


# Circular import required to allow commands to parse their arguments.
# What we really are doing in making parser.create_command a recursive function split over two files
# create_command -> Abstractcommand(args) -> create_command(args[0]) -> ...
from .gloomhavenparser import GloomhavenParser