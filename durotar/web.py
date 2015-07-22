#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Stoneopus Technologies Co., Ltd.
# <http://stoneopus.com>

import logging
import time

import tornado.web
import tornado.options

from tornado import httputil
from tornado.log import access_log, app_log, gen_log
import durotar

from durotar import template
from durotar import tornpg
from durotar.util import import_module, load_class
from durotar.filters import space_compress
from durotar.route import Route


class Application(tornado.web.Application):
    """Subclass of tornado.web.Application
    """

    handlers = []

    context_processors = []

    def __init__(self, **kwargs):
        """Initialize application"""
        settings = dict(debug=False)

        settings.update(kwargs)

        # load handlers from installed app which previously defined in settings
        self._install_app(settings.get('apps'))

        # process context defined in settings
        self._context_processors(settings.get('context_processors', []))

        tornado.web.Application.__init__(self, self.handlers, **settings)

        # database connection
        self._connect_db(self.settings.get('db_config'))


    def _install_app(self, apps):
        """Discovery handlers automaticlly from app directory"""
        if not apps or not isinstance(apps, list):
            return

        for app in apps:
            try:
                import_module(app + '.handlers')
            except ImportError as e:
                logging.warn("No handlers found in app package <%s>:"
                        "%s" % (app, e))

        self.handlers.extend(Route.routes())

    def _context_processors(self, processors):
        self.context_processors = [load_class(cls) for cls in set(processors)]

    def _connect_db(self, config):
        self.db = None
        if config:
            self.db = tornpg.Connection(**config)


class RequestHandler(tornado.web.RequestHandler):
    """RequestHandler for www port extended from
    tornado.web.RequestHandler.
    """

    def _apply_context_processors(self, kwargs):
        context = {}
        context.update(kwargs)

        for processor in self.application.context_processors:
            context.update({processor.__name__: processor(self)})

        return context

    def render_string(self, template_name, **kwargs):
        """Generate the given template with the given arguments.

        We return the generated byte string (in utf8). To generate and
        write a template as a response, use render() above.
        """
        context = self._apply_context_processors(kwargs)

        content = super(RequestHandler, self).render_string(template_name,
                                                            **context)
        return space_compress(content)

    def create_template_loader(self, template_path):
        """Returns a new mako template loader for the given path.

        May be overridden by subclasses. By default returns mako loader on
        the given path, using the ``autoescape`` application setting. if a
        ``template_loader`` application setting is supplied, uses that instead.
        """
        settings = self.application.settings
        if 'template_loader' in settings:
            return settings['template_loader']

        module_path = settings.get('mako_module_path', "/tmp/mako_module")
        kwargs = {}
        if 'autoescape' in settings:
            # autoescape=None means "no escaping", so we have to be sure
            # to only pass this kwargs if the user asked for i.
            kwargs['autoescape'] = settings['autoescape']
        return template.MakoLoader(template_path, module_path, **kwargs)

    def clear(self):
        """Resets all headers and content for this response."""
        self._headers = httputil.HTTPHeaders({
            "Server": "Durotar/%s" % durotar.version,
            "Content-Type": "text/html; charset=UTF-8",
            "Date": httputil.format_timestamp(time.time()),
        })
        self.set_default_headers()
        self._write_buffer = []
        self._status_code = 200
        self._reason = httputil.responses[200]