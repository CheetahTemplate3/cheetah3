#!/usr/bin/env python

import sys

import Cheetah.ImportHooks
Cheetah.ImportHooks.install()

import abc
import importlib
if sys.version_info > (3, 4):
    import importlib.abc
if sys.version_info > (3, 11):
    import importlib.resources.abc
