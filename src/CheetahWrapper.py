#!/usr/bin/env python
# $Id: CheetahWrapper.py,v 1.13 2002/11/10 09:36:22 hierro Exp $
"""Cheetah command-line interface.

2002-09-03 MSO: Total rewrite.
2002-09-04 MSO: Bugfix, compile command was using wrong output ext.
2002-11-08 MSO: Another rewrite.

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@damnsimple.com> and Mike Orr <iron@mso.oz.net>
Version: $Revision: 1.13 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2002/11/10 09:36:22 $
"""
__author__ = "Tavis Rudd <tavis@damnsimple.com> and Mike Orr <iron@mso.oz.net>"
__revision__ = "$Revision: 1.13 $"[11:-2]

##################################################
## DEPENDENCIES

import getopt, glob, os, pprint, re, shutil, sys
import cPickle as pickle

from _properties import Version
from Compiler import Compiler
from Template import Template
from Cheetah.Utils.Misc import mkdirsWithPyInitFiles
from Cheetah.Utils.optik import OptionParser

##################################################
## GLOBALS & CONSTANTS

try:
    True,False
except NameError:
    True, False = (1==1),(1==0)

optionDashesRx = re.compile(  R"^-{1,2}"  )
moduleNameRx = re.compile(  R"^[a-zA-Z_][a-zA-Z_0-9]*$"  )
   
class Error(Exception):
    pass


class Bundle:
    """Wrap the source, destination and backup paths in one neat little class.
       Used by CheetahWrapper.getBundles().
    """
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "<Bundle %r>" % self.__dict__


class MyOptionParser(OptionParser):
    standard_option_list = [] # We use commands for Optik's standard options.

    def error(self, msg):
        """Print our usage+error page."""
        usage(HELP_PAGE2, msg)

    def print_usage(self, file=None):
        """Our usage+error page already has this."""
        pass
    

##################################################
## USAGE FUNCTION & MESSAGES

def usage(usageMessage, errorMessage="", out=sys.stderr):
    """Write help text, an optional error message, and abort the program.
    """
    out.write(WRAPPER_TOP)
    out.write(usageMessage)
    exitStatus = 0
    if errorMessage:
        out.write('\n')
        out.write("*** USAGE ERROR ***: %s\n" % errorMessage)
        exitStatus = 1
    sys.exit(exitStatus)
             

WRAPPER_TOP = """\
         __  ____________  __
         \ \/            \/ /
          \/    *   *     \/    CHEETAH %(Version)s Command-Line Tool
           \      |       / 
            \  ==----==  /      by Tavis Rudd <tavis@damnsimple.com>
             \__________/       and Mike Orr <iron@mso.oz.net>
              
""" % globals()


HELP_PAGE1 = """\
USAGE:
------
  cheetah compile [options] [FILES ...]     : Compile template definitions
  cheetah fill [options] [FILES ...]        : Fill template definitions
  cheetah help                              : Print this help message
  cheetah options                           : Print options help message
  cheetah test                              : Run Cheetah's regression tests
  cheetah version                           : Print Cheetah version number

You may abbreviate the command to the first letter; e.g., 'h' == 'help'.
If FILES is a single "-", read standard input and write standard output.
Run "cheetah options" for the list of valid options.
"""

HELP_PAGE2 = """\
OPTIONS FOR "compile" AND "fill":
---------------------------------
  --idir DIR, --odir DIR : input/output directories (default: current dir)
  --iext EXT, --oext EXT : input/output filename extensions
    (default for compile: tmpl/py,  fill: tmpl/html)
  -R            : recurse subdirectories looking for input files
  --debug       : print lots of diagnostic output to standard error
  --env         : put the environment in the searchList
  --flat        : no destination subdirectories
  --nobackup    : don't make backups
  --pickle FILE : unpickle FILE and put that object in the searchList
  --stdout, -p  : output to standard output (pipe)

Run "cheetah help" for the main help screen.
"""

##################################################
## CheetahWrapper CLASS

