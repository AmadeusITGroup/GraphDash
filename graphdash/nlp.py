# -*- coding: utf-8 -*-

import re
import stop_words


class Cleaner(object):
    def __init__(self, removed_chars):
        self._regexp = re.compile(r'[{0}]'.format(removed_chars))

    def clean(self, word):
        """Removes any character from removed_chars in the string."""
        return self._regexp.sub('', word)


class StopWords(object):
    def __init__(self, language):
        self._stop_words = set(stop_words.get_stop_words(language))

    def __contains__(self, word):
        return word in self._stop_words

    def __iter__(self):
        return iter(self._stop_words)
