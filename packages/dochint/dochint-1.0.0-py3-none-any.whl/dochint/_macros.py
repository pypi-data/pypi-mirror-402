from . import exceptions, deferrable_string, _helper
from .deferrable_string import DeferrableString
from .state import State

import html
from typing import Any, Callable, Dict, Tuple
from xml.sax.saxutils import quoteattr
import latex2mathml.converter
import pybtex
import pybtex.database

def verbatim_func(text: str, **kwargs) -> [str, int]:
    if len(text) == 0:
        raise exceptions.IncompleteMacroError(
            'Could not find opening delimiter.')

    if len(text) == 1:
        raise exceptions.IncompleteMacroError(
            'Could not find closing delimiter')

    delimiter = text[0]
    text = text[1:]
    len_consumed = 1

    end = text.find(delimiter)
    if end < 0:
        raise exceptions.IncompleteMacroError(
            'Could not find closing delimiter.')

    verbatim_text = text[:end]
    len_consumed += end + 1

    escaped_text = html.escape(verbatim_text)
    return escaped_text, len_consumed

def _math_core(latex: str, display: str) -> str:
    try:
        mathml = latex2mathml.converter.convert(latex, display=display)
    except Exception as e:
        raise exceptions.LaTeXMathsError(f'{type(e)}')

    latex_escaped = quoteattr(latex)
    i = len('<math ')
    mathml = mathml[:i] + f'alttext={latex_escaped} ' + mathml[i:]
    return mathml

def imath_func(latex: str, **kwargs) -> str:
    return _math_core(latex, 'inline')

def dmath_func(latex: str, **kwargs) -> str:
    return _math_core(latex, 'block')

def equation_func(id: str, latex: str, state: State, opts: list[str]) -> str:
    if len(opts) > 0:
        text = opts[0]
        state.set_crossref(id, text=text)
    else:
        state.set_crossref(id)
        text = state.get_crossref_text(id)

    fig = f'<figure class=\'equation\' id={quoteattr(id)}>'
    fig += _math_core(latex, 'block')
    fig += f'<figcaption>({text})</figcaption>'
    fig += '</figure>'
    return fig

def id_func(id: str, state: State, opts: list[str]) -> str:
    if len(opts) > 0:
        text = opts[0]
        state.set_crossref(id, text=text)
    else:
        state.set_crossref(id)

    return quoteattr(id)

def tref_func(id: str, state: State, opts: list[str]) -> DeferrableString:
    def deferred_str_func(state: State) -> str:
        return state.get_crossref_text(id)

    if state.contains_crossref(id):
        return deferred_str_func(state)
    else:
        return deferred_str_func

def ref_func(id: str, state: State, opts: list[str]) -> DeferrableString:
    filename = state.filename

    def deferred_str_func(state: State) -> str:
        return state.get_crossref_anchor(id)

    if state.contains_crossref(id):
        return deferred_str_func(state)
    else:
        return deferred_str_func

class _BibliographyState:
    def __init__(self):
        self.citation_order: Dict[str, int] = dict()
        self.bibliography_items: Dict[str, str] = dict()
        self.bibtex_data: list[pybtex.database.BibliographyData, str] = []
        self.bibliography_present: bool = False
        self.bibliography_filename: str = None
        self.have_generated_bibliography: bool = False

def _get_or_init(state: State, attr: str, init_func: Callable) -> Any:
    if attr not in state:
        obj = init_func()
        state[attr] = obj
        return obj
    else:
        return state[attr]

def cite_func(ids: str, state: State, **kwargs) -> DeferrableString:
    bib_state = _get_or_init(state, '_bibliography', _BibliographyState)

    filename = state.filename
    id_list = ids.split(',')
    for id in id_list:
        if id in bib_state.citation_order:
            continue
        index = len(bib_state.citation_order)
        bib_state.citation_order[id] = index

    def deferred_str_func(state: State) -> str:
        bib_state = state['_bibliography']
        if not bib_state.bibliography_present:
            raise exceptions.CitationError(
                'Citations present but no bibliography')

        links = dict()
        for id in id_list:
            index = bib_state.citation_order[id]
            href = _helper.href(id, filename, bib_state.bibliography_filename)
            link = f'<a href={href}>{index+1}</a>'
            links[link] = index
        sorted_links = sorted(links, key=links.get)
        citation = f'[{','.join(sorted_links)}]'
        return citation

    return deferred_str_func

def addbibitem_func(id: str, bib: str, state: State, **kwargs) -> str:
    bib_state = _get_or_init(state, '_bibliography', _BibliographyState)
    bib_state.bibliography_items[id] = bib
    return ''

