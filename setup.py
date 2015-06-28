#!/usr/bin/env python
#
# Copyright (c) 2014 Stoneopus Technologies co., Ltd.
# <http://stoneopus.com>

"""
Durotar
-------

Durotar is a microframework for python based on Tornado, Mako and good
intentions.
"""

from __future__ import print_function

import os
import platform
import sys
import warnings


try:
    # Use setuptools if available, for install_requires (among other things).
    import setuptools
    from setuptools import Command, setup
except ImportError:
    setuptools = None
    from distutils.core import Command, setup

from distutils.core import Extension

# The following code is copied from
# https://github.com/mongodb/mongo-python-driver/blob/master/setup.py
# to support installing without the extension on platforms where
# no compiler is available.
from distutils.command.build_ext import build_ext


class custom_build_ext(build_ext):
    """Allow C extension building to fail.

    The C extension make text filter more efficient.
    """

    warning_message = """
********************************************************************
WARNING: %s could not
be compiled. No C extensions are essential for Durotar to run.
%s

Here are some hints for popular operating systems:

If you are seeing this message on Linux you probably need to
install GCC and/or the Python development package for your
version of Python.

Debian and Ubuntu users should issue the following command:

    $ sudo apt-get install build-essential python-dev

RedHat, CentOS, and Fedora users should issue the following command:

    $ sudo yum install gcc python-devel

If you are seeing this message on OSX please read the documentation
here:

http://api.mongodb.org/python/current/installation.html#osx
********************************************************************
"""

    def run(self):
        try:
            build_ext.run(self)
        except Exception:
            e = sys.exc_info()[1]
            sys.stdout.write("%s\n" % (str(e),))
            warnings.warn(self.warning_message % ("Extension modules",
                                                  "There was an issue with "
                                                  "your platform configuration"
                                                  " - see above."))

    def build_extension(self, ext):
        name = ext.name
        try:
            build_ext.build_extension(self, ext)
        except Exception:
            e = sys.exc_info()[1]
            sys.stdout.write("%s\n" % (str(e),))
            warnings.warn(self.warning_message % ("The %s extension "
                                                  "module" % (name,),
                                                  "The output above "
                                                  "this warning shows how "
                                                  "the compilation "
                                                  "failed."))


kwargs = {}

version = "0.1.0"

with open('README.rst') as f:
    kwargs['long_description'] = f.read()


if (platform.python_implementation() == "CPython" and
        os.environ.get('DUROTAR_EXTENSION') != '0'):
    # This extension builds and works on pypy as well, although pypy's jit
    # produces equivalent performance.
    kwargs['ext_modules'] = [
        Extension('durotar.cfilters',
                  sources=['durotar/filters.c']),
    ]

    if os.environ.get('TORNADO_EXTENSION') != '1':
        # Unless the user has specified that the extension is mandatory,
        # fall back to the pure-python implementation on any build failure.
        kwargs['cmdclass'] = {'build_ext': custom_build_ext}

setup(
    name="durotar",
    version=version,
    packages=["durotar"],
    install_requires = [
        'tornado>=4.0.2',
        'mako>=1.0.0',
        'FormEncode>=1.3.0a1',
        'psycopg2>=2.5.4',
    ],
    platforms=["Linux", "Unix", "Mac OS X", "Windows"],
    include_package_data=True,
    author="Mark Gao",
    author_email="elrilos@gmail.com",
    url="https://bitbucket.org/stoneopusinc/durotar",
    license="private license",
    description="Durotar is a Python web framework based on Tornado",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: Web Server",
        "Intended Audience :: Developers",
        "License :: Private License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    **kwargs
)
