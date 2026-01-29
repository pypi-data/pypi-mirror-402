from . import deferrable_string
from . import exceptions
from . import _helper
from . import _macros
from .deferrable_string import DeferrableString
from .macro import ArgsMacro, _ArgType, RawMacro, Macro
from .state import State

import re
from typing import Dict, Optional, Union

_base_macros_dict = {'<': '&lt;',
                     '>': '&gt;',
                     '&': '&amp;',
                     '\'': '&apos;',
                     '"': '&quot;',
                     '\n': '',
                     'verb': RawMacro(_macros.verbatim_func),
                     'verbatim': RawMacro(_macros.verbatim_func),
                     'm': ArgsMacro(_macros.imath_func, '{t}'),
                     'math': ArgsMacro(_macros.imath_func, '{t}'),
                     'maths': ArgsMacro(_macros.imath_func, '{t}'),
                     'imath': ArgsMacro(_macros.imath_func, '{t}'),
                     'imaths': ArgsMacro(_macros.imath_func, '{t}'),
                     'mathblock': ArgsMacro(_macros.dmath_func, '{t}'),
                     'mathsblock': ArgsMacro(_macros.dmath_func, '{t}'),
                     'bmath': ArgsMacro(_macros.dmath_func, '{t}'),
                     'bmaths': ArgsMacro(_macros.dmath_func, '{t}'),
                     'dmath': ArgsMacro(_macros.dmath_func, '{t}'),
                     'dmaths': ArgsMacro(_macros.dmath_func, '{t}'),
                     'equation': ArgsMacro(_macros.equation_func, '[d]{i}{t}'),
                     'eqn': ArgsMacro(_macros.equation_func, '[d]{i}{t}'),
                     'id': ArgsMacro(_macros.id_func, '[d]{i}'),
                     'tref': ArgsMacro(_macros.tref_func, '{i}'),
                     'ref': ArgsMacro(_macros.ref_func, '{i}'),
                     'cite': ArgsMacro(_macros.cite_func, '{i}'),
                     'addbibitem': ArgsMacro(
                         _macros.addbibitem_func, '{i}{d}'),
                     'addbibliographyitem': ArgsMacro(
                         _macros.addbibitem_func, '{i}{d}'),
                     'addbibtextext': ArgsMacro(
                         _macros.addbibtextext_func, '{t}'),
                     'addbibtexfile': ArgsMacro(
                         _macros.addbibtexfile_func, '{i}'),
                     'bibliography': ArgsMacro(_macros.bibliography_func, ''),
                     'printbibliography': ArgsMacro(
                         _macros.bibliography_func, ''),
                     'footnote': ArgsMacro(_macros.footnote_func, '{d}'),
                     'footnotes': ArgsMacro(_macros.footnotes_func, ''),
                     'printfootnotes': ArgsMacro(_macros.footnotes_func, '')}

class _IncompleteArgsError(ValueError):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

def _get_bracket_enclosed(text_after_opening, lr, escapes):
    l = lr[0]
    r = lr[1]
    texts_to_match = [l, r, *escapes]
    regex = '|'.join(re.escape(text) for text in texts_to_match)

    depth = 1
    text_enclosed = ''
    len_consumed = 0
    for match in re.finditer(regex, text_after_opening):
        s = match.group()
        if s in escapes:
            text_enclosed += text_after_opening[len_consumed:match.start()]
            text_enclosed += escapes[s]
            len_consumed = match.end()
        else:
            depth += 1 if s==l else -1
            text_enclosed += text_after_opening[len_consumed:match.start()]
            len_consumed = match.end()
            if depth == 0:
                break

            # if not end of argument, add bracket to argument text
            text_enclosed += s
    else:
        raise _IncompleteArgsError('Could not find closing bracket.')

    return text_enclosed, len_consumed

def _get_arg_after_opening(text_after_opening: str, lr: str,
    arg_type: _ArgType, macros_dict: Dict[str, Macro], prefix: str,
    state: State, deferred_strs: list[DeferrableString]) -> [str, int]:

    escapes_id = {prefix+'[': '[', prefix+']': ']',
                  prefix+'{': '{', prefix+'}': '}', prefix+prefix: prefix}
    escapes_tex = {'\\[': '\\[', '\\]': '\\]', '\\{': '\\{', '\\}': '\\}'}

    if arg_type == _ArgType.ID:
        arg, n = _get_bracket_enclosed(text_after_opening, lr, escapes_id)
    elif arg_type == _ArgType.TEX:
        arg, n = _get_bracket_enclosed(text_after_opening, lr, escapes_tex)
    else: # arg_type == _ArgType.DOC:
        arg, n = _process_text_internal(text_after_opening, macros_dict,
            prefix, state, deferred_strs, brackets=lr)
    return arg, n

