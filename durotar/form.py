#!/usr/bin/env python
#
# Copyright (c) 2014 Stoneopus Technologies Co., Ltd.
# <http://stoneopus.com>

"""A mixin for validating in tornado based on formencode
"""
import re

import formencode
from formencode import validators, htmlfill
from tornado.escape import _unicode


class Form(formencode.Schema):
    """A custom schema validates a dictionary of values, applying different
    validators (be key) to the different values.
    """

    # It is not an error when keys that aren't
    # associated with a validator are present:
    allow_extra_fields = True
    # Keys that aren't associated with validator
    # are removed:
    filter_extra_fields = True

    # retrieve the last validation `_after_` result
    # return by `_after_` method
    after_result = None

    _xsrf = validators.String(not_empty=True, max=54)

    def __init__(self, RequestHandler, **kwargs):
        super(Form, self).__init__()
        self._args = kwargs
        self._formdata = {}
        self._data = {}
        self._form_errors = {}
        self._errors = {}
        arguments = {}

        formencode.api.set_stdtranslation(languages=['zh'])

        # re-parse qs, keep_blank_fields for formencode to validate
        # so formencode not_empty setting work.
        request = RequestHandler.request
        content_type = request.headers.get('Content-Type', '')

        if request.method == 'POST':
            arguments = request.body_arguments

        for k, v in arguments.iteritems():
            v = map(RequestHandler.decode_argument, v)
            if len(v) == 1:
                self._formdata[k] = v[0]
            else:
                # keep a list of values as list (or set)
                self._formdata[k] = v

        self._handler = RequestHandler
        self._result = True

    @property
    def formdata(self):
        return self._formdata

    @property
    def data(self):
        return self._data

    @property
    def args(self):
        return self._args

    @property
    def errors(self):
        return self._form_errors

    @property
    def normalized_errors(self):
        return dict((k,str(self._form_errors[k])) for k in self._form_errors)

    def validate(self):
        self._result = True
        try:
            self._data = self.to_python(self._formdata)
        except formencode.Invalid, e:
            self._data = e.value
            self._form_errors = e.error_dict or {}
            self._errors = dict((k, v.encode('utf-8'))
                for k, v in e.unpack_errors().iteritems())
            self._result = False
        else:
            self.__after__()

        return self._result

    def add_error(self, attr, msg):
        """ Add custom error msg
        """
        self._result = False
        self._form_errors[attr] = msg

    def render(self, template_name, **kwargs):
        html = self._handler.render_string(template_name, **kwargs)
        if not self._result:
            html = htmlfill.render(html,
                defaults=self._formdata, errors=self._form_errors, encoding="utf8")
        self._handler.finish(html)

    def __after__(self):
        """A process hook after validate
        """
        pass


def decode_argument(value, name=None):
    """Decodes an argument from the request.
    """
    try:
        return _unicode(value)
    except UnicodeDecodeError:
        return value


class URL(validators.URL):
    url_re = re.compile(r'''
        ^(http|https)://
        (?:[%:\w]*@)?                           # authenticator
        (?P<domain>[a-z0-9][a-z0-9\-]{0,62}\.)* # (sub)domain - alpha followed by 62max chars (63 total)
        (?P<tld>[a-z]{2,})                      # TLD
        (?::[0-9]+)?                            # port

        # files/delims/etc
        (?P<path>/[a-z0-9\-\._~:/\?#\[\]@!%\$&\'\(\)\*\+,;=]*)?
        $
    ''', re.I | re.VERBOSE)