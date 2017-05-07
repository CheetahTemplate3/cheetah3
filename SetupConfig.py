#-------Main Package Settings-----------#
import sys

# Cheetah3 has already been taken at PyPI,
# CheetahTemplate3 seems to be too long.
name = 'Cheetah3'
from Cheetah.Version import Version as version
description = "Cheetah is a template engine and code generation tool"
license = "MIT"
author = "Tavis Rudd"
author_email = "tavis@damnsimple.com"
maintainer = "Oleg Broytman"
maintainer_email = "phd@phdru.name"
url = "http://cheetahtemplate.org/"
dev_tag = ""
download_url = "https://pypi.python.org/pypi/%s/%s%s" % (name, version, dev_tag)
del dev_tag
packages = ['Cheetah',
            'Cheetah.Macros',
            'Cheetah.Templates',
            'Cheetah.Tests',
            'Cheetah.Tools',
            'Cheetah.Utils',
            ]
classifiers = [line.strip() for line in '''\
  Development Status :: 5 - Production/Stable
  Intended Audience :: Developers
  Intended Audience :: System Administrators
  License :: OSI Approved :: MIT License
  Operating System :: OS Independent
  Programming Language :: Python
  Programming Language :: Python :: 2
  Programming Language :: Python :: 2.7
  Programming Language :: Python :: 3
  Programming Language :: Python :: 3.3
  Programming Language :: Python :: 3.4
  Programming Language :: Python :: 3.5
  Programming Language :: Python :: 3.6
  Topic :: Internet :: WWW/HTTP
  Topic :: Internet :: WWW/HTTP :: Dynamic Content
  Topic :: Internet :: WWW/HTTP :: Site Management
  Topic :: Software Development :: Code Generators
  Topic :: Software Development :: Libraries :: Python Modules
  Topic :: Software Development :: User Interfaces
  Topic :: Text Processing'''.splitlines() if not line.strip().startswith('#')]

from Cheetah.compat import PY2
if PY2:
    del line
del PY2  # Hide it from setup()

import os
import os.path
from distutils.core import Extension

ext_modules=[
             Extension("Cheetah._namemapper",
                        [os.path.join('Cheetah', 'c', '_namemapper.c')]),
           #  Extension("Cheetah._verifytype",
           #             [os.path.join('Cheetah', 'c', '_verifytype.c')]),
           #  Extension("Cheetah._filters",
           #             [os.path.join('Cheetah', 'c', '_filters.c')]),
           #  Extension('Cheetah._template',
           #             [os.path.join('Cheetah', 'c', '_template.c')]),
             ]

## Data Files and Scripts
scripts = ('bin/cheetah-compile',
           'bin/cheetah',
           'bin/cheetah-analyze',
        )

data_files = ['recursive: Cheetah *.tmpl *.txt *.rst LICENSE README.rst TODO']

if not os.getenv('CHEETAH_INSTALL_WITHOUT_SETUPTOOLS'):
    try:
        from setuptools import setup
        if sys.platform == 'win32':
            # use 'entry_points' instead of 'scripts'
            del scripts
            entry_points = {
                'console_scripts': [
                    'cheetah = Cheetah.CheetahWrapper:_cheetah',
                    'cheetah-compile = Cheetah.CheetahWrapper:_cheetah_compile',
                ]
        }
    except ImportError:
        pass

long_description = '''\
Cheetah3 is a free (BSD-style) and open source template engine and code
generation tool.

It can be used standalone or combined with other tools and frameworks. Web
development is its principle use, but Cheetah is very flexible and is also being
used to generate C++ game code, Java, sql, form emails and even Python code.

It's a fork of the original CheetahTemplate library.

Documentation
================================================================================
For a high-level introduction to Cheetah please refer to the User\'s Guide
at http://cheetahtemplate.org/users_guide/index.html

Credits
================================================================================
http://cheetahtemplate.org/authors.html

https://github.com/CheetahTemplate3/cheetah3/blob/master/LICENSE

Recent Changes
================================================================================
See http://cheetahtemplate.org/news.html for full details

'''
