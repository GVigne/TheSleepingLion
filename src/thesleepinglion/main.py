import cairo
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from tempfile import TemporaryDirectory
from pathlib import Path
import sys
import pkg_resources

from .gloomhaven.gloomhaven_constants import card_width, card_height
from .frosthaven.frosthaven_constants import fh_card_width, fh_card_height
from .frosthaven.frosthavenclass import FrosthavenClass
from .core.utils import show_parsing_errors, show_warning_errors
from .createHavenFromFile import create_haven_class_from_file
from .gui.main_window import MainWindow
from .backupFileHandler import GMLFileHandler

def thesleepinglion_main():
    version = pkg_resources.require("thesleepinglion")[0].version
    if len(sys.argv) == 1:
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
    else:
        print(f"You are using version {version} of The Sleeping Lion.")
        # The first argument should be some sort of path to a .gml file, the second the path to where the
        # PDF should be saved.
        path_to_gml = Path(sys.argv[1])
        if len(sys.argv) >= 3:
            path_to_pdf = Path(sys.argv[2])
        else:
            path_to_pdf = path_to_gml.with_suffix(".pdf")

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
            surface = cairo.PDFSurface(path_to_pdf, width, height)
            cr = cairo.Context(surface)
            for card in haven_class.cards:
                cr.save()
                haven_class.draw_card(card, cr)
                cr.restore()
                surface.show_page() # Save the page, so that each card is drawn on a separate page.
            surface.finish()
        else:
            # Print all the errors encountered during parsing.
            print("Something went wrong, and no file was generated. Please correct your GML file and try again.")
            print(show_parsing_errors(parsing_errors))