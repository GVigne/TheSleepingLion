from ..core.haven_type import Haven
from ..core.abstractGMLlinecontext import AbstractGMLLineContext
from .frosthaven_constants import *

class FrosthavenLineContext(AbstractGMLLineContext):
    def __init__(self, font: str = fh_card_font,
                font_size: int = fh_base_font_size,
                is_indented_context: bool = False,
                bold: bool = False,
                text_color: dict = {"red": 255, "green": 255, "blue": 255},
                class_color: dict = {"red": 0, "green": 0, "blue": 0},
                image_size: int = fh_small_image_size):
        super().__init__(font, font_size, is_indented_context, bold, text_color, class_color, Haven.FROSTHAVEN)
        self.image_size = image_size
        if self.is_indented_context: # If this is a secondary line (which uses a whitish background), use small font for images
            self.image_size = fh_small_image_size

    def new_context_effects(self,
                            font_size: int = None,
                            image_size: int = None):
        last_context = FrosthavenLineContext(self.font, self.font_size, self.is_indented_context,self.bold,
                                            self.text_color, self.class_color, self.image_size)
        self.context_history.append(last_context)
        if font_size is not None:
            self.font_size = font_size
        if image_size is not None:
            self.image_size = image_size

    def clear_last_effect(self):
        try:
            last_context = self.context_history.pop()
            self.font = last_context.font
            self.font_size = last_context.font_size
            self.bold = last_context.bold
            self.text_color = last_context.text_color
            self.image_size = last_context.image_size
        except IndexError:
            pass

    def clear(self):
        self.font = fh_card_font
        self.font_size = fh_base_font_size
        self.bold = False
        self.text_color = {"red": 255, "green": 255, "blue": 255}

        img_size = fh_small_image_size
        if self.is_indented_context:
            img_size = fh_medium_font_size
        self.image_size = img_size

        self.context_history = []
