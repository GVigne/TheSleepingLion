class AbstractGMLLineContext:
    """
    An abstract class to descript the context of a given GML line. Macros may change the context, and commands can
    query the context about the current color/size/font... and react accordingly. Note that positional macros should not interact
    with the context.
    An AbstractLineContext has 6 mandatory attributes (see __init__). It also holds a stack of contexts, so that
    an "undo" operation may be performed.
    """
    def __init__(self,
                font: str,
                font_size: int,
                is_small_context: bool,
                bold: bool,
                text_color: dict,
                class_color: dict):
        self.font = font
        self.font_size = font_size
        self.is_small_context = is_small_context
        self.bold = bold
        self.text_color = text_color
        self.class_color = class_color
        self.context_history = [] # A stack of AbstractLineContext, representing the previous states of the context.

    def new_context_effects(self):
        """
        This method should be overloaded to allow macros to change the context. Don't forget to create a push a new
        AbstractLineContext in the context_history stack.
        """
        pass

    def clear_last_effect(self):
        """
        This method should be overloaded to allow reverting to the previous state by popping the last context in
        the context_history stack.
        This method shouldn't do anything if the context history is empty.
        """
        pass

    def clear(self):
        """
        This method should be overloaded to revert the context to its inital state. Don't forget to reset the context_history stack.
        """
        pass