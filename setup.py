#!/usr/bin/env python
# $Id: setup.py,v 1.7 2001/09/06 03:51:55 tavis_rudd Exp $
"""A setup module for the Cheetah package, based on the disutils module

Meta-Data
==========
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.7 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/09/06 03:51:55 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.7 $"[11:-2]

##################################################
## DEPENDENCIES ##


from distutils.core import setup, Extension
from distutils.command.sdist import sdist

import os
import os.path
import re

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)


##################################################
## CLASSES ##

class sdist_docs(sdist):
    """a setup command that will rebuild Users Guide"""
    def run(self):
        try:
            from src.Version import version
            
            currentDir = os.getcwd()
            os.chdir(os.path.join(currentDir,'docs','src'))
            fp = open('users_guide.tex','r')
            originalTexCode = fp.read()
            fp.close()
            
            newTexCode = re.sub(r'(?<=\\release\{)[0-9\.]*',str(version), originalTexCode)
            
            fp = open('users_guide.tex','w')
            fp.write(newTexCode)
            fp.close()
            
            os.system('make -f Makefile')
            os.chdir(currentDir)
        except:
            print "The sdist_docs command couldn't rebuild the Users Guide"
            os.chdir(currentDir)
            
        sdist.run(self)
    

##################################################
## if run from the command line ##
     
if __name__ == '__main__':
    from src.Version import version
    
    from src import __doc__
    README = open('README','w')
    README.write(__doc__)
    README.close()
    synopsis = __doc__.split('\n')[0]

    if os.name == 'posix':
        ext_modules=[Extension("Cheetah/_namemapper", ["src/_namemapper.c"])]
    else:
        ext_modules=[]

    packages = ['Cheetah',
                'Cheetah.Templates',
                'Cheetah.Plugins',
                'Cheetah.Macros',
                'Cheetah.Tests',
                'Cheetah.Tools',
                ]

    setup (name = "Cheetah",
           author = "The Cheetah Development Team",
           author_email = "cheetahtemplate-devel@sourceforge.net",
           version = version,
           license = "The Python License",
           description = synopsis,
           long_description = __doc__,
           maintainer = "Tavis Rudd", 
           url = "http://www.cheetahtemplate.org",
           packages = packages,
           package_dir = {'Cheetah':'src'},
           
           ext_modules=ext_modules,

           scripts = ['bin/cheetah-compile',],

           cmdclass = { 'sdist_docs' : sdist_docs },  
           )


