#!/usr/bin/env python
"""Convert files from LaTeX format to ReStructured Text.

   This converter is meant only for saving keystrokes.  It won't catch
   everything and it may misformat stuff, so proofread the file after
   processing.

   "Verbatim" blocks are not converted due to the difficulty in placing the
   preceding colon(s) and indenting every line.
"""
import os, re, shutil, sys

def convert(filename):
    print "Processing file", filename
    backup = filename + ".bak"
    shutil.copy2(filename, backup)
    f = open(filename, 'r+')
    text = f.read()
    text = re.sub( R"%%%+", R"", text)
    text = re.sub( R"\\section\{(.*?)\}",    R"\1\n" + ("=" * 40), text)
    text = re.sub( R"\\subsection\{(.*?)\}", R"\1\n" + ("-" * 40), text)
    text = re.sub( R"\\label\{(.*?)\}",      R"\n..\n    :label: \1", text)
    text = re.sub( R"``|''",                 R'"',      text)
    text = re.sub( R"(?s)\{\\em (.*?)\}",    R"*\1*", text)
    text = re.sub( R"(?s)\{\\bf (.*?)\}",    R"**\1**", text)
    text = re.sub( R"(?s)\\code\{(.*?)\}",   R"``\1``", text)
    text = re.sub( R"\\(begin|end)\{(itemize|enumerate)\}\n", R"", text)
    text = re.sub( R"\\item ",                R"* ", text)
    #text = re.sub( 
    #    R"(?sm)(\w):\n\s*^\\begin\{verbatim\}\s*(.*?)\\end\{verbatim\}", 
    #    R"\1::\n\n\2", text)
    f.seek(0)
    f.write(text)
    f.truncate()
    f.close()


def main():
    if len(sys.argv) < 2:
        prog = os.path.basename(sys.argv[0])
        raise SystemExit("usage: %s FILENAMES ..." % prog)
    for filename in sys.argv[1:]:
        convert(filename)

if __name__ == "__main__":  main()
