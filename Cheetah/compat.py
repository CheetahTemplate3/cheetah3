import os
import sys

# Compatability definitions (inspired by six)
PY2 = sys.version_info[0] < 3
if PY2:
    # disable flake8 checks on python 3
    string_type = basestring  # noqa
    unicode = unicode  # noqa
else:
    string_type = str
    unicode = str

if PY2:
    import imp

    def load_module_from_file(base_name, module_name, filename):
        fp, pathname, description = imp.find_module(
            base_name, [os.path.dirname(filename)])
        try:
            module = imp.load_module(module_name, fp, pathname, description)
        finally:
            fp.close()
        return module
else:
    import importlib.util

    def load_module_from_file(base_name, module_name, filename):
        specs = importlib.util.spec_from_file_location(module_name, filename)
        return specs.loader.load_module()
