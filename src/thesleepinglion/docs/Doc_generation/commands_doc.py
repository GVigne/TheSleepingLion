r"""
This script is not meant to be launched by or through The Sleeping Lion. It is used to automatically generate documentation,
and should be manually executed every patch/update to get the images corresponding to every command.

Output example (note that line break do matter here):
\subsection{image}
\textbf{\underline{Arguments:}} Text goes here

\textbf{\underline{Description:}} Text goes here

\textbf{\underline{Example:}}

\begin{minipage}{0.45\linewidth}
\raggedright
\begin{spverbatim}
\attack{2}....
\end{spverbatim}
\end{minipage}
\begin{minipage}{0.45\linewidth}
\raggedleft
\includegraphics[scale=0.5]{image.pdf}
\end{minipage}

"""
from common import latexify
from pathlib import Path
import gi
gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
import cairo
from pypdf import PdfWriter, PdfReader
from thesleepinglion import GloomhavenClass, card_height, card_width


def command_to_latex(subsection_name: str, command_example: str, path_to_image:str):
    latex_string = "\\subsection{" + latexify(subsection_name) + "}\n"
    latex_string += """\\textbf{\\underline{Arguments:}} Text goes here

\\textbf{\\underline{Description:}} Text goes here

\\textbf{\\underline{Example:}}

\\begin{minipage}{0.45\\linewidth}
\\raggedright
\\begin{spverbatim}
"""
    latex_string += command_example + "\n" # Don"t latexify as it is in a verbatim environnment
    latex_string += """\\end{spverbatim}
\\end{minipage}
\\begin{minipage}{0.45\\linewidth}
\\raggedleft
\\includegraphics[scale=0.5]{"""
    latex_string += str(path_to_image) + "}" + "\n"
    latex_string += "\\end{minipage} \n\n"
    return latex_string

## Directory to where the PDF will be saved
target_directory = Path("Commands_images")
target_directory.mkdir(exist_ok=True)
directory_for_latex = Path("Doc_generation/Commands_images")

## Build all necessary informations for all aliases
gloomy_class = GloomhavenClass(Path("commands_doc.gml"))

## Parse and generate PDF files for every alias. Also generate a latex file.
path_to_latex_string = target_directory / Path("commands_in_latex.txt")
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

        line_center = card_height - card_height*0.32 # More or less where the Line object is centered
        line_height = 1.05*card.top_areas['center'][0].get_height()
        page.cropbox.lower_left = (0.11*card_width,line_center - line_height/2)
        page.cropbox.lower_right = (0.89*card_width, line_center - line_height/2)
        page.cropbox.upper_left = (0.11*card_width,line_center + line_height/2)
        page.cropbox.upper_right = (0.89*card_width, line_center + line_height/2)
        output.add_page(page)

        with open(save_path, 'wb') as out_file:
            # Overwrite the previous PDF files. Yes, it's ugly.
            output.write(out_file)

    latex_string += command_to_latex(card.name, card.top_text, (directory_for_latex/card.name).with_suffix(".pdf"))

with open(path_to_latex_string, "w") as f:
    f.write(latex_string)

