import os
import sys
from Cheetah.ImportHooks import CheetahDirOwner


def loadTemplate(templatePath, debuglevel=0):
    """Load template by full or relative path (including extension)

    Example: template = loadTemplate('views/index.tmpl')

    Template is loaded from from .py[co], .py or .tmpl -
    whatever will be found. Files *.tmpl are compiled to *.py;
    *.py are byte-compiled to *.py[co]. Compiled files are cached
    in the template directory. Errors on writing are silently ignored.
    """
    dirname, filename = os.path.split(templatePath)
    filename, ext = os.path.splitext(filename)
    template_dir = CheetahDirOwner(dirname)
    if ext:
        template_dir.templateFileExtensions = (ext,)
    template_dir.debuglevel = debuglevel
    mod = template_dir.getmod(filename)
    fqname = templatePath.replace(os.sep, '.')
    mod.__name__ = fqname
    sys.modules[fqname] = mod
    co = mod.__co__
    del mod.__co__
    exec(co, mod.__dict__)
    return mod
