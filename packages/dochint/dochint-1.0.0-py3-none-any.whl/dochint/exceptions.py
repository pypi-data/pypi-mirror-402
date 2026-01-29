class MacroCommandError(ValueError):
    '''Error raised for an invalid macro command.

    Members:

    message: str
        The invalid macro command identifier.
    '''
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class MacroEmptyError(ValueError):
    '''Error raised for a macro prefix at the end of a string/file.'''
    pass

class IncompleteMacroError(ValueError):
    '''Error raised for a macro whose input is incomplete.

    Members:

    message: str
        The macro command identifier.
    '''
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class LaTeXMathsError(ValueError):
    '''Error raised for invalid LaTeX maths notation input.

    Members:

    message: str
        The invalid LaTeX text.
    '''
    def __init__(self, message):
        super().__init__(message)
        self.message = message

LaTeXMathError = LaTeXMathsError

class CrossrefNotFoundError(KeyError):
    '''Error raised for an undefined cross-reference identifier.

    Members:

    message: str
        The undefined cross-reference identifier.
    '''
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class CrossrefExistsError(KeyError):
    '''Error raised for a cross-reference identifier that is defined twice.

    Members:

    message: str
        The twice-defined cross-reference identifier.
    '''
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class CitationError(KeyError):
    '''Error raised for an undefined citation identifier.

    Members:

    message: str
        The undefined citation identifier.
    '''
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class BibTeXError(ValueError):
    '''Error raised for invalid BibTeX input.

    Members:

    message: str
        The invalid BibTeX text.
    '''
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class FootnoteError(ValueError):
    '''Error raised for a footnote that is declared but never printed.

    Members:

    message: str
        The footnote text, possibly abridged with ellipses.
    '''
    def __init__(self, message):
        super().__init__(message)
        self.message = message
