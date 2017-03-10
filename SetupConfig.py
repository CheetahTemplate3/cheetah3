#-------Main Package Settings-----------#
import sys
from cheetah.compat import PY2

name = 'Cheetah'
from cheetah.Version import Version as version
license = "MIT"
author = "Tavis Rudd"
author_email = "tavis@damnsimple.com"
maintainer = "Oleg Broytman"
maintainer_email = "phd@phdru.name"
url = "https://cheetahtemplate3.github.io/"
packages = ['Cheetah',
            'Cheetah.Macros',            
            'Cheetah.Templates',
            'Cheetah.Tests',
            'Cheetah.Tools',
            'Cheetah.Utils',
            ]
classifiers = [line.strip() for line in '''\
  Development Status :: 2 - Pre-Alpha
  Intended Audience :: Developers
  Intended Audience :: System Administrators
  License :: OSI Approved :: MIT License
  Operating System :: OS Independent
  Programming Language :: Python
  Programming Language :: Python :: 2,
  Programming Language :: Python :: 2.7,
  Topic :: Internet :: WWW/HTTP
  Topic :: Internet :: WWW/HTTP :: Dynamic Content
  Topic :: Internet :: WWW/HTTP :: Site Management
  Topic :: Software Development :: Code Generators
  Topic :: Software Development :: Libraries :: Python Modules
  Topic :: Software Development :: User Interfaces
  Topic :: Text Processing'''.splitlines() if not line.strip().startswith('#')]

if PY2:
    del line

package_dir = {'Cheetah':'cheetah'}

import os
import os.path
from distutils.core import Extension

ext_modules=[
             Extension("Cheetah._namemapper", 
                        [os.path.join('cheetah', 'c', '_namemapper.c')]),
           #  Extension("Cheetah._verifytype", 
           #             [os.path.join('cheetah', 'c', '_verifytype.c')]),
           #  Extension("Cheetah._filters", 
           #             [os.path.join('cheetah', 'c', '_filters.c')]),
           #  Extension('Cheetah._template',
           #             [os.path.join('cheetah', 'c', '_template.c')]),
             ]

## Data Files and Scripts
scripts = ('bin/cheetah-compile',
           'bin/cheetah',
           'bin/cheetah-analyze',
        )

data_files = ['recursive: cheetah *.tmpl *.txt LICENSE README TODO CHANGES',]

if not os.getenv('CHEETAH_INSTALL_WITHOUT_SETUPTOOLS'):
    try:
        from setuptools import setup
        install_requires = [
                "Markdown >= 2.0.1",
        ]
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
        print('Not using setuptools, so we cannot install the Markdown dependency')


description = "Cheetah is a template engine and code generation tool."

long_description = '''Cheetah is an open source template engine and code generation tool.

It can be used standalone or combined with other tools and frameworks. Web
development is its principle use, but Cheetah is very flexible and is also being
used to generate C++ game code, Java, sql, form emails and even Python code.

Documentation
================================================================================
For a high-level introduction to Cheetah please refer to the User\'s Guide
at https://cheetahtemplate3.github.io/users_guide/index.html

Credits
================================================================================
https://github.com/CheetahTemplate3/cheetah3/blob/master/LICENSE

Recent Changes
================================================================================
See https://github.com/CheetahTemplate3/cheetah3/blob/master/CHANGES
for full details

'''
