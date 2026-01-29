'''A macro processor for authoring HTML documents.

The main entry points for this package are the process_text and process_texts
functions. The remainder of the Python API is used to define custom macros;
see Macro for more information. There is also a command-line interface to
dochint; see the README for more information.

For information about the behaviour of dochint, including how macro processing
works and which macros are available, see the README; such information is
beyond the scope of this package's docstrings.
'''

from .deferrable_string import DeferrableString, deferred_string_prefix
from .exceptions import (MacroCommandError,
                         MacroEmptyError,
                         IncompleteMacroError,
                         LaTeXMathsError,
                         LaTeXMathError,
                         CrossrefNotFoundError,
                         CrossrefExistsError,
                         CitationError,
                         BibTeXError,
                         FootnoteError)
from .macro import (ArgsMacroFunction,
                    RawMacroFunction,
                    ArgsMacro,
                    RawMacro,
                    Macro)
from .state import State
from .processor import process_text, process_texts

__all__ = ['DeferrableString', 'deferred_string_prefix',
           'MacroCommandError',
           'MacroEmptyError',
           'IncompleteMacroError',
           'LaTeXMathsError',
           'LaTeXMathError',
           'CrossrefNotFoundError',
           'CrossrefExistsError',
           'CitationError',
           'BibTeXError',
           'FootnoteError',
           'ArgsMacroFunction',
           'RawMacroFunction',
           'ArgsMacro',
           'RawMacro',
           'Macro',
           'State',
           'process_text', 'process_texts']
