# -*- coding: utf-8 -*-

import markdown

MD = markdown.Markdown(extensions=[
    'markdown.extensions.fenced_code',
    'markdown.extensions.codehilite',
])


class TagStripper(object):
    def __init__(self, tag):
        self._tag0 = '<{0}>'.format(tag)
        self._tag1 = '</{0}>'.format(tag)
        self._len_tag0 = len(self._tag0)
        self._len_tag1 = len(self._tag1)

    def strip(self, text):
        if text.startswith(self._tag0) and text.endswith(self._tag1):
            return text[self._len_tag0:-self._len_tag1]
        else:
            return text

TS = TagStripper('p')

# Used outside this module
md_convert = MD.convert


def md_iconvert(txt):
    return TS.strip(MD.convert(txt))
