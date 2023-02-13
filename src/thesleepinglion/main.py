import cairo
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

from .constants import card_width, card_height
from .items import *
from .commands import *
from .utils import show_parsing_errors, show_warning_errors
from .gloomhavenclass import GloomhavenClass
from .gui.main_window import MainWindow
from .backupFileHandler import GMLFileHandler
from tempfile import TemporaryDirectory
from pathlib import Path
import sys
import pkg_resources


def thesleepinglion_main():
    version = pkg_resources.require("thesleepinglion")[0].version
    if len(sys.argv) == 1:
        # The default use for The Sleeping Lion. Fire up the GUI.
        with TemporaryDirectory() as tmpdir:
            tmpfile = Path(tmpdir) / "Untitled.gml"# A temporary file which will be deleted when the user quits TSL
            tmpfile.with_suffix(".gml").touch() # Create the temporary file.
            tempclass = GloomhavenClass(tmpfile)
            saved_file = GMLFileHandler(tmpfile)
            mainwindow = MainWindow(tempclass, saved_file, version)
            mainwindow.window.show_all()
            Gtk.main()
    else:
        print(f"You are using version {version} of The Sleeping Lion.")
        # The first argument should be some sort of path to a .gml file, the second the path to where the
        # PDF should be saved.
        path_to_gml = Path(sys.argv[1])
        if len(sys.argv) >= 3:
            path_to_pdf = Path(sys.argv[2])
        else:
            path_to_pdf = path_to_gml.with_suffix(".pdf")

        gloomhaven_class = GloomhavenClass(path_to_gml)
        parsing_errors, parsing_warnings = gloomhaven_class.parse_gml()
        if len(parsing_errors) == 0:
            # Everything is mostly fine!
            if len(parsing_warnings) > 0:
                print("Warning: the following non-blocking errors occurred when parsing the GML file.")
                print(show_warning_errors(parsing_warnings))

            surface = cairo.PDFSurface(path_to_pdf, card_width, card_height)
            cr = cairo.Context(surface)
            for card in gloomhaven_class.cards:
                cr.save()
                gloomhaven_class.draw_card(card, cr)
                cr.restore()
                surface.show_page() # Save the page, so that each card is drawn on a separate page.
            surface.finish()
        else:
            # Print all the errors encountered during parsing.
            print("Something went wrong, and no file was generated. Please correct your GML file and try again.")
            print(show_parsing_errors(parsing_errors))