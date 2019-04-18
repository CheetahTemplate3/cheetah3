#!/usr/bin/env python

import os
import sys
import unittest

from Cheetah.Template import Template
from Cheetah.TemplateCmdLineIface import CmdLineIface


class TestHelp(unittest.TestCase):
    def setUp(self):
        self.NULL = NULL = open(os.devnull, 'w')
        sys.stdout = NULL

    def tearDown(self):
        self.NULL.close()
        sys.stdout = sys.__stdout__

    def test_help(self):
        klass = Template.compile(source='$foo')
        t = klass()
        cmdline = CmdLineIface(t, scriptName='test', cmdLineArgs=['-h'])
        self.assertRaises(SystemExit, cmdline._processCmdLineArgs)


class TestEnv(unittest.TestCase):
    def setUp(self):
        os.environ['foo'] = 'test foo'

    def tearDown(self):
        del os.environ['foo']

    def test_env(self):
        klass = Template.compile(source='$foo')
        t = klass()
        cmdline = CmdLineIface(t, scriptName='test', cmdLineArgs=['--env'])
        cmdline._processCmdLineArgs()
        assert str(t) == 'test foo'


if __name__ == '__main__':
    unittest.main()
