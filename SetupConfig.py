# -------Main Package Settings-----------#
from setuptools import Extension
import os
import os.path
import sys

from Cheetah.Version import Version as version
from Cheetah.compat import PY2

# Cheetah3 has already been taken at PyPI,
# CheetahTemplate3 seems to be too long.
# CT3 is just right!
name = 'CT3'
description = "Cheetah is a template engine and code generation tool"
license = "MIT"
author = "Tavis Rudd"
author_email = "tavis@damnsimple.com"
maintainer = "Oleg Broytman"
maintainer_email = "phd@phdru.name"
url = "https://cheetahtemplate.org/"
dev_tag = ""
download_url = "https://pypi.org/project/%s/%s%s" \
    % (name, version, dev_tag)
project_urls = {
    'Homepage': 'https://cheetahtemplate.org/',
    'Documentation': 'https://cheetahtemplate.org/users_guide/index.html',
    'Download': 'https://pypi.org/project/%s/%s%s/'
    % (name, version, dev_tag),
    'Github repo': 'https://github.com/CheetahTemplate3',
    'Issue tracker': 'https://github.com/CheetahTemplate3/cheetah3/issues',
    'Wikipedia': 'https://en.wikipedia.org/wiki/CheetahTemplate',
}
del dev_tag
keywords = ["template"]
platforms = "Any"
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
  Programming Language :: Python :: Implementation :: CPython
  Programming Language :: Python :: Implementation :: PyPy
  Programming Language :: Python
  Programming Language :: Python :: 2
  Programming Language :: Python :: 2.7
  Programming Language :: Python :: 3
  Programming Language :: Python :: 3.4
  Programming Language :: Python :: 3.5
  Programming Language :: Python :: 3.6
  Programming Language :: Python :: 3.7
  Programming Language :: Python :: 3.8
  Programming Language :: Python :: 3.9
  Programming Language :: Python :: 3.10
  Programming Language :: Python :: 3.11
  Programming Language :: Python :: 3.12
  Programming Language :: Python :: 3.13
  Topic :: Internet :: WWW/HTTP
  Topic :: Internet :: WWW/HTTP :: Dynamic Content
  Topic :: Internet :: WWW/HTTP :: Site Management
  Topic :: Software Development :: Code Generators
  Topic :: Software Development :: Libraries :: Python Modules
  Topic :: Software Development :: User Interfaces
  Topic :: Text Processing'''.splitlines() if not line.strip().startswith('#')]

if PY2:
    del line
del PY2  # Hide it from setup()

ext_modules = [
    Extension("Cheetah._namemapper",
              [os.path.join('Cheetah', 'c', '_namemapper.c')]),
    # Extension("Cheetah._verifytype",
    #            [os.path.join('Cheetah', 'c', '_verifytype.c')]),
    # Extension("Cheetah._filters",
    #            [os.path.join('Cheetah', 'c', '_filters.c')]),
    # Extension('Cheetah._template',
    #            [os.path.join('Cheetah', 'c', '_template.c')]),
]

# Data Files and Scripts
scripts = ('bin/cheetah-compile',
           'bin/cheetah',
           'bin/cheetah-analyze',
           )

data_files = ['recursive: Cheetah *.tmpl *.txt *.rst LICENSE README.rst TODO']

try:
    if sys.platform == 'win32':
        # use 'entry_points' instead of 'scripts'
        del scripts
        entry_points = {
            'console_scripts': [
                'cheetah = Cheetah.CheetahWrapper:_cheetah',
                'cheetah-compile = '
                'Cheetah.CheetahWrapper:_cheetah_compile',
            ]
        }
except ImportError:
    pass

long_description = '''\
Cheetah3 is a free and open source template engine and code generation tool.

It can be used standalone or combined with other tools and frameworks. Web
development is its principle use, but Cheetah is very flexible and
is also being used to generate C++ game code, Java, sql, form emails
and even Python code.

It's a fork of the original CheetahTemplate library.

Documentation
================================================================================
For a high-level introduction to Cheetah please refer to the User\'s Guide
at https://cheetahtemplate.org/users_guide/index.html

Credits
================================================================================
https://cheetahtemplate.org/authors.html

https://github.com/CheetahTemplate3/cheetah3/blob/master/LICENSE

Recent Changes
================================================================================
See https://cheetahtemplate.org/news.html for full details

'''

long_description_content_type = "text/x-rst"

python_requires = '>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*'

extras_require = {
    'filters': ['markdown'],
    'markdown': ['markdown'],
}
