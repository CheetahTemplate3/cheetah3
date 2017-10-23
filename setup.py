#!/usr/bin/env python
import os

try:
    os.remove('MANIFEST')  # to avoid those bloody out-of-date manifests!!
except Exception:
    pass

import SetupTools
import SetupConfig
configurations = (SetupConfig,)
SetupTools.run_setup(configurations)
