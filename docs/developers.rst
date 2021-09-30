Contributing to Cheetah
=======================

Cheetah is the work of many volunteers. If you use Cheetah, share your
experiences, tricks, customizations, and frustrations. Please visit
https://github.com/CheetahTemplate3/cheetah3 and file bug reports, feature
requests or pull requests.


Getting the Code
----------------
The Cheetah source code is stored in a central **Git** repository
hosted primarily by `GitHub <http://github.com>`_. The primary Git
repository can be found `here <http://github.com/CheetahTemplate3/cheetah3>`_.


Development Process
-------------------
The typical development workflow for Cheetah revolves around
two primary branches **maint** and **next**. The **next** branch is where development
planned for the next release of Cheetah is. The **maint** branch
on the otherhand is where backported fixes and patches will be applied for
the current release of Cheetah will go, it's common for a patch
to be applied to maint and next at the same time.

Anyone and everyone is encouraged to submit patches at any time, but as far
as bugs or feature requests go, we try to file those *first* in the `Cheetah3 Bug Tracker <https://github.com/CheetahTemplate3/cheetah3/issues>`_
and then they can be organized into particular releases as is necessary.

In addition to the bug tracker, Cheetah uses Github Actions
for automating builds and test runs (see: `Github Actions for Cheetah
<https://github.com/CheetahTemplate3/cheetah3/actions>`_).

Prior to the tarballing of a release, **all** tests must be passing before the
**next** branch is merged down to the Git **master** branch where the release
tarball will actually be created from.


Filing Bugs
-----------
No software is perfect, and unfortunately no bug report is either. If you've
found yourself faced with a bug in Cheetah, or just have a good idea for a
new feature, we kindly ask that you create an issue in the `Cheetah3 Bug Tracker <https://github.com/CheetahTemplate3/cheetah3/issues>`_.

Some tips for filing a *useful* bug report, try to include the following:

* A description of what you were trying to do, and what happened (i.e. reproduction steps), the more code you can include the better.
* Any and all tracebacks or compiler errors
* The version of Cheetah you're using
* The version of Python you're using
* The operating system you're running Cheetah on
* Any other pieces of information you might think are relevant

