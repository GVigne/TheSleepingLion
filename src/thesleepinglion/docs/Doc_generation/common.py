def latexify(python_string: str):
    """
    Do the following conversions:
    '\' -> $\backslash$
    '{', '}', '$', '_'-> '\{', '\}', '\$', '\_'
    """
    transposition_dict = {"{":'\\{',
                          "}": '\\}',
                          "$": '\\$',
                          "_": "\\_",
                          "\\": '$\\backslash$'
                        }
    return python_string.translate(python_string.maketrans(transposition_dict))