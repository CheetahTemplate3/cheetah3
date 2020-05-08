REM Downgrade pip/pkg_resources/setuptools to work around a bug in tox
REM that upgrades packages too eagerly and installs incompatible versions.

REM Cleanup
del /q /s .tox\py34-w32\lib\site-packages\pip
del /q /s .tox\py34-w32\lib\site-packages\pkg_resources
del /q /s .tox\py34-w32\lib\site-packages\setuptools

REM Install pkg_resources/setuptools
python -m zipfile -e devscripts\CI\setuptools-43.0.0.zip .
cd setuptools-43.0.0
python bootstrap.py
python setup.py install
cd ..
python -c "import setuptools; print(setuptools.__version__)"

REM Install pip
python -m tarfile -e devscripts\CI\pip-19.1.1.tar.gz
cd pip-19.1.1.
python bootstrap.py
python setup.py install
cd ..
pip --version

REM Use fixed pip to install dependencies
pip install %*
