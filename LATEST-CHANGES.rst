Minor features:

  - Protect ``import cgi`` in preparation to Python 3.13.

Tests:

  - Run tests with Python 3.12.

CI:

  - GHActions: Ensure ``pip`` only if needed

    This is to work around a problem in conda with Python 3.7 -
    it brings in wrong version of ``setuptools`` incompatible with Python 3.7.

