#!/usr/bin/env python
# $Id: SetupTools.py,v 1.8 2006/01/01 23:40:54 tavis_rudd Exp $
"""Some tools for extending and working with distutils

CREDITS: This module borrows code and ideas from M.A. Lemburg's excellent setup
tools for the mxBase package.

"""

__author__ = "Tavis Rudd <tavis@damnsimple.com>"
__version__ = "$Revision: 1.8 $"[11:-2]

import os
from os import listdir
import os.path
from os.path import exists, isdir, isfile, join, splitext
import types
import glob
import string
import traceback

from distutils.core import setup
if 'CHEETAH_USE_SETUPTOOLS' in os.environ:
    try:
        # use http://peak.telecommunity.com/DevCenter/setuptools if it's installed
        # requires Py >=2.3
        from setuptools import setup
    except ImportError:   
        from distutils.core import setup

from distutils.core import Command
from distutils.command.install_data import install_data

#imports from Cheetah ...
from src.FileUtils import findFiles

##################################################
## CLASSES ##
   
class mod_install_data(install_data):
    """A modified version of the disutils install_data command that allows data
    files to be included directly in the installed Python package tree.
    """

    def finalize_options(self):

        if self.install_dir is None:
            installobj = self.distribution.get_command_obj('install')
            #self.install_dir = installobj.install_platlib
            self.install_dir = installobj.install_lib
        install_data.finalize_options(self)

    def run (self):

        if not self.dry_run:
            self.mkpath(self.install_dir)
        data_files = self.get_inputs()
        
        for entry in data_files:
            if type(entry) != types.StringType:
                raise ValueError, 'The entries in "data_files" must be strings'
            
            entry = string.join(string.split(entry, '/'), os.sep)
            # entry is a filename or glob pattern
            if entry.startswith('recursive:'):
                entry = entry[len('recursive:'):]
                dir = entry.split()[0]
                globPatterns = entry.split()[1:]
                filenames = findFiles(dir, globPatterns)
            else:
                filenames = glob.glob(entry)
            
            for filename in filenames:
                ## generate the dstPath from the filename
                # - deal with 'package_dir' translations
                topDir, subPath = (filename.split(os.sep)[0],
                                   os.sep.join( filename.split(os.sep)[1:] )
                                   )

                package_dirDict = self.distribution.package_dir
                if package_dirDict:
                    packageDir = topDir
                    for key, val in package_dirDict.items():
                        if val == topDir:
                            packageDir = key
                            break
                else:
                    packageDir = topDir
                dstPath = os.path.join(self.install_dir, packageDir, subPath)

                ## add the file to the list of outfiles
                dstdir = os.path.split(dstPath)[0]
                if not self.dry_run:
                    self.mkpath(dstdir)
                    outfile = self.copy_file(filename, dstPath)[0]
                else:
                    outfile = dstPath
                self.outfiles.append(outfile)
        
##################################################
## FUNCTIONS ##

def run_setup(configurations):
    """ Run distutils setup.

        The parameters passed to setup() are extracted from the list of modules,
        classes or instances given in configurations.

        Names with leading underscore are removed from the parameters.
        Parameters which are not strings, lists, tuples, or dicts are removed as
        well.  Configurations which occur later in the configurations list
        override settings of configurations earlier in the list.

    """
    # Build parameter dictionary
    kws = {}
    for configuration in configurations:
        kws.update(vars(configuration))
    for name, value in kws.items():
        if name[:1] == '_' or \
           type(value) not in (types.StringType,
                               types.ListType,
                               types.TupleType,
                               types.DictType,
                               types.IntType,
                               ):
            del kws[name]

    # Add setup extensions
    cmdclasses = {
        'install_data': mod_install_data,
        }

    kws['cmdclass'] = cmdclasses

    # Invoke distutils setup
    apply(setup, (), kws)

