#! /usr/bin/env python
# -*- coding: utf-8 -*-
########################################################################
# Python kontocheck package
#
# Copyright (c) 2013 by joonis new media <thimo.kraemer@joonis.de>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.

from __future__ import division, absolute_import, print_function, unicode_literals

import sys
import os
from distutils.core import setup
from distutils.extension import Extension
import struct

PY2 = sys.version_info[0] == 2
if PY2:
    import io
    open = io.open
    str = unicode  # noqa: F821
    chr = unichr  # noqa: F821
    range = xrange  # noqa: F821
    input = raw_input  # noqa: F821
    import future_builtins
    ascii = future_builtins.ascii
    filter = future_builtins.filter
    hex = future_builtins.hex
    map = future_builtins.map
    oct = future_builtins.oct
    zip = future_builtins.zip
    nativestring = bytes
else:
    nativestring = str
    basestring = str

# Py2.6 requires a byte string
_PY_BIT = struct.calcsize(b'P') * 8

dir = os.path.abspath(os.path.dirname(__file__))

# Read package description
with open(os.path.join(dir, 'README.rst'), 'rt', encoding='utf-8') as fh:
    readme = fh.read()

package_data = {
    nativestring('kontocheck'): ['data/blz.lut2'],
}
        
if os.name == 'nt':
    package_data['kontocheck'].append('lib/kontocheck%s.dll' % _PY_BIT)
    ext_modules = None
else:
    # distutils requires native string types
    ext_modules = [
        Extension(
            nativestring('kontocheck.lib.kontocheck'),
            sources=[nativestring('lib/konto_check/konto_check.c')],
            libraries=[nativestring('z')],
        ),
    ]

dist = setup(
    name='kontocheck',
    version='6.15.4',
    author='Thimo Kraemer',
    author_email='thimo.kraemer@joonis.de',
    url='http://www.joonis.de/software/fintech/kontocheck',
    description='Python ctypes wrapper of the konto_check library.',
    long_description=readme,
    keywords=['kontocheck', 'iban', 'bic', 'scl'],
    download_url='',
    license='LGPLv3',
    ext_modules=ext_modules,
    package_dir={'kontocheck': 'src'},
    packages=[nativestring('kontocheck')],
    package_data=package_data,
    # python_requires='>=3.4',
    classifiers=[
        'Topic :: Office/Business :: Financial',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
    ],
)
