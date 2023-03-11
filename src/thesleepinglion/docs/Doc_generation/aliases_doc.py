"""
This script is not meant to be launched by or through The Sleeping Lion. It is used to automatically generate documentation,
and should be manually executed every patch/update to get the images corresponding to every alias.

Output example:
\subsubsection{attack}
\begin{tabularx}{\linewidth}{M{0.5\linewidth}M{0.5\linewidth}}
   $\backslash$attack\{3\}  & \includegraphics[scale=0.5]{Alias_images/attack.pdf} \\
   \multicolumn{2}{c}{$\backslash$attack\{\$x\$\} = Attack $\backslash$image\{attack.svg\} \$x\$} \\
\end{tabularx}

Note: run 'ps2pdf' on the .pdf file generated for the aliases. This will drastically reduce its size (16 Mo -> 440 Ko)
"""

from pathlib import Path
import gi
gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
import cairo
from pypdf import PdfWriter, PdfReader
from tempfile import TemporaryDirectory
from common import latexify
from thesleepinglion import GloomhavenClass, base_aliases, card_height, card_width

def alias_to_latex(subsection_name: str, example_string: str, path_to_image: Path, full_alias_description: str):
    """
    Backslashes should be escaped because they have a special meaning in python.
    We are not using f strings here as there are too many curly brackets - and rather than escape them all with an other
    curly bracket, let's just use the plus operator.
    """
    latex_string = "\\subsubsection{" + latexify(subsection_name) + "}\n"
    latex_string += """\\begin{minipage}{0.45\\linewidth}
\\raggedright
\\begin{spverbatim}\n"""
    latex_string += example_string + "\n"
    latex_string +="""\\end{spverbatim}
\\end{minipage}
\\begin{minipage}{0.45\\linewidth}
\\raggedleft
\\includegraphics[scale=0.5]"""
    latex_string += "{" + str(path_to_image) + "}\n"
    latex_string += """\end{minipage}
\\begin{center}
\\begin{BVerbatim}\n"""
    latex_string += full_alias_description + "\n"
    latex_string +="""\\end{BVerbatim}
\\end{center}\n\n"""
    return latex_string

## Directory to where the PDF will be saved
target_directory = Path("Aliases_images")
directory_for_latex = Path("Doc_generation/Aliases_images")
target_directory.mkdir(exist_ok=True)

## Build all necessary informations for all aliases
aliases_infos = {}
for alias in base_aliases:
    splitted = alias.split("=")
    example = splitted[0].replace("$x$", "3").strip()

    name = splitted[0][1:]
    i = 0
    while i<len(name):
        if name[i] == "{":
            break
        i+=1
    name = name[:i].strip()

    aliases_infos[name] = (example, alias)

## Build a dummy gml file
dummy_gml_text = "class:\n    name: ''\n"
for i, (alias_name, infos) in enumerate(aliases_infos.items()):
    dummy_gml_text = dummy_gml_text + f"{alias_name}:\n top: |\n    {infos[0]}\n"

with TemporaryDirectory() as tmpdir:
    tmpfile = Path(tmpdir) / "Untitled.gml"
    tmpfile.touch()
    with open(tmpfile, "w") as f:
        f.write(dummy_gml_text)
    gloomy_class = GloomhavenClass(tmpfile)

## Parse and generate PDF files for every alias. Also generate a latex file.
path_to_latex_string = target_directory / Path("aliases_in_latex.txt")
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

        if card.name == "loss" or card.name == "definitive_loss":
            # Crop half of the card instead of almost all of the card
            page.cropbox.lower_left = (0, 0.465*card_height)
            page.cropbox.lower_right = (card_width, 0.465*card_height)
            # Also crop the title
            page.cropbox.upper_left = (0, 0.9*card_height)
            page.cropbox.upper_right = (card_width, 0.9*card_height)
            output.add_page(page)
        else:
            line_center = card_height - card_height*0.32 # More or less where the Line object is centered
            line_height = 2*card.top_areas['center'][0].get_height()
            page.cropbox.lower_left = (0.15*card_width,line_center - line_height/2)
            page.cropbox.lower_right = (0.85*card_width, line_center - line_height/2)
            page.cropbox.upper_left = (0.15*card_width,line_center + line_height/2)
            page.cropbox.upper_right = (0.85*card_width, line_center + line_height/2)
            output.add_page(page)

        with open(save_path, 'wb') as out_file:
            # Overwrite the previous PDF files. Yes, it's ugly.
            output.write(out_file)

    example, full_alias = aliases_infos[card.name]
    latex_string += alias_to_latex(card.name, example, (directory_for_latex/card.name).with_suffix(".pdf"), full_alias)

with open(path_to_latex_string, "w") as f:
    f.write(latex_string)

