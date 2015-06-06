#!/usr/bin/env python
#
# Copyright (c) 2014 Stoneopus Technologies Co., Ltd.
# <http://stoneopus.com>

"""Decorates RequestHandlers and builds up a list of routables
handlers.

Here is a simple "Hello, world" example::

    @route(r'/', name='index')
    class MainHandler(tornado.web.RequestHandler):
        pass

    class Application(tornado.web.Application):
        def __init__(self):
            handlers = [
                # ...
            ] + route.routes()
"""

import logging

import tornado.web

class Route(object):

    _routes = {}

    def __init__(self, pattern, kwargs=None, name=None, host=".*$"):
        self.pattern = pattern
        self.kwargs = kwargs or {}
        self.name = name
        self.host = host

    def __call__(self, handler_class):
        """gets called when we class decorate"""
        logging.debug("URLSpec pattern `%s`, found handler_class `%s`"
                      % (self.pattern, handler_class))
        name = self.name and self.name or handler_class.__name__
        spec = tornado.web.url(self.pattern, handler_class,
                                   self.kwargs, name=name)
        self._routes.setdefault(self.host, []).append(spec)

        return handler_class

    @classmethod
    def routes(cls, application=None):
        if application:
            for host, handlers in cls._routes.items():
                Application.add_handlers(host, handlers)
        else:
            return reduce(lambda x, y: x + y, cls._routes.values()) \
                if cls._routes else []

    @classmethod
    def url_for(cls, name, *args):
        named_handlers = dict([(spec.name, spec) for spec in cls.routes()
                                                              if spec.name])
        if name in named_handlers:
            return named_handlers[name].reverse(*args)
        raise KeyError("%s not found in named urls" % name)

route = Route