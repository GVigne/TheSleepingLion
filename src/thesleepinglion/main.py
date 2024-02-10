import cairo
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from tempfile import TemporaryDirectory
from pathlib import Path
import argparse
import pkg_resources

from .gloomhaven.gloomhaven_constants import card_width, card_height
from .frosthaven.frosthaven_constants import fh_card_width, fh_card_height
from .frosthaven.frosthavenclass import FrosthavenClass
from .core.utils import show_parsing_errors, show_warning_errors
from .core.export_utils import save_cards_as_deck
from .createHavenFromFile import create_haven_class_from_file
from .gui.main_window import MainWindow
from .backupFileHandler import GMLFileHandler

def thesleepinglion_main():
    version = pkg_resources.require("thesleepinglion")[0].version

    # Get CLI arguments
    argparser = argparse.ArgumentParser(
        description="""Run thesleepinglion without arguments to launch the UI.
                    You can also specify the following arguments to bypass the UI and directly parse a GML file to a PDF or PNG file.""",
            epilog="Thanks for using The Sleeping Lion!")
    argparser.add_argument("-i", "--input", action="store", metavar="",
                           help="path to the input .gml file")
    argparser.add_argument("-o", "--output", action="store", metavar="",
                           help="path to the output (parsed) file. If not specified, the output will be placed in the same folder as the input")
    argparser.add_argument("-f", "--format", action="store", metavar="", choices=["pdf", "png"], default="pdf",
                           help='format of the output file (by default, PDF). Must be either "pdf" or "png"')
    argparser.add_argument("-w", "--width", action="store", metavar="", default=5, type=int, choices=[i for i in range(1,11)],
                           dest="deck_width", help="the deck's width, in number of cards. Must be an integer betwen 1 and 10")

    arguments = argparser.parse_args()

    if arguments.input is None and arguments.output is None:
        # The default use for The Sleeping Lion. Fire up the GUI.
        with TemporaryDirectory() as tmpdir:
            tmpfile = Path(tmpdir) / "Untitled.gml"# A temporary file which will be deleted when the user quits TSL
            tmpfile.with_suffix(".gml").touch() # Create the temporary file.
            tempclass = create_haven_class_from_file(tmpfile)
            saved_file = GMLFileHandler(tmpfile)
            mainwindow = MainWindow(tempclass, saved_file, version)
            mainwindow.window.show_all()
            Gtk.main()
        pass
    elif arguments.input is None and arguments.output is not None:
        print(f"Please specify an input .gml file.")
    else:
        print(f"You are using version {version} of The Sleeping Lion.")
        path_to_gml = Path(arguments.input)
        if arguments.output is None:
            path_to_output = path_to_gml.with_suffix(f".{arguments.format}")
        else:
            path_to_output = Path(arguments.output)

        haven_class = create_haven_class_from_file(path_to_gml)
        parsing_errors, parsing_warnings = haven_class.parse_gml()
        if len(parsing_errors) == 0:
            # Everything is mostly fine!
            if len(parsing_warnings) > 0:
                print("Warning: the following non-blocking errors occurred when parsing the GML file.")
                print(show_warning_errors(parsing_warnings))
            width, height = card_width, card_height
            if isinstance(haven_class, FrosthavenClass):
                width, height = fh_card_width, fh_card_height
            save_cards_as_deck(haven_class, path_to_output, arguments.deck_width, width, height, arguments.format)
        else:
            # Print all the errors encountered during parsing.
            print("Something went wrong, and no file was generated. Please correct your GML file and try again.")
            print(show_parsing_errors(parsing_errors))