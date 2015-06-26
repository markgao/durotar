#!/usr/bin/env python
#
# Copyright (c) 2014 Stoneopus Technologies Co., Ltd.
# <http://stoneopus.com>

"""This module contains implementations of various third-party
authentication schemes.

All the classes in this file are class mixins designed to be used with
the `durotar.web.RequestHandler` class. They are used in two ways:

* On a login handler, use methods such as ``authenticate_redirect()``,
  ``authorize_redirect()``, and ``get_authenticated_user()`` to
  establish the user's identity and store authentication tokens to your
  database and/or cookies.
* In non-login handlers, use methods such as ``wechat_request()``
  to use the authtication tokens to make requests to the respective services.
"""

from __future__ import absolute_import, division, print_function, with_statement

import logging
import functools

from tornado.concurrent import TracebackFuture, return_future
from tornado import gen
from tornado import httpclient
from tornado import escape
from tornado.httputil import url_concat
from tornado.log import gen_log
from tornado.stack_context import ExceptionStackContext
from tornado.util import ArgReplacer

try:
    import urlparse # py2
except ImportError:
    import urllib.parse as urlparse #py3

try:
    import urllib.parse as urllib_parse # py3
except ImportError:
    import urllib as urllib_parse # py2

try:
    long # py2
except NameError:
    long = int # py3

class AuthError(Exception):
    pass


def _auth_future_to_callback(callback, future):
    try:
        result = future.result()
    except AuthError as e:
        gen_log.warning(str(e))
        result = None
    callback(result)


def _auth_return_future(f):
    """Similar to tornado.concurrent.return_future, but uses the auth
    module's legacy callback interface.

    Note that when using this decorator the ``callback`` parameter
    inside the function will actually be a future
    """
    replacer = ArgReplacer(f, 'callback')

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        future = TracebackFuture()
        callback, args, kwargs = replacer.replace(future, args, kwargs)
        if callback is not None:
            future.add_done_callback(
                functools.partial(_auth_future_to_callback, callback))
        def handle_exception(typ, value, tb):
            if future.done():
                return False
            else:
                future.set_exc_info((typ, value, tb))
                return True
        with ExceptionStackContext(handle_exception):
            f(*args, **kwargs)
        return future
    return wrapper
        

class WechatMixin(object):
    """Abstract implementation of Wechat OAuth 2.0

    See `WechatMpMixin` below for an example implementation.

    Class atrributes:

    * ``_OAUTH_AUTHORIZE_URL``: The service's authorization url.
    * ``_OAUTH_ACCESS_TOKEN_URL``: The service's access token url.
    """
    @return_future
    def authorize_redirect(self, redirect_uri=None, appid=None,
                           secret=None, extra_params=None,
                           callback=None, scope=None, response_type="code"):
        """Redirects the user to obtain OAuth authorization for this service.

        Some providers require that you register a redirect URL with
        your application instead of passing one via this method. You
        should call this method to log the user in, and then call
        ``get_authenticated_user`` in the handler for your
        redirect URL to complete the authorization process.
        """
        args = {
            'redirect_uri': redirect_uri,
            'appid': appid,
            'response_type': response_type
        }
        if extra_params:
            args.update(extra_params)
        if scope:
            args['scope'] = ",".join(scope)
        self.redirect(
            url_concat(self._OAUTH_AUTHORIZE_URL, args)+'#wechat_redirect')
        callback()

    def _oauth_request_token_url(self, redirect_uri=None, appid=None,
                                 secret=None, code=None,
                                 grant_type='authorization_code',
                                 extra_params=None):
        url = self._OAUTH_ACCESS_TOKEN_URL
        args = dict(
            redirect_uri=redirect_uri,
            code=code,
            appid=appid,
            secret=secret,
            grant_type=grant_type,
        )
        if extra_params:
            args.update(extra_params)
        return url_concat(url, args)


