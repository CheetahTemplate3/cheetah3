import os.path
import string
from Cheetah.compat import unicode

letters = None
try:
    letters = string.ascii_letters
except AttributeError:
    letters = string.letters

_l = ['_'] * 256
for c in string.digits + letters:
    _l[ord(c)] = c
_pathNameTransChars = ''.join(_l)
del _l, c


def convertTmplPathToModuleName(tmplPath,
                                _pathNameTransChars=_pathNameTransChars,
                                splitdrive=os.path.splitdrive,
                                ):
    try:
        moduleName = splitdrive(tmplPath)[1].translate(_pathNameTransChars)
    except (UnicodeError, TypeError):
        moduleName = unicode(splitdrive(tmplPath)[1])\
            .translate(unicode(_pathNameTransChars))
    return moduleName
