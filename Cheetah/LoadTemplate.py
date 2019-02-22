import os
import sys
from Cheetah.ImportHooks import CheetahDirOwner


def loadTemplateModule(templatePath, debuglevel=0):
    """Load template's module by full or relative path (extension is optional)

    Examples:

        template = loadTemplateModule('views/index')
        template = loadTemplateClass('views/index.tmpl')

    Template is loaded from from .py[co], .py or .tmpl -
    whatever will be found. Files *.tmpl are compiled to *.py;
    *.py are byte-compiled to *.py[co]. Compiled files are cached
    in the template directory. Errors on writing are silently ignored.
    """
    drive, localPath = os.path.splitdrive(templatePath)
    dirname, filename = os.path.split(localPath)
    filename, ext = os.path.splitext(filename)
    if dirname:
        # Cleanup: Convert /Templates//views/ -> /Templates/views
        dirname_list = dirname.replace(os.sep, '/').split('/')
        dirname_list = [d for (i, d) in enumerate(dirname_list)
                        if i == 0 or d]  # Preserve root slash
        dirname = os.sep.join(dirname_list)
    template_dir = CheetahDirOwner(drive + dirname)
    if ext:
        template_dir.templateFileExtensions = (ext,)
    template_dir.debuglevel = debuglevel
    mod = template_dir.getmod(filename)
    if mod is None:
        raise ImportError("Cannot find {}".format(templatePath))
    mod.__name__ = filename
    sys.modules[filename] = mod
    co = mod.__co__
    del mod.__co__
    exec(co, mod.__dict__)
    return mod


def loadTemplateClass(templatePath, debuglevel=0):
    """Load template's class by full or relative path"""
    mod = loadTemplateModule(templatePath, debuglevel=debuglevel)
    return getattr(mod, mod.__name__)
