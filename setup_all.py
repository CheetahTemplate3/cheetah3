#!/usr/bin/env python
"""This version of the setup.py script is used to install Cheetah + all third_party_packages

"""
import string, os, sys
cwd = os.getcwd()

### install the main package
execfile('setup.py')                    

### then install all the third_party_packages
packages=[]
for p in packages:
   d = os.path.join(cwd, 'third_party_packages', p)
   os.chdir(d)
   print "Working on", d, "(", os.getcwd(), ")"
   os.system(sys.executable+' setup.py '+string.join(sys.argv[1:],' '))
