#!/usr/bin/env python
#
# Copyright (c) 2014 Stoneopus Technologies Co., Ltd.
# <http://stoneopus.com>

"""Miscellaneous utility functions and classes.

This module is used internally by Durotar. It is not necessarily expected
that the functions and classes defined here will be useful to other
applications, but they are documented here in case they are.
"""

from __future__ import absolute_import, division, print_function, with_statement

from importlib import import_module


def load_class(path):
    """Load class from path.
    """

    mod_name, cls_name = None, None

    try:
        mod_name, cls_name = path.rsplit(".", 1)
        mod = import_module(mod_name)
    except AttributeError as e:
        raise RuntimeError("Error importing %s: '%s'" % (mod_name, e))

    try:
        cls = getattr(mod, cls_name)
    except AttributeError:
        raise RuntimeError('%s not defined in %s' % (cls_name, mod_name))

    return cls