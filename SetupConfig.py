#-------Main Package Settings-----------#
name = "Cheetah"
from src.Version import Version as version
maintainer = "Tavis Rudd"
author = "The Cheetah Development Team"
author_email = "cheetahtemplate-discuss@lists.sf.net"
url = "http://www.CheetahTemplate.org/"
packages = ['Cheetah',
            'Cheetah.Templates',
            'Cheetah.Tests',
            'Cheetah.Tools',
            'Cheetah.Utils',
	    'Cheetah.Utils.optik',
            ]
classifiers = [line.strip() for line in '''\
  Development Status :: 4 - Beta
  #Development Status :: 5 - Production/Stable
  Intended Audience :: Developers
  Intended Audience :: System Administrators
  License :: OSI Approved :: MIT License
  Operating System :: OS Independent
  Programming Language :: Python
  Topic :: Internet :: WWW/HTTP
  Topic :: Internet :: WWW/HTTP :: Dynamic Content
  Topic :: Internet :: WWW/HTTP :: Site Management
  Topic :: Software Development :: Code Generators
  Topic :: Software Development :: Libraries :: Python Modules
  Topic :: Software Development :: User Interfaces
  Topic :: Text Processing'''.splitlines() if not line.strip().startswith('#')]
del line

package_dir = {'Cheetah':'src'}

import os
import os.path
from distutils.core import Extension

## we only assume the presence of a c compiler on Posix systems, NT people will
#  have to enable this manually. 
if os.name == 'posix':
    ext_modules=[Extension("Cheetah._namemapper", [os.path.join("src" ,"_namemapper.c")]
                           )
                 ]
else:
    ext_modules=[]


## Data Files and Scripts
scripts = ['bin/cheetah-compile',
           'bin/cheetah',
           ]
data_files = ['recursive: src *.tmpl *.txt LICENSE README TODO CHANGES',
              ]

## GET THE DESCRIPTION AND CREATE THE README
from src import __doc__  
README = open('README','w')
README.write(__doc__)
README.close()

description = __doc__.split('\n')[0]
long_description = __doc__
