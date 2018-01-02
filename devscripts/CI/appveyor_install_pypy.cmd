REM curl -fsSL -o pypy2.zip https://bitbucket.org/pypy/pypy/downloads/pypy2-v5.10.0-win32.zip
REM 7z x pypy2.zip -oc:\

REM Borrowed from https://github.com/pytest-dev/pytest/blob/master/scripts/install-pypy.bat
REM install pypy using choco
REM redirect to a file because choco install python.pypy is too noisy. If the command fails, write output to console
choco install python.pypy > pypy-inst.log 2>&1 || (type pypy-inst.log & exit /b 1)
