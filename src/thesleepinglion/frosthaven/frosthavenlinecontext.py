from ..core.haven_type import Haven
from ..core.abstractGMLlinecontext import AbstractGMLLineContext
from .frosthaven_constants import *

class FrosthavenLineContext(AbstractGMLLineContext):
    def __init__(self, font: str = fh_card_font,
                font_size: int = fh_base_font_size,
                is_indented_context: bool = False,
                bold: bool = False,
                text_color: dict = {"red": 255, "green": 255, "blue": 255},
                class_color: dict = {"red": 0, "green": 0, "blue": 0}):
        super().__init__(font, font_size, is_indented_context, bold, text_color, class_color, Haven.FROSTHAVEN)
