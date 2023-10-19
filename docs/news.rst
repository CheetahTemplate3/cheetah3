News
====

Development (master)
--------------------

Minor features:

  - Protect ``import cgi`` in preparation to Python 3.13.

Tests:

  - Run tests with Python 3.12.

CI:

  - GHActions: Ensure ``pip`` only if needed

    This is to work around a problem in conda with Python 3.7 -
    it brings in wrong version of ``setuptools`` incompatible with Python 3.7.

3.3.2 (2023-08-08)
------------------

Bug fixes:

  - Fixed printing to stdout in ``CheetahWrapper``.

CI:

   - CI(GHActions): Install all Python and PyPy versions from ``conda-forge``.

3.3.1 (2022-12-25)
------------------

Bug fixes:

  - Fixed ``ImportHooks`` under PyPy3.

Tests:

  - Run tests with PyPy3.

CI:

  - Use ``conda`` to install older Pythons

    Ubuntu >= 22 and ``setup-python`` dropped Pythons < 3.7.
    Use ``s-weigand/setup-conda`` instead of ``setup-python``.

3.3.0.post1 (2022-11-26)
------------------------

Tests:

  - Run tests with Python 3.11.

  - Fix DeprecationWarning: ``unittest.findTestCases()`` is deprecated. Use
    ``unittest.TestLoader.loadTestsFromModule()`` instead.

CI:

  - Publish wheels at Github Releases.

3.3.0 (2022-10-10)
------------------

Great move:

  - PyPI has wrongfully classified project ``Cheetah3`` as "critical".
    This puts a burden to use 2FA to manage the project at PyPI. To
    avoid the burden the project is renamed to ``CT3`` at PyPI.
    There will be no updates for ``Cheetah3``.
    Sorry for the inconvenience!

Minor features:

  - Use relative imports everywhere.

Tests:

  - Run pure-python ``NameMapper`` tests in a separate process.

  - Fixed a bug in tests with pure-python ``NameMapper``.

  - Add Python 3.10 to ``tox.ini``.

CI:

  - Migrated to GitHub Actions.

    Due to the absent of Python 3.4 at GH Actions tests are not run and
    wheels are not built. Installation from sources should work.

    Due to GH Actions lacking old compilers for w32/w64 releases for old
    Python versions (currently 2.7) are packaged without compiled
    _namemapper.pyd extension. Cheetah can be used without compiled
    _namemapper.pyd extension. A pure-python replacement should work;
    ``Cheetah`` imports it automatically if the compiled extension is
    not available.

  - Stop testing at Travis CI.

  - Stop testing at AppVeyor.

3.2.7b1 (2021-07-25)
--------------------

Minor features:

  - Load from JSON file to searchlist (similar to loading from pickle).

Bug fixes:

  - Fix ``filetype`` for Python 2 in ``Template``.

Build, CI:

  - Build wheels for ``aarch64`` at Travis; publish them at PyPI.

Tests:

  - ``tox.ini``: Limit ``VIRTUALENV_PIP`` version for Python 3.4.

3.2.6.post1 (2021-02-22)
------------------------

Tests:

  - Add Python 3.9 to ``tox.ini``.

  - Refactor ``tox.ini``.

CI:

  - Run tests with Python 3.9 at Travis and AppVeyor.

  - Run tests for Python 3.4 with ``tox`` under Python 3.5.

3.2.6 (2020-10-01)
------------------

Bug fixes:

  - Fixed use of uninitialized variable in _namemapper.

3.2.5 (2020-05-16)
------------------

Build:

  - Install ``Cheetah3`` + ``markdown`` (used in ``Cheetah.Filters``)
    using ``pip install cheetah3[filters]`` (or ``cheetah3[markdown]``).

CI:

  - Run tests with Python 3.8 at Travis CI.

3.2.4 (2019-10-22)
------------------

Minor features:

  - Import from ``collections`` for Python 2,
    from ``collections.abc`` for Python 3.

Bug fixes:

  - Fixed infinite recursion in ``ImportManager`` on importing
    module ``_bootlocale`` inside ``open()``.

3.2.3 (2019-05-10)
------------------

Bug fixes:

  - Fixed infinite recursion in ``ImportManager`` on importing
    a builtin module.

Documentation:

  - The site https://cheetahtemplate.org/ is now served with HTTPS.
  - Updated docs regarding fixed tests.

Tests:

  - Removed ``unittest.main()`` calls from tests:
    ``python -m unittest discover -t Cheetah -s Cheetah/Tests -p '[A-Z]*.py'``
    does it.
  - Fixed ``cheetah test`` command.
  - Fixed script ``buildandrun``: copy test templates
    to the ``build/lib`` directory.

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
