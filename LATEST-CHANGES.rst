Bug fixes:

  - Fixed ``ImportHooks`` under PyPy3.

Tests:

  - Run tests with PyPy3.

CI:

  - Use ``conda`` to install older Pythons

    Ubuntu >= 22 and ``setup-python`` dropped Pythons < 3.7.
    Use ``s-weigand/setup-conda`` instead of ``setup-python``.