def addbibtextext_func(bibtex: str, state: State,**kwargs) -> str:
    try:
        db = pybtex.database.parse_string(bibtex, 'bibtex')
    except Exception as e:
        raise exceptions.BibTeXError(f'{type(e)}')

    bib_state = _get_or_init(state, '_bibliography', _BibliographyState)
    bib_state.bibtex_data.append((db, bibtex))
    return ''

def addbibtexfile_func(bibtex_fpath: str, state: State,
                       **kwargs) -> DeferrableString:
    if state.cwd is not None:
        bibtex_fpath_full = f'{state.cwd}/{bibtex_fpath}'
    else:
        bibtex_fpath_full = bibtex_fpath

    with open(bibtex_fpath_full, 'r') as f:
        bibtex = f.read()
    return addbibtextext_func(bibtex, state)

def _get_bibliography_html(bib_state: _BibliographyState) -> str:
    bib_items = bib_state.bibliography_items
    for db, bibtex in bib_state.bibtex_data:
        db_ids = [id for id in db.entries
                  if id in bib_state.citation_order and id not in bib_items]
        try:
            citations_full_html_raw = pybtex.format_from_string(bibtex,
                'unsrt', citations=db_ids, output_backend='html')
        except Exception as e:
            raise exceptions.BibTeXError(f'{type(e)}')

        citations_full_html = _helper.numbered_character_entities(
            citations_full_html_raw)

        # extract citations inside <dd> elements
        for id in db_ids:
            l = '<dd>'
            r = '</dd>'
            j = citations_full_html.find(l) + len(l)
            k = citations_full_html.find(r)
            bib_items[id] = citations_full_html[j:k]
            citations_full_html = citations_full_html[k+len(r):]

    sorted_ids = sorted(bib_state.citation_order.keys(),
                        key=bib_state.citation_order.get)

    html = '<ol>\n'
    for id in sorted_ids:
        if id not in bib_items:
            raise exceptions.CitationError(
                f'Bibliography item {id} does not exist')

        # only add IDs to the list items in the first bibliography generated
        if bib_state.have_generated_bibliography:
            html += f'<li>{bib_items[id]}</li>\n'
        else:
            html += f'<li id={quoteattr(id)}>{bib_items[id]}</li>\n'

    html += '</ol>'
    bib_state.have_generated_bibliography = True
    return html

def bibliography_func(state: State, **kwargs) -> DeferrableString:
    def deferred_str_func(state: State) -> str:
        bib_state = state['_bibliography']
        return _get_bibliography_html(bib_state)

    bib_state = _get_or_init(state, '_bibliography', _BibliographyState)
    bib_state.bibliography_present = True
    bib_state.bibliography_filename = state.filename
    return deferred_str_func

class _FootnoteState:
    def __init__(self):
        self.footnote_groups: list[Tuple(str, Dict[str, Tuple[str, str]])] = []
        self.pending_footnotes: list[str] = []

def footnote_func(text: str, state: State, **kwargs) -> DeferrableString:
    footnote_state = _get_or_init(state, '_footnotes', _FootnoteState)
    group_index = len(footnote_state.footnote_groups)
    footnote_state.pending_footnotes.append(text)

    def deferred_str_func(state: State) -> str:
        footnote_state = state['_footnotes']

        try:
            footnote_group = footnote_state.footnote_groups[group_index]
        except IndexError:
            m = deferrable_string._replace_deferred_strings_with_ellipsis(text)
            raise exceptions.FootnoteError(m)

        group_filename, footnote_dict = footnote_group
        id, ref_text = footnote_dict[text]
        href = _helper.href(id, state.filename, group_filename)
        return f'<sup><a href={href}>{ref_text}</a></sup>'

    return deferred_str_func

def footnotes_func(state: State, **kwargs) -> str:
    footnote_state = _get_or_init(state, '_footnotes', _FootnoteState)
    group_index = len(footnote_state.footnote_groups)
    footnote_texts = footnote_state.pending_footnotes
    footnote_state.pending_footnotes = []

    footnote_dict = dict()
    footnote_htmls = []
    for footnote_index, text in enumerate(footnote_texts):
        ref_text = f'{footnote_index+1}'
        id = f'_footnote_{group_index+1}_{footnote_index+1}'
        footnote_dict[text] = (id, ref_text)

        qid = quoteattr(id)
        footnote_html = f'<p id={qid}><sup>{ref_text}</sup>{text}</p>'
        footnote_htmls.append(footnote_html)

    footnote_state.footnote_groups.append((state.filename, footnote_dict))
    footnotes_html = '\n'.join(footnote_htmls)
    return footnotes_html
