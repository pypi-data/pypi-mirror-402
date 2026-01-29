import html
import re
from xml.sax.saxutils import quoteattr

def href(id, current_fname, dest_fname):
    if (dest_fname is None) or (current_fname == dest_fname):
        return quoteattr(f'#{id}')
    else:
        return quoteattr(f'{dest_fname}#{id}')

def numbered_character_entities(text):
    def numbered_entity_repl(named_entity_match):
        named_entity = named_entity_match.group()
        entity_str = html.unescape(named_entity)
        result = ''
        for c in entity_str:
            result += f'&#{ord(c)};'
        return result

    return re.sub('&[^;]*;', numbered_entity_repl, text)

def base26_to_int(b26):
    b26_lower = b26.lower()
    result = 0
    for c in b26_lower:
        c_value = ord(c) - ord('a') + 1
        if not 1 <= c_value <= 26:
            raise ValueError(f'Invalid base 26 string `{b26}`')
        result *= 26
        result += c_value
    return result

def int_to_base26(n):
    result = ''
    while n > 0:
        i = n % 26
        if i == 0:
            i = 26
        n -= i
        n //= 26
        result = chr(i + ord('A') - 1) + result
    return result