def _get_args(text: str, n_opts: int, n_args: int, arg_types: list[_ArgType],
    macros_dict: Dict[str, Macro], prefix: str, state: State,
    deferred_strs: list[DeferrableString]) -> [list[str], list[str], int]:

    len_consumed = 0

    # scan options
    opts = []
    for i in range(n_opts):
        # skip whitespace
        match = re.search('\\S', text[len_consumed:])
        if match is None:
            raise _IncompleteArgsError('Could not find opening bracket.')
        len_consumed += match.start()

        # if first non-whitespace character is not bracket, error
        bracket = text[len_consumed]
        if bracket == '{':
            # end of opts, skip to scanning args
            break
        elif bracket != '[':
            raise _IncompleteArgsError('Could not find opening bracket.')

        len_consumed += 1
        opt, n = _get_arg_after_opening(text[len_consumed:], '[]',
            arg_types[i], macros_dict, prefix, state, deferred_strs)
        opts.append(opt)
        len_consumed += n

    # scan arguments
    args = []
    for i in range(n_args):
        # skip whitespace
        match = re.search('\\S', text[len_consumed:])
        if match is None:
            raise _IncompleteArgsError('Could not find opening bracket.')
        len_consumed += match.start()

        # if first non-whitespace character is not bracket, error
        bracket = text[len_consumed]
        if bracket != '{':
            raise _IncompleteArgsError('Could not find opening bracket.')

        len_consumed += 1
        arg, n = _get_arg_after_opening(text[len_consumed:], '{}',
            arg_types[n_opts+i], macros_dict, prefix, state, deferred_strs)
        args.append(arg)
        len_consumed += n

    return opts, args, len_consumed

def _handle_macro(text: str, macro: Macro,
    macros_dict: Dict[str, Macro], prefix: str, state: State,
    deferred_strs: list[DeferrableString]) -> [DeferrableString, int]:

    if isinstance(macro, str):
        return macro, 0

    if isinstance(macro, RawMacro):
        return macro.func(text, state=state)

    # ArgsMacro

    try:
        opts, args, len_consumed = _get_args(text, macro.n_opts, macro.n_args,
            macro._arg_types, macros_dict, prefix, state, deferred_strs)
    except _IncompleteArgsError as e:
        raise exceptions.IncompleteMacroError(e.message)

    output = macro.func(*args, state=state, opts=opts)
    return output, len_consumed

def _process_text_internal(text: str, macros_dict: Dict[str, Macro],
    prefix: str, state: State, deferred_strs: list[DeferrableString],
    brackets: str='') -> [str, int]:

    len_prefix = len(prefix)
    if len(brackets) == 0:
        regex = re.escape(prefix)
    else:
        regex = f'{re.escape(prefix)}|[{re.escape(brackets)}]'

    output = ''
    len_consumed = 0
    bracket_level = 0
    while len(text) > 0:
        # scan to macro prefix or brackets
        match = re.search(regex, text)
        if match is None:
            # no macro prefix left, return remaining text
            output += deferrable_string._escape_deferred_prefix(text)
            len_consumed += len(text)
            return output, len_consumed

        # split text before and after match
        i = match.start()
        j = match.end()
        text_before = text[:i]
        text_match = match.group()
        text_after = text[j:]
        output += text_before
        len_consumed += j

        # handle brackets
        if text_match in brackets:
            l = brackets[0]
            if text_match == l:
                bracket_level += 1
            else:
                if bracket_level == 0:
                    return output, len_consumed
                else:
                    bracket_level -= 1
            output += text_match
            text = text_after
            continue

        # match is the macro prefix

        # handle missing macro command (macro prefix at EOF)
        if len(text_after) == 0:
            raise exceptions.MacroEmptyError()

        # handle escaped literal prefix
        if text_after.startswith(prefix):
            output += deferrable_string._escape_deferred_prefix(prefix)
            text = text_after[len_prefix:]
            len_consumed += len_prefix
            continue

        # handle escaped brackets
        if text_after[0] in brackets:
            output += text_after[0]
            text = text_after[1:]
            len_consumed += 1
            continue

        # read an identifier or non-identifier single character
        match = re.match('\\w+', text_after)
        if match is None:
            macro_command = text_after[0]
        else:
            macro_command = match.group(0)

        k = len(macro_command)
        text_after_command = text_after[k:]
        len_consumed += k

        # if this is not a valid macro command, error
        if not macro_command in macros_dict:
            raise exceptions.MacroCommandError(macro_command)

        # handle macro
        macro = macros_dict[macro_command]
        try:
            result, args_len_consumed = _handle_macro(text_after_command,
                macro, macros_dict, prefix, state, deferred_strs)
        except (exceptions.IncompleteMacroError,
                exceptions.CrossrefExistsError,
                exceptions.CrossrefNotFoundError) as e:
            raise type(e)(f'`{macro_command}`: {e.message}')

        if isinstance(result, str):
            output += result
        else:
            dp = deferrable_string.deferred_string_prefix
            output += f'{dp}{len(deferred_strs)};'
            deferred_strs.append(result)
        text = text_after_command[args_len_consumed:]
        len_consumed += args_len_consumed

    return output, len_consumed

