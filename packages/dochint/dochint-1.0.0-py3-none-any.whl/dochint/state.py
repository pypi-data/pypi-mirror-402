from . import exceptions, _helper

from collections.abc import Hashable
import re
from typing import Any, Optional

class State:
    '''Object representing the state of the current text processing context.

    Members:

    filename: Optional[str]
        Name of the current file (None for single-file processing).
    cwd: Optional[str]
        Directory to resolve macro-argument file paths from (None for the
        process' working directory)
    '''
    def __init__(self):
        self._attr_dict = dict()
        self._crossref_dict = dict()
        self._crossref_lists = dict()
        self._crossref_chapter_prefix = ''

        self.filename = None
        self.cwd = None

    def set(self, key: Hashable, value: Any) -> None:
        '''Sets a state variable.'''
        self._attr_dict[key] = value

    def get(self, key: Hashable) -> Any:
        '''Gets a state variable.'''
        return self._attr_dict[key]

    def contains(self, key: Hashable) -> bool:
        '''Checks if a given state variable exists.'''
        return key in self._attr_dict

    def __getitem__(self, key: Hashable) -> Any:
        '''Sets a state variable.'''
        return self.get(key)

    def __setitem__(self, key: Hashable, value: Any) -> None:
        '''Gets a state variable.'''
        self.set(key, value)

    def __contains__(self, key: Hashable) -> bool:
        '''Checks if a given state variable exists.'''
        return self.contains(key)

    def contains_crossref(self, id: str) -> bool:
        '''Checks if a cross-reference exists.

        Arguments:

        id: str
            Cross-reference identifier to check.
        '''
        return id in self._crossref_dict

    def set_crossref(self, id: str, text: Optional[str]=None) -> None:
        '''Defines a cross-reference.

        Arguments:

        id: str
            Cross-reference identifier to define.
        text: str, optional
            Cross-reference label text.

        Exceptions raised:

        CrossrefExistsError
            Raised if a cross-reference with identifer id already exists.
        '''
        if self.contains_crossref(id):
            raise exceptions.CrossrefExistsError(id)

        if text is not None:
            self._crossref_dict[id] = (self.filename, text)
            return

        # generate numbered cross-reference

        # find the namespace of the id
        match = re.search('[\\.:]', id)
        if match is None:
            namespace = ''
        else:
            namespace = id[:match.start()]

        ref_group = (namespace, self._crossref_chapter_prefix)

        # add the id to the list for this namespace and chapter prefix
        if ref_group not in self._crossref_lists:
            self._crossref_lists[ref_group] = []
        self._crossref_lists[ref_group].append(id)

        # get the reference number and add it to the dictionary
        ref_num = len(self._crossref_lists[ref_group])
        ref_text = f'{self._crossref_chapter_prefix}{ref_num}'
        self._crossref_dict[id] = (self.filename, ref_text)

    def get_crossref_text(self, id: str) -> str:
        '''Gets the label text of a cross-reference.

        Arguments:

        id: str
            Cross-reference identifier.

        Exceptions raised:

        CrossrefNotFoundError
            Raised if a cross-reference with identifier id does not exist.
        '''
        if not self.contains_crossref(id):
            raise exceptions.CrossrefNotFoundError(id)

        fname, text = self._crossref_dict[id]
        return text

    def get_crossref_href(self, id: str) -> str:
        '''Gets a URI for a cross-reference, usable as a href attribute.

        Arguments:

        id: str
            Cross-reference identifier.

        Exceptions raised:

        CrossrefNotFoundError
            Raised if a cross-reference with identifier id does not exist.
        '''
        if not self.contains_crossref(id):
            raise exceptions.CrossrefNotFoundError(id)

        fname, text = self._crossref_dict[id]
        href = _helper.href(id, self.filename, fname)
        return href

    def get_crossref_anchor(self, id: str) -> str:
        '''Gets an <a> element linking to a cross-reference.

        Arguments:

        id: str
            Cross-reference identifier.

        Exceptions raised:

        CrossrefNotFoundError
            Raised if a cross-reference with identifier id does not exist.
        '''
        if not self.contains_crossref(id):
            raise exceptions.CrossrefNotFoundError(id)

        fname, text = self._crossref_dict[id]
        href = _helper.href(id, self.filename, fname)
        link = f'<a href={href}>{text}</a>'
        return link
