#!/usr/bin/env python
# Akshaal (C) 2010, GNU GPL. http://akshaal.info

from distutils.core import setup
from distutils.core import setup, Extension

import sys

ldir = sys.argv[1]
sys.argv = [sys.argv[0]] + sys.argv[2:]

setup (name        = 'simavr',
       description = 'Python bindings for a simple, lean and mean AVR simulator (simavr).',
       ext_modules = [Extension ('_csimavr',
                                 ['csimavr.i'],
                                 swig_opts = ['-I../sim', '-O', '-w451'],
                                 extra_compile_args = ['-g', '--std=gnu99', '-I../sim', '-I../../include', '-mfpmath=sse', '-msse2', '-O3'],
                                 extra_link_args = ['-L../' + ldir, '-lsimavr', '-lelf'],
                                )
                     ],
       py_modules  = ["csimavr", "simavr"],
     )

