#!/usr/bin/env python
# $Id: CheetahWrapper.py,v 1.10 2002/10/20 03:29:01 hierro Exp $
"""Cheetah command-line interface.

2002-09-03 MSO: Total rewrite.
2002-09-04 MSO: Bugfix, compile command was using wrong output ext.

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@damnsimple.com> and Mike Orr <iron@mso.oz.net>
Version: $Revision: 1.10 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2002/10/20 03:29:01 $
"""
__author__ = "Tavis Rudd <tavis@damnsimple.com> and Mike Orr <iron@mso.oz.net>"
__revision__ = "$Revision: 1.10 $"[11:-2]

##################################################
## DEPENDENCIES

import getopt, glob, os, pprint, re, shutil, sys
import cPickle as pickle

from _properties import Version
from Compiler import Compiler
from Template import Template
from Cheetah.Utils.dualglob import dualglob
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
  -R : recurse subdirectories looking for input files
  -p : output to standard output (pipe)
  --debug : print lots of diagnostic output to standard error
  --env : put the environment in the searchList
  --pickle FILE : unpickle FILE and put that object in the searchList

Run "cheetah help" for the main help screen.
"""

##################################################
## MAIN ROUTINE

class CheetahWrapper:

    MAKE_BACKUPS = True
    BACKUP_SUFFIX = "_bak"

    def __init__(self):
        self.progName = None
        self.command = None
        self.opts = None
        self.files = None
        self.searchList = []

    ##################################################
    ## HELPER METHODS

    def backup(self, dst):
        """Back up a file verbosely."""

        if not os.path.exists(dst):
            return None
        backup = dst + self.BACKUP_SUFFIX
        shutil.copyfile(dst, backup)
        return backup


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
        pao("-p", action="store_true", dest="stdout", default=0)
        pao("--debug", action="store_true", dest="debug", default=0)
        pao("--env", action="store_true", dest="env", default=0)
        pao("--pickle", action="store_true", dest="pickle", default=0)
        self.opts, self.files = opts, files = parser.parse_args(args)
        if opts.debug:
            print >>sys.stderr, "cheetah compile", args
            print >>sys.stderr, "Options are"
            print >>sys.stderr, pprint.pformat(vars(opts))
            print >>sys.stderr, "Files are", files
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


    def verifyBasenameIsLegalModuleName(self, base, src):
        """Does what it says.
           
           in : base, string, the base name to check.
                src, string, the entire source path (for error message).
        """

        if not moduleNameRx.match(base):
            raise Error(
                "%s: base name %s contains invalid characters.  It must" \
                " be named according to the same rules as Python modules."
                % (base, src) )


    def compileOrFillPair(self, pair):
        src = pair.src
        dst = pair.dst
        base = pair.base
        basename = pair.basename
        dstDir = pair.dstDir
        what = self.isCompile and "Compiling" or "Filling"
        print what, src, "->", dst, # No trailing newline.
        try:
            if self.isCompile:
                self.verifyBasenameIsLegalModuleName(basename, src)
                obj = Compiler(file=src, \
                    moduleName=basename, mainClassName=basename)
            else:
                obj = Template(file=src, searchList=self.searchList)
            output = str(obj)
            bak = self.backup(dst)
        except:
            print # Print pending newline before error message.
            raise
        if bak:
            print "(backup %s)" % bak # On same line as previous message.
        else:
            print # Print pending newline.
        #if not os.path.exists(dstDir):
        #    os.makedirs(dstDir) # XXX Commented, buggy.
        f = open(dst, 'w')
        f.write(output)
        f.close()


    def compileOrFill(self):
        opts, files = self.opts, self.files
        if files == ["-"]: 
            self.compileOrFillStdin()
            return
        elif not files and opts.recurse:
            print "Drilling down recursively from current directory."
            files = [os.curdir]
        elif not files:
            usage(HELP_PAGE1, "Neither files nor -R specified!")
        pairs = dualglob(files, iext=opts.iext, oext=opts.oext,
            idir=opts.idir, odir=opts.odir, recurse=opts.recurse,
            addIextIfMissing=True, verbose=True, debug=opts.debug)
        if opts.debug:
            print >>sys.stderr, "I will operate on the following files:"
            for pair in pairs:
                print >>sys.stderr, "  %s -> %s" % (pair.src, pair.dst)
        for pair in pairs:
            self.compileOrFillPair(pair)
            

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
            #opts, files = self.opts, self.files
        except IndexError:
            usage(HELP_PAGE1, "not enough command-line arguments")

        # Step 2: Call the command
        meths = (self.compile, self.fill, self.help, self.options,
            self.test, self.version)
        for meth in meths:
            methName = meth.func_name
            methInitial = methName[0]
            if command in (methName, methInitial):
                sys.argv[0] += (" " + methName)
                # @@MO: I don't necessarily agree sys.argv[0] should be 
                # modified.
                meth()
                return
        # If none of the commands matched.
        usage(HELP_PAGE1, "unknown command '%s'" % command)

    run = main




##################################################
## if run from the command line
if __name__ == '__main__':  CheetahWrapper().main()

# vim: shiftwidth=4 tabstop=4 expandtab
