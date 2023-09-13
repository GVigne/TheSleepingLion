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

    def new_context_effects(self,
                            font_size: int = None):
        last_context = FrosthavenLineContext(self.font, self.font_size, self.is_indented_context,
                                            self.bold, self.text_color, self.class_color)
        self.context_history.append(last_context)
        if font_size is not None:
            self.font_size = font_size

    def clear_last_effect(self):
        try:
            last_context = self.context_history.pop()
            self.font = last_context.font
            self.font_size = last_context.font_size
            self.bold = last_context.bold
            self.text_color = last_context.text_color
        except IndexError:
            pass