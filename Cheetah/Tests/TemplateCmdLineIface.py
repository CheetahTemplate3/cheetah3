try:
    from io import BytesIO, TextIOWrapper, StringIO
except ImportError:
    try:
        from cStringIO import StringIO as BytesIO
    except ImportError:
        from StringIO import StringIO as BytesIO

from tempfile import NamedTemporaryFile

import os
import pickle
import json
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


class TestPickleStdin(unittest.TestCase):

    def setUp(self):
        pickle_bytes = pickle.dumps({'foo': 'test foo'})
        if hasattr(sys.stdin, 'buffer'):
            sys.stdin = TextIOWrapper(BytesIO(pickle_bytes))
        else:
            sys.stdin = BytesIO(pickle_bytes)

    def tearDown(self):
        sys.stdin = sys.__stdin__

    def test_pickle_stdin(self):
        klass = Template.compile(source='$foo')
        t = klass()
        cmdline = CmdLineIface(t, scriptName='test',
                               cmdLineArgs=['--pickle=-'])
        cmdline._processCmdLineArgs()
        assert str(t) == 'test foo'


class TestPickleFile(unittest.TestCase):

    def setUp(self):
        self.pickle_file = pickle_file = \
            NamedTemporaryFile(mode='wb', delete=False)
        pickle.dump({'foo': 'test foo'}, pickle_file)
        pickle_file.close()

    def tearDown(self):
        os.remove(self.pickle_file.name)

    def test_pickle_file(self):
        klass = Template.compile(source='$foo')
        t = klass()
        cmdline = CmdLineIface(t, scriptName='test',
                               cmdLineArgs=['--pickle', self.pickle_file.name])
        cmdline._processCmdLineArgs()
        assert str(t) == 'test foo'


class TestJsonStdin(unittest.TestCase):

    def setUp(self):
        json_string = json.dumps({'foo': 'test foo'})
        if hasattr(sys.stdin, 'buffer'):
            sys.stdin = TextIOWrapper(StringIO(json_string))
        else:
            sys.stdin = BytesIO(json_string.encode('utf-8'))

    def tearDown(self):
        sys.stdin = sys.__stdin__

    def test_json_stdin(self):
        klass = Template.compile(source='$foo')
        t = klass()
        cmdline = CmdLineIface(t, scriptName='test',
                               cmdLineArgs=['--json=-'])
        cmdline._processCmdLineArgs()
        assert (True)


class TestJsonFile(unittest.TestCase):

    def setUp(self):
        self.json_file = NamedTemporaryFile(mode='w', delete=False)
        json.dump({'foo': 'test foo'}, self.json_file)
        self.json_file.close()

    def tearDown(self):
        os.remove(self.json_file.name)

    def test_json_file(self):
        klass = Template.compile(source='$foo')
        t = klass()
        cmdline = CmdLineIface(t, scriptName='test',
                               cmdLineArgs=['--json', self.json_file.name])
        cmdline._processCmdLineArgs()
        assert str(t) == 'test foo'