class WechatMpMixin(WechatMixin):
    """Wechat Media Platform authentication using OAuth2
    """
    _OAUTH_ACCESS_TOKEN_URL = "https://api.weixin.qq.com/sns/oauth2/access_token?"
    _OAUTH_AUTHORIZE_URL = "https://open.weixin.qq.com/connect/oauth2/authorize?"
    _OAUTH_NO_CALLBACKS = False
    _WECHAT_BASE_URL = "https://api.weixin.qq.com/sns"

    @_auth_return_future
    def get_openid(self, redirect_uri, appid, secret, code,
                   callback, grant_type='authorization_code'):
        http = self.get_auth_http_client()
        args = {
            'redirect_uri': redirect_uri,
            'appid': appid,
            'secret': secret,
            'code': code,
            'grant_type': grant_type,
        }

        http.fetch(self._oauth_request_token_url(**args),
                   functools.partial(self._on_openid, redirect_uri, appid,
                                     secret, callback))

    def _on_openid(self, redirect_uri, appid, secret, future, response):
        if response.error:
            future.set_exception(AuthError('WechatMp auth error: %s') %
                                             str(response.error))
            return

        #args = escape.parse_qs_bytes(escape.native_str(response.body))
        logging.debug("response.body: %s" % response.body)
        args = escape.json_decode(response.body)
        logging.debug("args[access_token]: %s" % args.get('access_token'))
        session = {
            'access_token': args.get('access_token'),
            'expires_in': args.get('expires_in'),
            'refresh_token': args.get('refresh_token'),
            'openid': args.get('openid'),
            'scope': args.get('scope'),
        }

        future.set_result(session)

    @_auth_return_future
    def get_authenticated_user(self, redirect_uri, appid, secret, code,
                               callback, grant_type='authorization_code',
                               extra_fields=None):
        """Handles the login for the Wechat user, returning a user object.

        Example usage::

        class WechatMpLoginHandler(LoginHandler, sin.auth.WechatMpMixin):
            @tornado.gen.coroutine
            def get(self):
                if self.get_argument("code", False):
                    user = yield self.get_authenticated_user(
                        redirect_uri="/auth/wechatmp/",
                        appid=self.settings['wechatmp_appid'],
                        secret=self.settings['wechatmp_secret'],
                        code=self.get_argument('code'))
                    # Save the user with e.g. set_secure_cookie
                else:
                    yield self.authorize_redirect(
                        redirect_uri="/auth/wechatmp/",
                        appid=self.settings['wechatmp_appid'],
                        extra_params={'scope': "snsapi_base,snsapi_userinfo"})
        """
        http = self.get_auth_http_client()
        args = {
            'redirect_uri': redirect_uri,
            'code': code,
            'appid': appid,
            'secret': secret,
            'grant_type': grant_type,
        }

        fields = set(['openid', 'nickname', 'sex', 'province', 'city',
                      'country', 'headimgurl', 'privilege', 'unionid'])

        if extra_fields:
            fields.update(extra_fields)

        http.fetch(self._oauth_request_token_url(**args),
                   functools.partial(self._on_access_token, redirect_uri, appid,
                                       secret, callback, fields))

    def _on_access_token(self, redirect_uri, appid, secret, future,
                         fields, response):
        if response.error:
            future.set_exception(AuthError('WechatMp auth error: %s' %
                                             str(response)))
            return

        #args = escape.parse_qs_bytes(escape.native_str(response.body))
        args = escape.json_decode(response.body)
        session = {
            'access_token': args.get('access_token'),
            'expires_in': args.get('expires_in'),
            'refresh_token': args.get('refresh_token'),
            'openid': args.get('openid'),
            'scope': args.get('scope'),
        }

        self.wechat_request(
            path="/userinfo",
            callback=functools.partial(
                self._on_get_user_info, future, session, fields),
            access_token=session['access_token'],
            fields=",".join(fields)
        )

    def _on_get_user_info(self, future, session, fields, user):
        if user is None:
            future.set_result(None)
            return

        fieldmap = {}
        for field in fields:
            fieldmap[field] = user.get(field)

        fieldmap.update({'access_token': session['access_token'],
                         'expires_in': session['expires_in'],
                         'refresh_token': session['refresh_token'],
                         'scope': session['scope']})
        future.set_result(fieldmap)

    @_auth_return_future
    def wechat_request(self, path, callback, access_token=None,
                       post_args=None, **args):
        """Fetches the given relative API path, e.g., "/userinfo"

        If the request is a POST, ``post_args`` should be provided. Query
        string arguments should be given as keyword arguments.

        Many methods require an OAuth access token which you can
        obtain through `~WechatMixin.authorize_redirect` and
        `get_authenticated_user`. The user returned through that
        process includes an ``access_token`` attribute that can be
        used to make authenticated requests via this method.

        Example usage::

        class MainHandler(tornado.web.RequestHandler,
                          sin.auth.WechatMpMixin):
            @tornado.web.authenticated
            @tornado.gen.coroutine
            def get(self):
                new_entry = yield self.wechat_request(
                    "/userinfo",
                    post_args={'nickname', 'new-name'},
                    access_token=self.current_user['access_token'])

                if not new_entry:
                    # call failed; perhaps missiong permission?
                    yield self.authorize_redirect()
                    return
                self.finish("Posted a message!")

        The given path is relative to ``self._WECHAT_BASE_URL``,
        """
        url = self._WECHAT_BASE_URL + path
        all_args = {}
        if access_token:
            all_args['access_token'] = access_token
            all_args.update(args)

        if all_args:
            url += "?" + urllib_parse.urlencode(all_args)
        callback = functools.partial(self._on_wechat_request, callback)
        http = self.get_auth_http_client()
        if post_args is not None:
            http.fetch(url, method="POST", body=urllib_parse.urlencode(post_args),
                       callback=callback)
        else:
            http.fetch(url, callback=callback)

    def _on_wechat_request(self, future, response):
        if response.error:
            future.set_exception(AuthError("Error response %s fetching %s" %
                                           (response.error, response.request.url)))
            return

        future.set_result(escape.json_decode(response.body))

    def get_auth_http_client(self):
        """Returns the `.AsyncHTTPClient` instance to be used for auth requests.

        May be overridden by subclasses to use an HTTP client other than
        the default.
        """
        return httpclient.AsyncHTTPClient()