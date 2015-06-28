#!/usr/bin/env python
#
# Copyright (c) 2015 Stoneopus Technologies Co., Ltd.
# <http://Stoneopus.com>

"""Filter methods for HTML, JSON, URLs, and others.

Also includes a few other miscellaneous string manipulation functions that
have crept in over time.
"""

from __future__ import absolute_import, division, print_function, with_statement

import re

# Script on/off tags
SC_ON = "<!-- SCRIPT_ON -->"
SC_OFF = "<!-- SCRIPT_OFF -->"

try:
    from durotar.cfilters import uspace_compress
    def space_compress(chunk):
        try:
            chunk = unicode(chunk, "utf-8")
        except TypeError:
            chunk = unicode(chunk)
        return uspace_compress(chunk)
except ImportError:
    _between_tags1 = re.compile('> +')
    _between_tags2 = re.compile(' +<')
    _spaces = re.compile('[\s]+')
    _ignore = re.compile('(' + SC_OFF + '|' + SC_ON + ')', re.S | re.I)
    def space_compress(chunk):
        res = ''
        sc = True
        for p in _ignore.split(chunk):
            if p == SC_OFF:
                sc = True
            elif p == SC_ON:
                sc = False
            elif sc:
                p = _spaces.sub(' ', p)
                p = _between_tags1.sub('>', p)
                p = _between_tags2.sub('<', p)
                res += p
            else:
                res += p

        return res