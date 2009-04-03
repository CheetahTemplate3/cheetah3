#-------Main Package Settings-----------#
name = "Cheetah"
from src.Version import Version as version
maintainer = "Tavis Rudd"
author = "Tavis Rudd"
author_email = "cheetahtemplate-discuss@lists.sf.net"
url = "http://www.CheetahTemplate.org/"
packages = ['Cheetah',
            'Cheetah.Macros',            
            'Cheetah.Templates',
            'Cheetah.Tests',
            'Cheetah.Tools',
            'Cheetah.Utils',
            ]
classifiers = [line.strip() for line in '''\
  #Development Status :: 4 - Beta
  Development Status :: 5 - Production/Stable
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

description = "Cheetah is a template engine and code generation tool."

long_description = '''Cheetah is an open source template engine and code generation tool.

It can be used standalone or combined with other tools and frameworks. Web
development is its principle use, but Cheetah is very flexible and is also being
used to generate C++ game code, Java, sql, form emails and even Python code.

Documentation
================================================================================
For a high-level introduction to Cheetah please refer to the User\'s Guide
at http://cheetahtemplate.org/learn.html

Mailing list
================================================================================
cheetahtemplate-discuss@lists.sourceforge.net
Subscribe at http://lists.sourceforge.net/lists/listinfo/cheetahtemplate-discuss

Credits
================================================================================
http://cheetahtemplate.org/credits.html

Praise
================================================================================
"I\'m enamored with Cheetah" - Sam Ruby, senior member of IBM Emerging
Technologies Group & director of Apache Software Foundation

"Give Cheetah a try. You won\'t regret it. ... Cheetah is a truly powerful
system. ... Cheetah is a serious contender for the 'best of breed' Python
templating." - Alex Martelli

"People with a strong PHP background absolutely love Cheetah for being Smarty,
but much, much better." - Marek Baczynski

"I am using Smarty and I know it very well, but compiled Cheetah Templates with
its inheritance approach is much powerful and easier to use than Smarty." -
Jaroslaw Zabiello

"There is no better solution than Cheetah" - Wilk

"A cheetah template can inherit from a python class, or a cheetah template, and
a Python class can inherit from a cheetah template. This brings the full power
of OO programming facilities to the templating system, and simply blows away
other templating systems" - Mike Meyer

"Cheetah has successfully been introduced as a replacement for the overweight
XSL Templates for code generation. Despite the power of XSL (and notably XPath
expressions), code generation is better suited to Cheetah as templates are much
easier to implement and manage." - The FEAR development team
    (http://fear.sourceforge.net/docs/latest/guide/Build.html#id2550573)

"I\'ve used Cheetah quite a bit and it\'s a very good package" - Kevin Dangoor,
lead developer of TurboGears.

Recent Changes
================================================================================
See http://cheetahtemplate.org/docs/CHANGES for full details.

'''
try:
    recentChanges = open('CHANGES').read().split('\n1.0')[0]
    long_description += recentChanges
    del recentChanges
except:
    pass
