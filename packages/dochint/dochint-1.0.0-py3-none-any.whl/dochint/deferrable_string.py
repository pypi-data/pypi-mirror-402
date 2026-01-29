from .state import State
import re
from typing import Callable, TypeAlias, Union

DeferrableString: TypeAlias = Union[str, Callable[State, str]]

deferred_string_prefix = '\uedef'

def _escape_deferred_prefix(text: str) -> str:
    return re.sub(re.escape(deferred_string_prefix),
                  f'{deferred_string_prefix};', text)

def _resolve_deferred_strings(text: str, ls: list[DeferrableString],
                             state: State) -> str:
    pattern = f'{re.escape(deferred_string_prefix)}([0-9]*);'
    def repl(match) -> str:
        i_str = match.group(1)
        if not i_str.isnumeric():
            return deferred_string_prefix

        i = int(i_str)
        s = ls[i]
        if isinstance(s, str):
            return s
        else:
            s_resolved = _resolve_deferred_strings(s(state), ls, state)
            ls[i] = s_resolved
            return s_resolved

    return re.sub(pattern, repl, text)

def _replace_deferred_strings_with_ellipsis(text: str) -> str:
    pattern = f'{re.escape(deferred_string_prefix)}([0-9]*);'
    def repl(match) -> str:
        i_str = match.group(1)
        if i_str.isnumeric():
            return '...'
        else:
            return deferred_string_prefix

    return re.sub(pattern, repl, text)