class CheetahWrapper:
    MAKE_BACKUPS = True
    BACKUP_SUFFIX = "_bak"

    def __init__(self):
        self.progName = None
        self.command = None
        self.opts = None
        self.files = None
        self.sourceFiles = []
        self.searchList = []

    ##################################################
    ## HELPER METHODS

    def backup(self, dst):
        """Back up a destination file and return the backup path."""

        if not os.path.exists(dst):
            return None
        backup = dst + self.BACKUP_SUFFIX
        shutil.copyfile(dst, backup)
        return backup

    def _fixExts(self):
        assert self.opts.oext, "oext is empty!"
        iext, oext = self.opts.iext, self.opts.oext
        if iext and not iext.startswith("."):
            self.opts.iext = "." + iext
        if oext and not oext.startswith("."):
            self.opts.oext = "." + oext
    

    def parseOpts(self, args):
        self.isCompile = isCompile = self.command[0] == 'c'
        defaultOext = isCompile and ".py" or ".html"
        parser = MyOptionParser()
        pao = parser.add_option
        pao("--idir", action="store", dest="idir", default="")
        pao("--odir", action="store", dest="odir", default="")
        pao("--iext", action="store", dest="iext", default=".tmpl")
        pao("--oext", action="store", dest="oext", default=defaultOext)
        pao("-R", action="store_true", dest="recurse", default=0)
        pao("--stdout", "-p", action="store_true", dest="stdout", default=0)
        pao("--debug", action="store_true", dest="debug", default=0)
        pao("--env", action="store_true", dest="env", default=0)
        pao("--pickle", action="store_true", dest="pickle", default=0)
        pao("--flat", action="store_true", dest="flat", default=0)
        pao("--nobackup", action="store_true", dest="nobackup", default=0)
        self.opts, self.files = opts, files = parser.parse_args(args)
        if opts.debug:
            print >>sys.stderr, "cheetah compile", args
            print >>sys.stderr, "Options are"
            print >>sys.stderr, pprint.pformat(vars(opts))
            print >>sys.stderr, "Files are", files
        self._fixExts()
        if opts.env:
            self.searchList.append(os.environ)
        if opts.pickle:
            f = open(opts.pickle, 'rb')
            unpickled = pickle.load(f)
            f.close()
            self.searchList.append(unpickled)


    def compileOrFillStdin(self):
            if self.isCompile:
                output = Compiler(file=sys.stdin)
            else:
                output = Template(file=sys.stdin)
            output = str(output)
            sys.stdout.write(output)


    def compileOrFillBundle(self, b):
        src = b.src
        dst = b.dst
        base = b.base
        basename = b.basename
        dstDir = os.path.dirname(dst)
        what = self.isCompile and "Compiling" or "Filling"
        print what, src, "->", dst, # No trailing newline.
        if os.path.exists(dst) and not self.opts.nobackup:
            bak = b.bak
            print "(backup %s)" % bak # On same line as previous message.
        else:
            bak = None
            print
        if self.isCompile:
            if not moduleNameRx.match(basename):
                tup = basename, src
                raise Error("""\
%s: base name %s contains invalid characters.  It must
be named according to the same rules as Python modules.""" % tup)
            obj = Compiler(file=src, \
                moduleName=basename, mainClassName=basename)
        else:
            obj = Template(file=src, searchList=self.searchList)
        output = str(obj)
        if bak:
            shutil.copyfile(dst, bak)
        if dstDir and not os.path.exists(dstDir):
            if self.isCompile:
                mkdirsWithPyInitFiles(dstDir)
            else:
                os.makedirs(dstDir)
        if self.opts.stdout:
            sys.stdout.write(output)
        else:
            f = open(dst, 'w')
            f.write(output)
            f.close()

    def _checkForCollisions(self, bundles):
        """Check for multiple source paths writing to the same destination
           path.
        """
        isError = False
        dstSources = {}
        for b in bundles:
            if dstSources.has_key(b.dst):
                dstSources[b.dst].append(b.src)
            else:
                dstSources[b.dst] = [b.src]
        keys = dstSources.keys()
        keys.sort()
        for dst in keys:
            sources = dstSources[dst]
            if len(sources) > 1:
                isError = True
                sources.sort()
                fmt = \
