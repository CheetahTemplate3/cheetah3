#-------Main Package Settings-----------#
name = "Cheetah"
from src.Version import version
maintainer = "Tavis Rudd"
author = "The Cheetah Development Team"
author_email = "cheetahtemplate-discuss@lists.sf.net"
url = "http://www.CheetahTemplate.org/"
packages = ['Cheetah',
            'Cheetah.Templates',
            'Cheetah.Tests',
            'Cheetah.Tools',
            ]

package_dir = {'Cheetah':'src'}

import os
from distutils.core import Extension
if os.name == 'posix':
    ext_modules=[Extension("Cheetah/_namemapper", ["src/_namemapper.c"])]
else:
    ext_modules=[]


## Data Files and Scripts
scripts = ['bin/cheetah-compile',
           ]
data_files = ['recursive: src *.tmpl *.txt LICENSE README',
              ]

## GET THE DESCRIPTION AND CREATE THE README
from src import __doc__  
README = open('README','w')
README.write(__doc__)
README.close()

description = __doc__.split('\n')[0]
long_description = __doc__
