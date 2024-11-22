Bug fixes:

  - Fixed ``ImportHooks``: it must raise ``ModuleNotFoundError``
    instead of ``ImportError``.

  - Fixed absolute import in ``ImportHooks`` under Python 3.

  - Use ``cache_from_source`` in ``ImportManager`` to find out
    ``.pyc``/``.pyo`` byte-code files.

  - Fixed unmarshalling ``.pyc``/``.pyo`` byte-code files
    in ``ImportManager``.

  - Fixed ``Template.webInput``: Use ``urllib.parse.parse_qs``
    instead of ``cgi.FieldStorage``; Python 3.13 dropped ``cgi``.

  - Fixed ``_namemapper.c``: Silent an inadvertent ``TypeError`` exception
    in ``PyMapping_HasKeyString`` under Python 3.13+
    caused by ``_namemapper`` looking up a key in a non-dictionary.

  - Fixed ``_namemapper.c``: Silence ``IndexError`` when testing
    ``name[attr]``. Some objects like ``re.MatchObject`` implement both
    attribute access and index access. This confuses ``NameMapper`` because
    it expects ``name[attr]`` to raise ``TypeError`` for objects that don't
    implement mapping protocol.

  - Fixed mapping test in ``NameMapper.py``:
    Python 3.13 brough a new mapping type ``FrameLocalsProxy``.

  - Fixed another ``RecursionError`` in ``ImportHooks`` under PyPy3.

Tests:

  - tox: Run tests under Python 3.13.

CI:

  - CI(GHActions): Switch to ``setup-miniconda``.

  - CI(GHActions): Run tests under Python 3.13.

Build/release:

  - Rename sdist to lowercase; different build tools produce different case.
    This is important because stupid PyPI doesn't ignore sdists
    in different cases but also doesn't allow uploading.
    So we use single case, all lower. Also see PEP 625.
