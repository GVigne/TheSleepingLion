r"""
This script is not meant to be launched by or through The Sleeping Lion. It is used to automatically generate documentation,
and should be manually executed every patch/update to get the images corresponding to every command.

The latex code is identical to the one for commands.
"""
from common import latexify
from pathlib import Path
import gi
gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
import cairo
from pypdf import PdfWriter, PdfReader
from thesleepinglion import GloomhavenClass, card_height, card_width


def macro_to_latex(subsection_name: str, macro_example: str, path_to_image:str):
    latex_string = "\\subsection{" + latexify(subsection_name) + "}\n"
    latex_string += """\\textbf{\\underline{Arguments:}} Text goes here

\\textbf{\\underline{Description:}} Text goes here

\\textbf{\\underline{Example:}}

\\begin{minipage}{0.45\\linewidth}
\\raggedright
\\begin{spverbatim}
"""
    latex_string += macro_example + "\n" # Don"t latexify as it is in a verbatim environnment
    latex_string += """\\end{spverbatim}
\\end{minipage}
\\begin{minipage}{0.45\\linewidth}
\\raggedleft
\\includegraphics[scale=0.5]{"""
    latex_string += str(path_to_image) + "}" + "\n"
    latex_string += "\\end{minipage} \n\n"
    return latex_string

## Directory to where the PDF will be saved
target_directory = Path("Macros_images")
target_directory.mkdir(exist_ok=True)
directory_for_latex = Path("Doc_generation/Macros_images")

## Build all necessary informations for all aliases
gloomy_class = GloomhavenClass(Path("macros_doc.gml"))

## Parse and generate PDF files for every alias. Also generate a latex file.
path_to_latex_string = target_directory / Path("macros_in_latex.txt")
latex_string = ""
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

        if card.name == "column2" or card.name == "topleft" or card.name == "bottomright":
            # Positional macro -> show half of the card
            page.cropbox.lower_left = (0, 0.465*card_height)
            page.cropbox.lower_right = (card_width, 0.465*card_height)
            # Also crop the title
            page.cropbox.upper_left = (0, 0.9*card_height)
            page.cropbox.upper_right = (card_width, 0.9*card_height)
        else:
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

    latex_string += macro_to_latex(card.name, card.top_text, (directory_for_latex/card.name).with_suffix(".pdf"))

with open(path_to_latex_string, "w") as f:
    f.write(latex_string)