def process_text(text: str, extra_macros: Optional[Dict[str, Macro]]=None,
                 prefix: str='\\', cwd: Optional[str]=None) -> str:
    '''Process macros in a single source text.

    Arguments:

    text: str
        Text to be processed, containing macros.
    extra_macros: Dict[str, Macro], optional
        Additional macro definitions.
    prefix: str, optional
        String that prefixes all macro commands. Defaults to '\\'.
    cwd: str, optional
        Directory for macros to resolve file paths from. Defaults to the
        process' working directory.

    Returns the processed text.
    '''

    if len(prefix) == 0:
        raise ValueError('prefix must be non-empty')

    if extra_macros is not None:
        macros_dict = _base_macros_dict | extra_macros
    else:
        macros_dict = _base_macros_dict

    state = State()
    state.cwd = cwd
    deferred_strs = []
    result, _ = _process_text_internal(text, macros_dict, prefix,
                                       state, deferred_strs)
    return deferrable_string._resolve_deferred_strings(result, 
                                                       deferred_strs, state)

def _compute_numbering_prefixes(texts: list[tuple[str, str]],
    numberings: Dict[str, Union[int, str]]) -> Dict[str, str]:

    filename_prefixes = dict()
    is_arabic = True
    i = 0
    for filename, _ in texts:
        i += 1

        if filename in numberings:
            numbering_set = numberings[filename]
            if isinstance(numbering_set, int):
                i = numbering_set
                is_arabic = True
            else:
                try:
                    i = int(numbering_set)
                    is_arabic = True
                except ValueError:
                    i = _helper.base26_to_int(numbering_set)
                    is_arabic = False

        if is_arabic:
            filename_prefixes[filename] = f'{i}.'
        else:
            filename_prefixes[filename] = f'{_helper.int_to_base26(i)}.'

    return filename_prefixes

def process_texts(texts: list[tuple[str, str]],
    numberings: Optional[Dict[str, Union[int, str]]]=None, prefix: str='\\',
    extra_macros: Optional[Dict[str, Macro]]=None, cwd: Optional[str]=None) \
        -> Dict[str, str]:
    '''Process macros in a sequence of text files.

    Arguments:

    texts: str
        A list of (filename, text) tuples for the texts to be processed.
    numberings: Dict[str, Union[int, str]], optional
        Files at which to (re)set chapter numbering/lettering, and what number
        or letter to reset them to; see the README for more information.
    prefix: str, optional
        String that prefixes all macro commands. Defaults to '\\'.
    extra_macros: Dict[str, Macro], optional
        Additional macro definitions.
    cwd: str, optional
        Directory for macros to resolve file paths from. Defaults to the
        process' working directory.

    Returns a dictionary of the processed texts, keyed by filename.

    Note that this function does not open any files or otherwise access the
    file system; the filenames provided are used purely for generating URIs.
    '''

    if len(texts) == 0:
        return {}

    if extra_macros is not None:
        macros_dict = _base_macros_dict | extra_macros
    else:
        macros_dict = _base_macros_dict

    filename_prefixes = _compute_numbering_prefixes(texts,
        (numberings if numberings is not None else dict()))

    state = State()
    state.cwd = cwd
    deferred_strs = []
    results_deferrable = {}
    for filename, text in texts:
        state.filename = filename
        state._crossref_chapter_prefix = filename_prefixes[filename]
        result, _ = _process_text_internal(text, macros_dict, prefix,
                                           state, deferred_strs)
        results_deferrable[filename] = result

    results = {}
    for filename, text in results_deferrable.items():
        state.filename = filename
        state._crossref_chapter_prefix = filename_prefixes[filename]
        result = deferrable_string._resolve_deferred_strings(
            text, deferred_strs, state)
        results[filename] = result
    return results