"Collision: multiple source files %s map to one destination file %s"
                print fmt % (sources, dst)
        if isError:
            what = self.isCompile and "Compilation" or "Filling"
            sys.exit("%s aborted due to collisions" % what)
                

    def getBundles(self, sourceFiles):
        debug = self.opts.debug
        flat = self.opts.flat
        idir = self.opts.idir
        iext = self.opts.iext
        nobackup = self.opts.nobackup
        odir = self.opts.odir
        oext = self.opts.oext
        idirSlash = idir + os.sep
        bundles = []
        for src in sourceFiles:
            # 'base' is the subdirectory plus basename.
            base = src
            if idir and src.startswith(idirSlash):
                base = src[len(idirSlash):]
            if iext and base.endswith(iext):
                base = base[:-len(iext)]
            basename = os.path.basename(base)
            if flat:
                dst = os.path.join(odir, basename + oext)
            else:
                dst = os.path.join(odir, base + oext)
            bak = dst + self.BACKUP_SUFFIX
            b = Bundle(src=src, dst=dst, bak=bak, base=base, basename=basename)
            bundles.append(b)
        return bundles


    def _expandSourceFilesWalk(self, arg, dir, files):
        """Recursion extension for .expandSourceFiles().
           This method is a callback for os.path.walk().
           'arg' is a list to which successful paths will be appended.
        """
        iext = self.opts.iext
        for fil in files:
            path = os.path.join(dir, fil)
            if   path.endswith(iext) and os.path.isfile(path):
                arg.append(path)
            elif os.path.islink(path) and os.path.isdir(path):
                os.path.walk(path, self._expandSourceFilesWalk, arg)
            # If is directory, do nothing; 'walk' will eventually get it.


    def expandSourceFiles(self, files, recurse, addIextIfMissing):
        """Calculate source paths from 'files' by applying the 
           command-line options.
        """
        idir = self.opts.idir
        iext = self.opts.iext
        debug = self.opts.debug
        ret = [] 
        for fil in self.files:
            oldRetLen = len(ret)
            if debug:
                print "Expanding", fil
            path = os.path.join(idir, fil)
            pathWithExt = path + iext # May or may not be valid.
            if os.path.isdir(path):
                if recurse:
                    os.path.walk(path, self._expandSourceFilesWalk, ret)
                else:
                    raise Error("source file '%s' is a directory" % path)
            elif os.path.isfile(path):
                ret.append(path)
            elif addIextIfMissing and not path.endswith(iext) and \
                os.path.isfile(pathWithExt):
                ret.append(pathWithExt)
                # Do not recurse directories discovered by iext appending.
            elif os.path.exists(path):
                print "Skipping source file '%s', not a plain file." % path
            else:
                print "Skipping source file '%s', not found." % path
            if debug and len(ret) > oldRetLen:
                print "  ... found", ret[oldRetLen:]
        return ret


    def compileOrFill(self):
        opts, files = self.opts, self.files
        debug = self.opts.debug
        if files == ["-"]: 
            self.compileOrFillStdin()
            return
        elif not files and opts.recurse:
            which = opts.idir and "idir" or "current"
            print "Drilling down recursively from %s directory." % which
            sourceFiles = []
            dir = os.path.join(self.opts.idir, os.curdir)
            os.path.walk(dir, self._expandSourceFilesWalk, sourceFiles)
        elif not files:
            usage(HELP_PAGE1, "Neither files nor -R specified!")
        else:
            sourceFiles = self.expandSourceFiles(files, opts.recurse, True)
        sourceFiles = [os.path.normpath(x) for x in sourceFiles]
        if debug:
            print "All source files found:", sourceFiles
        bundles = self.getBundles(sourceFiles)
        if debug:
            print "All bundles:", pprint.pformat(bundles)
        if self.opts.flat:
            self._checkForCollisions(bundles)
        for b in bundles:
            self.compileOrFillBundle(b)
            

    ##################################################
    ## COMMAND METHODS

    def compile(self):
        self.compileOrFill()

    def fill(self):
        self.compileOrFill()

    def help(self):
        usage(HELP_PAGE1, "", sys.stdout)

    def options(self):
        usage(HELP_PAGE2, "", sys.stdout)

    def test(self):
        from Cheetah.Tests import Test
        import Cheetah.Tests.unittest_local_copy as unittest
        del sys.argv[1:] # Prevent unittest from misinterpreting options.
        unittest.main(testSuite=Test.testSuite)

    def version(self):
        print Version

    # If you add a command, also add it to the 'meths' variable in main().

    ##################################################
    ## MAIN ROUTINE

    def main(self, argv=None):
        """The main program controller."""

        if argv is None:
            argv = sys.argv

        # Step 1: Determine the command and arguments.
        try:
            self.progName = progName = os.path.basename(argv[0])
            self.command = command = optionDashesRx.sub("", argv[1])
            self.parseOpts(argv[2:])
        except IndexError:
            usage(HELP_PAGE1, "not enough command-line arguments")

        # Step 2: Call the command
        meths = (self.compile, self.fill, self.help, self.options,
            self.test, self.version)
        for meth in meths:
            methName = meth.__name__
            # Or meth.im_func.func_name
            # Or meth.func_name (Python >= 2.1 only, sometimes works on 2.0)
            methInitial = methName[0]
            if command in (methName, methInitial):
                sys.argv[0] += (" " + methName)
                # @@MO: I don't necessarily agree sys.argv[0] should be 
                # modified.
                meth()
                return
        # If none of the commands matched.
        usage(HELP_PAGE1, "unknown command '%s'" % command)

    #run = main




##################################################
## if run from the command line
if __name__ == '__main__':  CheetahWrapper().main()

# vim: shiftwidth=4 tabstop=4 expandtab
