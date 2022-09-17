from glob import glob
import os
import os.path
import sys

from distutils.command.install_data import install_data
from distutils.errors import CCompilerError, DistutilsExecError, \
    DistutilsPlatformError
from setuptools import setup
from setuptools.command.build_ext import build_ext

# imports from Cheetah ...
from Cheetah.FileUtils import findFiles
from Cheetah.compat import string_type

if sys.platform == 'win32':
    # 2.6's distutils.msvc9compiler can raise an IOError when failing to
    # find the compiler
    ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError,
                  IOError, TypeError)
else:
    ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError)

##################################################
# CLASSES ##


class BuildFailed(Exception):
    pass


class mod_build_ext(build_ext):
    """A modified version of build_ext command that raises an
    exception when building of the extension fails.
    """

    def run(self):
        try:
            build_ext.run(self)
        except DistutilsPlatformError as x:
            raise BuildFailed(x)

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except ext_errors as x:
            raise BuildFailed(x)


class mod_install_data(install_data):
    """A modified version of the disutils install_data command that allows data
    files to be included directly in the installed Python package tree.
    """

    def finalize_options(self):

        if self.install_dir is None:
            installobj = self.distribution.get_command_obj('install')
            # self.install_dir = installobj.install_platlib
            self.install_dir = installobj.install_lib
        install_data.finalize_options(self)

    def run(self):

        if not self.dry_run:
            self.mkpath(self.install_dir)
        data_files = self.get_inputs()

        for entry in data_files:
            if not isinstance(entry, string_type):
                raise ValueError('The entries in "data_files" must be strings')

            entry = os.sep.join(entry.split('/'))
            # entry is a filename or glob pattern
            if entry.startswith('recursive:'):
                entry = entry[len('recursive:'):]
                dir = entry.split()[0]
                globPatterns = entry.split()[1:]
                filenames = findFiles(dir, globPatterns)
            else:
                filenames = glob(entry)

            for filename in filenames:
                # generate the dstPath from the filename
                # - deal with 'package_dir' translations
                topDir, subPath = (filename.split(os.sep)[0],
                                   os.sep.join(filename.split(os.sep)[1:])
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

                # add the file to the list of outfiles
                dstdir = os.path.split(dstPath)[0]
                if not self.dry_run:
                    self.mkpath(dstdir)
                    outfile = self.copy_file(filename, dstPath)[0]
                else:
                    outfile = dstPath
                self.outfiles.append(outfile)

##################################################
# FUNCTIONS ##


def run_setup(configurations):
    """Run distutils/setuptools setup.

    The parameters passed to setup() are extracted from the list of modules,
    classes or instances given in configurations.

    Names with leading underscore are removed from the parameters.
    Parameters which are not strings, lists, tuples, or dicts are removed as
    well.  Configurations which occur later in the configurations list
    override settings of configurations earlier in the list.
    """
    # Build parameter dictionary
    kws = {}
    newkws = {}
    for configuration in configurations:
        kws.update(vars(configuration))
    for name, value in kws.items():
        if name[:1] == '_':
            continue
        if not isinstance(value, (string_type, list, tuple, dict, int)):
            continue
        newkws[name] = value
    kws = newkws

    # Add setup extensions
    cmdclasses = {
        'build_ext': mod_build_ext,
        'install_data': mod_install_data,
    }

    kws['cmdclass'] = cmdclasses

    try:
        setup(**kws)
    except BuildFailed as x:
        print("One or more C extensions failed to build.")
        print("Details: %s" % x)
        if os.environ.get('CHEETAH_C_EXTENSIONS_REQUIRED'):
            raise x
        print("Retrying without C extensions enabled.")

        del kws['ext_modules']
        setup(**kws)

        print("One or more C extensions failed to build.")
        print("Performance enhancements will not be available.")
        print("Pure Python installation succeeded.")
