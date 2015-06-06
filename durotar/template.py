#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Stoneopus Technologies Co., Ltd.
# <http://stoneopus.com>

"""A simple template wrap for mako template engine.
"""

import os.path

from tornado.template import Loader
from mako.lookup import TemplateLookup


class MakoLoader(Loader):
    """A Mako template loader that loads from a single root directory.
    """
    def __init__(self, root_directory, **kwargs):
        super(MakoLoader, self).__init__(root_directory, **kwargs)
        self.root = os.path.abspath(root_directory)

    def _create_template(self, name):
        _lookup = TemplateLookup(directories=[self.root],
            module_directory='/tmp/mako_module', input_encoding='utf-8',
            output_encoding='utf-8', encoding_errors='replace')
        template = _lookup.get_template(name)
        template.generate = template.render

        return template