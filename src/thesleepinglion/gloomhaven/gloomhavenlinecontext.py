from .gloomhaven_constants import *
from ..core.abstractGMLlinecontext import AbstractGMLLineContext
from ..core.haven_type import Haven

class GloomhavenLineContext(AbstractGMLLineContext):
    """
    Context for Gloomhaven formatting.
    """
    @staticmethod
    def CreateFromIndentation(is_indented_context: bool, class_color: dict):
        """
        Note: path_to_gml MUST be a Path object, not a string.
        """
        font_size = base_font_size
        if is_indented_context:
            font_size = small_font_size
        return GloomhavenLineContext(font_size = font_size, is_indented_context=is_indented_context, class_color=class_color)

    def __init__(self,
                font: int = card_font,
                font_size: int = base_font_size,
                is_indented_context: bool = False,
                bold: bool = False,
                text_color: dict = {"red": 255, "green": 255, "blue": 255}, # By default, text is in white
                class_color: dict = {"red": 0, "green": 0, "blue": 0}, # By default, class's color is black
                banner_background: bool = False):
        super().__init__(font, font_size, is_indented_context, bold, text_color, class_color, Haven.GLOOMHAVEN)

        self.is_indented_context = is_indented_context
        if self.is_indented_context:
            self.font_size = small_font_size
        self.banner_background = banner_background

    def new_context_effects(self,
                            font: int = None,
                            font_size: int = None,
                            text_color: dict = None,
                            bold: bool = None,
                            banner_background: bool = None):
        last_context = GloomhavenLineContext(self.font, self.font_size, self.is_indented_context,
                                            self.bold, self.text_color, self.class_color, self.banner_background)
        self.context_history.append(last_context)
        if font is not None:
            self.font = font
        if font_size is not None:
            self.font_size = font_size
        if text_color is not None:
            self.text_color = text_color
        if bold is not None:
            self.bold = bold
        if banner_background is not None:
            self.banner_background = banner_background

    def clear_last_effect(self):
        """
        Note that we can't clear the "black banner" effect.
        """
        try:
            last_context = self.context_history.pop()
            self.font = last_context.font
            self.font_size = last_context.font_size
            self.text_color = last_context.text_color
            self.bold = last_context.bold
        except IndexError:
            pass

    def clear(self):
        """
        Once again, the "black banner" effect can't be undone or cleared.
        """
        self.font = card_font
        self.bold = False
        self.text_color = {"red": 255, "green": 255, "blue": 255}

        size = base_font_size
        if self.is_indented_context:
            size = small_font_size
        self.font_size = size

        self.context_history = []