News
====

Development (master)
--------------------

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
