import sys

PY2 = sys.version_info[0] < 3
if PY2:
    # disable flake8 checks on python 3
    string_type = basestring  # noqa
    unicode = unicode  # noqa
else:
    string_type = str
    unicode = str
