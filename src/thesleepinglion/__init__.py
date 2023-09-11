# Fonts must be loaded first, before anything else is.
import manimpango
import sys
from pkg_resources import resource_filename
from pathlib import Path

if sys.platform == "linux":
    manimpango.register_font(resource_filename("thesleepinglion.assets.gloomhaven.fonts", "majallab.ttf"))
    manimpango.register_font(resource_filename("thesleepinglion.assets.gloomhaven.fonts", "PirataOne-Regular.ttf"))
    manimpango.register_font(resource_filename("thesleepinglion.assets.frosthaven.fonts", "GermaniaOne-Regular.ttf"))
    manimpango.register_font(resource_filename("thesleepinglion.assets.frosthaven.fonts", "MarkaziText-Regular.ttf"))
else:
    # manimpango seems to fail for Windows 11 (works for Windows 10 though).
    # Call the Windows API directly.
    from ctypes import windll, byref, create_unicode_buffer
    def add_font(file):
        FR_PRIVATE = 0x10
        file = byref(create_unicode_buffer(file))
        windll.gdi32.AddFontResourceExW(file, FR_PRIVATE, 0)

    add_font(resource_filename("thesleepinglion.assets.gloomhaven.fonts", "majallab.ttf"))
    add_font(resource_filename("thesleepinglion.assets.gloomhaven.fonts", "PirataOne-Regular.ttf"))
    add_font(resource_filename("thesleepinglion.assets.frosthaven.fonts", "GermaniaOne-Regular.ttf"))
    add_font(resource_filename("thesleepinglion.assets.frosthaven.fonts", "MarkaziText-Regular.ttf"))

# Allow end-users to import a GloomhavenClass. This is required for the automatic documentation generation.
from .gloomhaven.gloomhavenclass import GloomhavenClass
from .gloomhaven.gloomhaven_aliases import base_aliases
from .gloomhaven.gloomhaven_constants import card_height, card_width
