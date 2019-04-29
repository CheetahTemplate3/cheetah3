News
====

3.2.2 (2019-04-29)
------------------

Minor features:

  - Replaced outdated and insecure ``mktemp`` with ``mkstemp``.

Bug fixes:

  - Fixed bugs in ``TemplateCmdLineIface.py``: read binary pickles
    from stdin and files.

Tests:

  - Use ``cgi.escape()`` for Python 2, ``html.escape()`` for Python 3.
  - Created tests for ``TemplateCmdLineIface``.


3.2.1 (2019-03-19)
------------------

Minor features:

  - Changed ``LoadTemplate.loadTemplate{Module,Class}``:
    the loaded module's ``__name__`` set to just the file name.
  - Use ``imp`` for Python 2, ``importlib`` for Python 3.

Bug fixes:

  - Fix a bug in ``LoadTemplate.loadTemplate{Module,Class}``:
    raise ``ImportError`` if the template was not found.

CI:

  - At Travis deploy wheels for macOS.
  - At AppVeyor deploy wheels directly to PyPI.


3.2.0 (2019-02-06)
------------------

Features:

  - Dropped support for Python 3.3.
  - Implement ``LoadTemplate.loadTemplate{Module,Class}``
    to load templates from ``.py[co]``, ``.py`` or ``.tmpl``.
  - ``CheetahDirOwner`` caches compiled template in the template directory.
  - ``CheetahDirOwner`` now silently ignores errors on compiled templates
    writing. To get tracebacks set ``CheetahDirOwner.debuglevel = 1``.
  - ``CheetahDirOwner`` and ``DirOwner`` byte-compile compiled templates
    to ``.pyc/.pyo``. Errors on writing are silently ignored.

Minor features:

  - Implement ``Compiler.__unicode__`` under Python 2
    and ``Compiler.__bytes__`` under Python 3.

Bug fixes:

  - Fix a bug in ``Compiler.__str__``: under Python 2 the method
    always returns str; it encodes unicode to str using encoding from the
    compiled source. Under Python 3 the method decodes bytes to str.

Code:

  - Source code was made flake8-clean using the latest flake8.

Documentation:

  - Remove outdated section markers.
  - Better documentation for ImportHooks.
  - Add an example of a universal makefile.

CI:

  - Run tests with Python 3.7.
  - At Travis deploy sdists and wheels for tags.


3.1.0 (2018-03-03)
------------------

Features:

  - Fix Cheetah to work with PyPy. Pull request by Mathias Stearn.

Minor features:

  - Code cleanup: fix code style to satisfy flake8 linter.

Documentation:

  - Rename www directory to docs.

Tests:

  - Run pypy tests at AppVeyor.
  - Use remove-old-files.py from ppu to cleanup pip cache
    at Travis and AppVeyor.


3.0.1 (2018-02-27)
------------------

Bug fixes:

  - Fix a minor bug in Compiler.


3.0.0 (2017-05-07)
------------------

Major features:

  - !!!THIS RELEASE REQUIRES RECOMPILATION OF ALL COMPILED CHEETAH TEMPLATES!!!
  - Stop supporting Python older than 2.7.
  - Update code to work with Python 3.3+. Tested with 3.3, 3.4, 3.5 and 3.6.

Minor features:

  - Use '/usr/bin/env python' for scripts;
    this allows eggs/wheels to be installed into virtual environments.

Bug fixes:

  - Fix a bug in multiple inheritance (#extend Parent1, Parent2).
    Pull request by Jonathan Ross Rogers.
  - Fix bugs in pure-python NameMapper.py. Bugs reported by Noah Ingham,
    patches by Adam Karpierz, tests by Oleg Broytman.

Tests:

  - Run tests at Travis (Linux) and AppVeyor (w32) with Python 2.7, 3.3, 3.4,
    3.5 and 3.6; x86 and x64.
  - Fix a problem in Unicode tests - cleanup temporary files.

`Older news`_

.. _`Older news`: news2.html
