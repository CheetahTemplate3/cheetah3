#!/usr/bin/env python
# $Id: CheetahWrapper.py,v 1.18 2005/01/03 19:57:24 tavis_rudd Exp $
"""Cheetah command-line interface.

2002-09-03 MSO: Total rewrite.
2002-09-04 MSO: Bugfix, compile command was using wrong output ext.
2002-11-08 MSO: Another rewrite.

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@damnsimple.com> and Mike Orr <iron@mso.oz.net>
Version: $Revision: 1.18 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2005/01/03 19:57:24 $
"""
__author__ = "Tavis Rudd <tavis@damnsimple.com> and Mike Orr <iron@mso.oz.net>"
__revision__ = "$Revision: 1.18 $"[11:-2]

import getopt, glob, os, pprint, re, shutil, sys
import cPickle as pickle

from Cheetah.Version import Version
from Cheetah.Compiler import Compiler
from Cheetah.Template import Template
from Cheetah.Utils.Misc import mkdirsWithPyInitFiles
from Cheetah.Utils.optik import OptionParser

optionDashesRE = re.compile(  R"^-{1,2}"  )
moduleNameRE = re.compile(  R"^[a-zA-Z_][a-zA-Z_0-9]*$"  )
   
def fprintfMessage(stream, format, *args):
    if format[-1:] == '^':
        format = format[:-1]
    else:
        format += '\n'
    if args:
        message = format % args
    else:
        message = format
    stream.write(message)

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
  cheetah test [options]                    : Run Cheetah's regression tests
                                            : (same as for unittest)
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
  -R                : recurse subdirectories looking for input files
  --debug           : print lots of diagnostic output to standard error
  --env             : put the environment in the searchList
  --flat            : no destination subdirectories
  --nobackup        : don't make backups
  --pickle FILE     : unpickle FILE and put that object in the searchList
  --stdout, -p      : output to standard output (pipe)
Run "cheetah help" for the main help screen.
"""

##################################################
## CheetahWrapper CLASS

class CheetahWrapper:
    MAKE_BACKUPS = True
    BACKUP_SUFFIX = ".bak"

    def __init__(self):
        self.progName = None
        self.command = None
        self.opts = None
        self.files = None
        self.sourceFiles = []
        self.searchList = []

    ##################################################
    ## VERBOSITY METHODS

    def chatter(self, format, *args):
        """Print a verbose message to stdout.  But don't if .opts.stdout is
           true or .opts.verbose is false.
        """
        if self.opts.stdout or not self.opts.verbose:
            return
        fprintfMessage(sys.stdout, format, *args)


    def debug(self, format, *args):
        """Print a debugging message to stderr, but don't if .debug is
           false.
        """
        if self.opts.debug:
            fprintfMessage(sys.stderr, format, *args)
    
    def warn(self, format, *args):
        """Always print a warning message to stderr.
        """
        fprintfMessage(sys.stderr, format, *args)


    ##################################################
    ## HELPER METHODS

    def _fixExts(self):
        assert self.opts.oext, "oext is empty!"
        iext, oext = self.opts.iext, self.opts.oext
        if iext and not iext.startswith("."):
            self.opts.iext = "." + iext
        if oext and not oext.startswith("."):
            self.opts.oext = "." + oext
    

    def parseOpts(self, args):
        C, D, W = self.chatter, self.debug, self.warn
        self.isCompile = isCompile = self.command[0] == 'c'
        defaultOext = isCompile and ".py" or ".html"
        parser = MyOptionParser()
        pao = parser.add_option
        pao("--idir", action="store", dest="idir", default="")
        pao("--odir", action="store", dest="odir", default="")
        pao("--iext", action="store", dest="iext", default=".tmpl")
        pao("--oext", action="store", dest="oext", default=defaultOext)
        pao("-R", action="store_true", dest="recurse", default=False)
        pao("--stdout", "-p", action="store_true", dest="stdout", default=False)
        pao("--debug", action="store_true", dest="debug", default=False)
        pao("--env", action="store_true", dest="env", default=False)
        pao("--pickle", action="store", dest="pickle", default="")
        pao("--flat", action="store_true", dest="flat", default=False)
        pao("--nobackup", action="store_true", dest="nobackup", default=False)
        self.opts, self.files = opts, files = parser.parse_args(args)
        D("""\
