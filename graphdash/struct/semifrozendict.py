# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals


class SemiFrozenDict(dict):
    """
    This is an implementation of a dict who blocks
    new keys after initialization, but allows for
    existing keys to be modified.

    The use case is if you have configuration that
    needs to be overriden.
    """

    # __init__ doesn't call __setitem__
    # We only want to restrict post-init setitem calls, so we only have to
    # override __setitem__ and update (who does not call __setitem__).

    def __setitem__(self, key, value):
        if key in self:
            super(SemiFrozenDict, self).__setitem__(key, value)
        else:
            # Addition DENIED
            print(('(!) Preventing addition of new key "{0}" in dict, '
                   'authorized keys are {1}').format(key, list(self)))

    def update(self, *args, **kwargs):
        dict_ = dict(*args, **kwargs)
        for k in dict_:
            self[k] = dict_[k]
