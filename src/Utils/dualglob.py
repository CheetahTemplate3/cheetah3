#!/usr/bin/env python
"""dualglob.py -- find source/destination filename pairs.

One public function, 'dualglob', takes a list of filenames/paths/directories,
finds the eligible source files (=input files) and constructs the appropriate
destination path (=output file) for each.  It returns a list of DualGlob
objects.

DualGlob objects have the following attributes, all strings:
    src, the source path + filename.
    dst, the destination path + filename.
    base, the base filename (no extension, but possibly with subdirectory).
    basename, the base filename (without the directory or extension).
    srcDir, the directory part of 'src'.
    srcExt, the extension of part 'src'.
    dstDir, the directory part of 'dst'.
    dstExt, the extension part of 'dst'.

The dualglob function recognizes the following arguments:
    files, list of strings.  The search paths.  Usually from the command line.
    iext, string.  The primary extension for source files.
        Two uses:  (1) if a file specified on the command line doesn't exist
        *and* 'addIextIfMissing' is true, add this extension and try again.
        (2) When recursing subdirectories, only filenames with this suffix are
        eligible to be source files.
    oext, string.  The extension for destination files.  dualglob always adds
        this extension to the base name, stripping the source extension.
        Warning: if a file has a period in the base name but no extension
        (e.g., 'file.1'), dualglob will erroneously assume '1' is the source
        extension and strip it.
        Note: if the source file is "-" (standard input), the destination file
        is "-" (standard output).
    idir, string, default ''.  Directory prefix added to all source files.
        Useful if the source files are not in the current directory.
    odir, string, default ''.  Directory prefix added to all destination files.
    recurse, boolean, default False.  If true, recurse directories.  If false,
        raise Error if any file in 'files' is a directory.
    addIextIfMissing, boolean, default True.  See 'iext'.
    verbose, boolean, default True.  Print diagnostic messages to stdout.

For each arg:
    Add src prefix to file (if not empty).
    If source is file, take it.
    Else if source missing, 
        if addIextIfMissing, add iext suffix to file.
            If is file, take it.
            Else print warning and skip it (missing source file).
        Else (if not addText), print warning and skip it (missing source file).
    Else if source is directory,
        if recurse, do recursion (below).
        else (if not recurse), print warning and skip it (is a directory).

"Take it" means:
Construct dst path from dst prefix + arg base (w/o ext) + dst suffix.
Append (src, dst) pair to result list, or (src, dest, base) if returnBaseToo
is true.

"Recurse" means:
For each item in the directory:
    If is directory, recurse it.
    Else if is file and ends with iext suffix, take it.
    Else skip it w/o warning.
Append all the taken pairs to the result list.

Not implemented:
If argument "-" is encountered, it means standard input, and renders
("-", "-") in the result.  The calling program should look for "-" and
treat it as a special case.
"""
import os

try:
    True, False
except NameError:
    True, False = (1==1), (1==0)



class Error(Exception):
    pass


class DualGlob:
    def __init__(self, src, dst, base):
        self.src = src
        self.dst = dst
        self.base = base
        self.basename = os.path.basename(base)
        self.srcDir, fn = os.path.split(src)
        self.srcExt = os.path.splitext(fn)[1][1:]
        self.dstDir, fn = os.path.split(dst)
        self.dstExt = os.path.splitext(fn)[1][1:]



class _SuperGlob:
    def __init__(self):
        self.iext = ''
        self.oext = ''
        self.idir = ''
        self.odir = ''
        self.recurse = False
        #self.addIextIfMissing = True
        self.verbose = True
        self.debug = False
        self.result = []


    def _fixExts(self):
        iext, oext = self.iext, self.oext
        if iext and not iext.startswith("."):
            self.iext = "." + iext
        if oext and not oext.startswith("."):
            self.oext = "." + oext
        elif not oext:
            raise Error("attribute 'oext' must not be empty")
    

    def _evaluateDir(self, orig):
        if self.debug:
            print "Recursing directory %s" % orig
        iext = self.iext
        if not self.recurse:
            raise Error("""\
source file '%s' is directory but recursion flag is False""" % src)
        for fil in os.listdir(orig):
            if orig == os.curdir:
                path = fil
            else:
                path = os.path.join(orig, fil)
            if os.path.isdir(path):
                self._evaluateDir(path)
            elif not fil.endswith(iext):
                continue  # Skip this file, it has the wrong extension.
            else:
                self.evaluate(path, False)


    def evaluate(self, orig, addIextIfMissing=False):
        if self.debug:
            print "Evaluating %s" % orig
        idir = self.idir
        iext = self.iext
        recurse = self.recurse
        verbose = self.verbose
        iextLen = len(iext)
        if orig.endswith(iext):
            base = orig[:-iextLen]
        else:
            base = orig
        src = os.path.join(idir, orig)
        if os.path.isdir(src):
            if recurse:
                self._evaluateDir(src)
            else:
                raise Error("source file '%s' is a directory" % src)
        elif os.path.isfile(src):
            self._includePair(src, base)
        elif ( not src.endswith(iext) ) and addIextIfMissing:
            srcWithExt = src + iext
            self.evaluate(srcWithExt, False)
        elif os.path.exists(src):
            print "Skipping source file '%s', not a plain file." % src
        elif verbose:
            print "Skipping source file '%s', not found." % src


    def _includePair(self, src, base):
        odir = self.odir
        oext = self.oext
        dst = base + oext
        if odir:
           dst = os.path.join(odir, dst)
        dg = DualGlob(src, dst, base)
        if self.debug:
            print vars(dg)
        self.result.append(dg)
#### End class _SuperGlob ###
        

def dualglob(files, iext, oext, idir='', odir='', recurse=True,
    addIextIfMissing=False, verbose=False, debug=False):
    sg = _SuperGlob()
    sg.iext = iext
    sg.oext = oext
    sg.idir = idir
    sg.odir = odir
    sg.recurse = recurse
    #sg.addIextIfMissing = addIextIfMissing
    sg.verbose = verbose
    sg.debug = debug
    sg._fixExts()
    for fil in files:
        sg.evaluate(fil, addIextIfMissing)
    return sg.result


def test():
    """Test routine.  For best results, run this in a directory
    containing 'a.tmpl', 'b.tmpl', 'dir/a.tmpl' and 'dir/b',
    'dir2/a.tmpl', 'dir2/b'.
    """
    files = ['a.tmpl', 'b', 'dir', 'dir2/a.tmpl', 'dir2/b', 'missing']
    result = glob(files, iext='tmpl', oext='py', recurse=True,
        addIextIfMissing=True, verbose=True)
    for tup in result:
        print tup



# vim: shiftwidth=4 tabstop=4 expandtab
