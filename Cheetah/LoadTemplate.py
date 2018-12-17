import imp
import os
import sys
from Cheetah.ImportHooks import CheetahDirOwner


def _loadTemplate(templatePath, debuglevel=0):
    """Load template by full or relative path (including extension)

    Example: template = loadTemplate('views/index.tmpl')

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
        # Add all "modules" to sys.modules
        components = []
        for d in dirname_list:
            components.append(d)
            _mod_name = '.'.join(components)
            _mod = imp.new_module(_mod_name)
            _d = os.path.abspath(os.sep.join(components))
            _mod.__file__ = _d
            _mod.__path__ = [_d]
            sys.modules[_mod_name] = _mod
    template_dir = CheetahDirOwner(drive + dirname)
    if ext:
        template_dir.templateFileExtensions = (ext,)
    template_dir.debuglevel = debuglevel
    mod = template_dir.getmod(filename)
    fqname = os.path.join(dirname, filename).replace(os.sep, '.')
    mod.__name__ = fqname
    sys.modules[fqname] = mod
    co = mod.__co__
    del mod.__co__
    exec(co, mod.__dict__)
    return mod, filename


def loadTemplateModule(templatePath, debuglevel=0):
    return _loadTemplate(templatePath, debuglevel=debuglevel)[0]


def loadTemplateClass(templatePath, debuglevel=0):
    mod, filename = _loadTemplate(templatePath, debuglevel=debuglevel)
    return getattr(mod, filename)
