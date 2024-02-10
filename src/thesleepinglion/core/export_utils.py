import cairo as cairo
from pathlib import Path
from .abstracthavenclass import AbstractHavenClass


def save_cards_as_deck(haven_class: AbstractHavenClass,
                       save_path: Path,
                       deck_width: int,
                       card_width: int,
                       card_height: int,
                       format: str = "pdf"): # pdf or png
        """
        Fit as many cards on an A4 sheet (ie like when printing)
        """
        deck_height = len(haven_class.cards)//deck_width + 1
        if format == "pdf":
            surface = cairo.PDFSurface(save_path, deck_width*card_width, deck_height*card_height)
        else:
            surface = cairo.ImageSurface(cairo.FORMAT_RGB24, deck_width*card_width, deck_height*card_height)
        cr = cairo.Context(surface)
        cr.move_to(0,0)
        for i, card in enumerate(haven_class.cards):
            cr.save()
            cr.translate((i % deck_width)*card_width, (i//deck_width)*card_height)
            cr.move_to(0,0)
            haven_class.draw_card(card, cr)
            cr.restore()
        # Save the file
        if format == "pdf":
            surface.finish()
        else:
            surface.write_to_png(save_path)