cheetah compile %s
Options are
%s
Files are %s""", args, pprint.pformat(vars(opts)), files)
        self._fixExts()
        if opts.env:
            self.searchList.append(os.environ)
        if opts.pickle:
            f = open(opts.pickle, 'rb')
            unpickled = pickle.load(f)
            f.close()
            self.searchList.append(unpickled)
        opts.verbose = not opts.stdout


    def compileOrFillStdin(self):
            if self.isCompile:
                output = Compiler(file=sys.stdin)
            else:
                output = Template(file=sys.stdin)
            output = str(output)
            sys.stdout.write(output)


    def compileOrFillBundle(self, b):
        C, D, W = self.chatter, self.debug, self.warn
        src = b.src
        dst = b.dst
        base = b.base
        basename = b.basename
        dstDir = os.path.dirname(dst)
        what = self.isCompile and "Compiling" or "Filling"
        C("%s %s -> %s^", what, src, dst) # No trailing newline.
        if os.path.exists(dst) and not self.opts.nobackup:
            bak = b.bak
            C(" (backup %s)", bak) # On same line as previous message.
        else:
            bak = None
            C("")
        if self.isCompile:
            if not moduleNameRE.match(basename):
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
        C, D, W = self.chatter, self.debug, self.warn
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
                W(fmt, sources, dst)
        if isError:
            what = self.isCompile and "Compilation" or "Filling"
            sys.exit("%s aborted due to collisions" % what)
                

    def getBundles(self, sourceFiles):
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
                dbn = basename
                if odir and base.startswith(os.sep):
                    odd = odir
                    while odd != '':
                        i = base.find(odd)
                        if i == 0:
                            dbn = base[len(odd):]
                            if dbn[0] == '/':
                                dbn = dbn[1:]
                            break
                        odd = os.path.dirname(odd)
                        if odd == '/':
                            break
                    dst = os.path.join(odir, dbn + oext)
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
        C, D, W = self.chatter, self.debug, self.warn
        idir = self.opts.idir
        iext = self.opts.iext
        ret = [] 
        for fil in self.files:
            oldRetLen = len(ret)
            D("Expanding %s", fil)
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
                W("Skipping source file '%s', not a plain file.", path)
            else:
                W("Skipping source file '%s', not found.", path)
            if len(ret) > oldRetLen:
                D("  ... found %s", ret[oldRetLen:])
        return ret


    def compileOrFill(self):
        C, D, W = self.chatter, self.debug, self.warn
        opts, files = self.opts, self.files
        if files == ["-"]: 
            self.compileOrFillStdin()
            return
        elif not files and opts.recurse:
            which = opts.idir and "idir" or "current"
            C("Drilling down recursively from %s directory.", which)
            sourceFiles = []
            dir = os.path.join(self.opts.idir, os.curdir)
            os.path.walk(dir, self._expandSourceFilesWalk, sourceFiles)
        elif not files:
            usage(HELP_PAGE1, "Neither files nor -R specified!")
        else:
            sourceFiles = self.expandSourceFiles(files, opts.recurse, True)
        sourceFiles = [os.path.normpath(x) for x in sourceFiles]
        D("All source files found: %s", sourceFiles)
        bundles = self.getBundles(sourceFiles)
        D("All bundles: %s", pprint.pformat(bundles))
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
        # @@MO: Ugly kludge.
        TEST_WRITE_FILENAME = 'cheetah_test_file_creation_ability.tmp'
        try:
            f = open(TEST_WRITE_FILENAME, 'w')
        except:
            sys.exit("""\
Cannot run the tests because you don't have write permission in the current
directory.  The tests need to create temporary files.  Change to a directory
you do have write permission to and re-run the tests.""")
        else:
            f.close()
            os.remove(TEST_WRITE_FILENAME)
        # @@MO: End ugly kludge.
        from Cheetah.Tests import Test
        import Cheetah.Tests.unittest_local_copy as unittest
        del sys.argv[1:] # Prevent unittest from misinterpreting options.
        sys.argv.extend(self.testOpts)
        #unittest.main(testSuite=Test.testSuite)
        #unittest.main(testSuite=Test.testSuite)
        unittest.main(module=Test)
        
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
            self.command = command = optionDashesRE.sub("", argv[1])
            if command == 'test':
                self.testOpts = argv[2:]
            else:
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
