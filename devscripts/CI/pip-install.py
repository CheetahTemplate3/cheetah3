#! /usr/bin/env python

import subprocess
import sys

subprocess.check_call([sys.executable, '-m', 'ensurepip'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + sys.argv[1:])
