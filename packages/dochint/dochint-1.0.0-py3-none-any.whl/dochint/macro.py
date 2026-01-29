from .deferrable_string import DeferrableString
from .state import State

from enum import auto, Enum
import re
from typing import Callable, Dict, NamedTuple, Protocol, TypeAlias, Union

class ArgsMacroFunction(Protocol):
    '''Type for the handler function of an ArgsMacro.'''
    def __call__(self, *args: str, state: State=None,
                 opts: list[str]=[]) -> DeferrableString:
        '''Handler function for an ArgsMacro.

        Arguments:

        *args: str
            Mandatory macro arguments. For "document-like" arguments, this may
            contain escape sequences representing deferred strings, of the form
            f'{deferred_string_prefix}{integer_id};', with a literal occurrence
            of deferred_string_prefix being represented as
            f'{deferred_string_prefix};'. For this reason, it is easiest not to
            parse document-like input at all, only pass it through
            unaltered or concatenated with other strings.
        opts: list[str]
            List of optional macro arguments.
        state: State
            State object for current processing context.

        Returns a DeferrableString for the output text of the macro. The
        returned string, either directly or deferred, may contain the same
        deferred string escape sequences as a "document-like" argument. Thus,
        any use of the literal deferred_string_prefix character in the output
        should be escaped as f'{deferred_string_prefix};'.
        '''
        pass

class _ArgType(Enum):
    ID = 0
    TEX = 1
    DOC = 2

def _process_arg_spec(arg_spec: str) -> [int, int, list[_ArgType]]:
    msg = f'invalid argument specification \'{arg_spec}\''
    arg_spec_stripped = re.sub('\\s', '', arg_spec)
    if len(arg_spec_stripped) % 3 != 0:
        raise ValueError(msg)

    arg_spec_lower = arg_spec_stripped.lower()
    thirds = (arg_spec_lower[0::3], arg_spec_lower[1::3], arg_spec_lower[2::3])

    n_opts = 0
    n_args = 0
    arg_types = []
    finished_opts = False
    for opening, arg_char, closing in zip(*thirds):
        if opening+closing not in {'{}', '[]'}:
            raise ValueError(msg)

        if opening == '{' and not finished_opts:
            finished_opts = True
        elif opening == '[' and finished_opts:
            raise ValueError(msg)

        try:
            arg_type_dict = {'i': _ArgType.ID,
                             't': _ArgType.TEX,
                             'd': _ArgType.DOC}
            arg_type = arg_type_dict[arg_char]
        except KeyError:
            raise ValueError(msg)

        arg_types.append(arg_type)
        if finished_opts:
            n_args += 1
        else:
            n_opts += 1

    return n_opts, n_args, arg_types

class ArgsMacro:
    '''Object representing a macro with arguments in brackets.'''
    def __init__(self, func: ArgsMacroFunction, arg_spec: str):
        '''Initialiser for ArgsMacro.

        Arguments:

        func: ArgsMacroFunction
            Macro handler function
        arg_spec: str
            String specifying the macro arguments. This should be a sequence
            of square brackets followed by a sequence of curly brackets, all
            with one of three letters ('i', 't', or 'd') enclosed in them.
            Examples of valid arg_spec strings include '[d]{i}{t}', '{d}', or
            ''. Each pair of brackets represents a macro argument, with square
            brackets representing optional arguments and curly brackets
            representing mandatory arguments, and the letter representing
            the type of input text parsing for the argument, 'i' for
            "identifier-like" arguments, 't' for "TeX-like" arguments, and 'd'
            for "document-like" arguments.

        Exceptions raised:

        ValueError:
            Raised if arg_spec is invalid.
        '''
        self.func = func
        n_opts, n_args, arg_types = _process_arg_spec(arg_spec)
        self.n_opts = n_opts
        self.n_args = n_args
        self._arg_types = arg_types

class RawMacroFunction(Protocol):
    '''Type for the handler function of a RawMacro.'''
    def __call__(self, text: str,
                 state: State=None) -> [DeferrableString, int]:
        '''Handler function for a RawMacro.

        Arguments:

        text: str
            Full remaining text of the current file after the macro command.
        state: State
            State object for current processing context.

        Returns [DeferrableString, int], the former of which is the output text
        of the macro, and the latter of which is the number of characters
        following the macro command that are consumed by the macro and replaced
        with its output text.
        '''
        pass

class RawMacro(NamedTuple):
    '''Object representing a macro whose input is all following text.

    Members:
    func: RawMacroFunction
        The macro handler function.
    '''
    func: RawMacroFunction

Macro: TypeAlias = Union[str, ArgsMacro, RawMacro]
