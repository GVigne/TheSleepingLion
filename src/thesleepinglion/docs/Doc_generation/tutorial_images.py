r"""
This script is not meant to be launched by or through The Sleeping Lion. It is used to automatically generate image
used in the tutorial.
"""
from common import latexify
from pathlib import Path
import gi
gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
import cairo
from pypdf import PdfWriter, PdfReader
from thesleepinglion import GloomhavenClass, card_height, card_width

## Directory to where the PDF will be saved
target_directory = Path("Tutorial_images")
target_directory.mkdir(exist_ok=True)

gloomy_class = GloomhavenClass(Path("tutorial_images.gml"))

## Parse and generate PDF files for every example.
gloomy_class.parse_gml()
for card in gloomy_class.cards:
    save_path = (target_directory / f"{card.name}").with_suffix(".pdf")
    surface = cairo.PDFSurface(save_path, card_width, card_height)
    cr = cairo.Context(surface)
    gloomy_class.draw_card(card, cr)
    surface.finish()
    with open(save_path, "rb") as in_file:
        input = PdfReader(in_file)
        output = PdfWriter()
        page = input.pages[0]

        line_center = card_height - card_height*0.32 # More or less where the Line object is centered
        line_height = 1.05*max([col.get_height() for col in card.top_areas['center']])

        page.cropbox.lower_left = (0.11*card_width,line_center - line_height/2)
        page.cropbox.lower_right = (0.89*card_width, line_center - line_height/2)
        page.cropbox.upper_left = (0.11*card_width,line_center + line_height/2)
        page.cropbox.upper_right = (0.89*card_width, line_center + line_height/2)
        output.add_page(page)

        with open(save_path, 'wb') as out_file:
            # Overwrite the previous PDF files. Yes, it's ugly.
            output.write(out_file)