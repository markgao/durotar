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


try:
    # Use setuptools if available, for install_requires (among other things).
    import setuptools
    from setuptools import Command, setup
except ImportError:
    setuptools = None
    from distutils.core import Command, setup

kwargs = {}

version = "0.1.0"

with open('README.rst') as f:
    kwargs['long_description'] = f.read()


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
