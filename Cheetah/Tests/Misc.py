# -*- coding: utf-8 -*-

import os
import shutil
import sys
import tempfile
import unittest

from Cheetah import SettingsManager
from Cheetah.CacheRegion import CacheRegion
from Cheetah.CacheStore import Error as CacheError, MemoryCacheStore
from Cheetah.SourceReader import Error, SourceReader


class SettingsManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmpDir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpDir)

    def test_mergeDictionaries(self):
        left = {'foo': 'bar', 'abc': {'a': 1, 'b': 2, 'c': (3,)}}
        right = {'xyz': (10, 9)}
        expect = {
            'xyz': (10, 9), 'foo': 'bar', 'abc': {'a': 1, 'c': (3,), 'b': 2}
        }
        result = SettingsManager.mergeNestedDictionaries(left, right)
        self.assertEqual(result, expect)

    def test_read_settings_from_python_file(self):
        manager = SettingsManager.SettingsManager()
        original_path = sys.path[:]
        directory = self.tmpDir
        path = os.path.join(directory, 'settings.py')
        with open(path, 'wb') as source:
            source.write(b'# coding: utf-8\n'
                         b'value = 42\n_hidden = 1\n'
                         b'text = u"caf\xc3\xa9"\n'
                         b'def get_value():\n    return value\n')
        settings = manager.readSettingsFromPySrcFile(path)
        self.assertEqual(settings['value'], 42)
        self.assertEqual(settings['text'], u'caf\xe9')
        self.assertEqual(settings['get_value'](), 42)
        self.assertNotIn('_hidden', settings)
        self.assertEqual(manager.settings(), {})
        self.assertEqual(sys.path, original_path)
        original_cwd = os.getcwd()
        try:
            os.chdir(directory)
            settings = manager.readSettingsFromPySrcFile('settings.py')
            self.assertEqual(settings['value'], 42)
        finally:
            os.chdir(original_cwd)
        self.assertEqual(sys.path, original_path)
        os.remove(path)

    def test_import_settings_merges_selected_dictionary(self):
        directory = self.tmpDir
        path = os.path.join(directory, 'settings.py')
        with open(path, 'w') as source:
            source.write('value = 42\n'
                         'selected = {"nested": {"new": 2}, "value": 3}\n')
        manager = SettingsManager.SettingsManager()
        manager.updateSettingsFromConfigStr('importSettings = ' + path)
        self.assertEqual(manager.setting('value'), 42)
        manager = SettingsManager.SettingsManager()
        manager.updateSettingsFromConfigStr(
            'value = 1\nnested = python:{"old": 1}\n'
            'importSettings = ' + path + '; selected')
        self.assertEqual(manager.setting('value'), 3)
        self.assertEqual(manager.setting('nested'), {'old': 1, 'new': 2})

    def test_python_settings_can_import_sibling(self):
        original_path = sys.path[:]
        directory = self.tmpDir
        helper = os.path.join(directory, 'cheetah_settings_test_helper.py')
        with open(helper, 'w') as source:
            source.write('value = 42\n')
        path = os.path.join(directory, 'settings.py')
        with open(path, 'w') as source:
            source.write('from cheetah_settings_test_helper import value\n')
        try:
            settings = SettingsManager.SettingsManager().readSettingsFromPySrcFile(path)  # noqa: E501
            self.assertEqual(settings['value'], 42)
            self.assertEqual(sys.path, original_path)
        finally:
            sys.modules.pop('cheetah_settings_test_helper', None)

    def test_python_settings_errors_restore_import_path(self):
        manager = SettingsManager.SettingsManager()
        original_path = sys.path[:]
        directory = self.tmpDir
        path = os.path.join(directory, 'settings.py')
        self.assertRaises(IOError, manager.readSettingsFromPySrcFile, path)
        for source_text, error in [('invalid syntax !', SyntaxError),
                                   ('raise ValueError("failed")', ValueError)]:
            with open(path, 'w') as source:
                source.write(source_text)
            self.assertRaises(error, manager.readSettingsFromPySrcFile, path)
            self.assertEqual(sys.path, original_path)
            os.remove(path)


class SourceReaderTests(unittest.TestCase):
    def test_ungetc(self):
        reader = SourceReader('abc')
        self.assertEqual(reader.getc(), 'a')
        reader.ungetc()
        self.assertEqual(reader.getc(), 'a')

    def test_ungetc_replaces_the_character(self):
        reader = SourceReader('abc')
        reader.getc()
        reader.ungetc('x')
        self.assertEqual(reader.getc(), 'x')
        self.assertEqual(reader.getc(), 'b')

    def test_ungetc_at_the_start(self):
        reader = SourceReader('abc')
        self.assertRaises(Error, reader.ungetc)

    def test_stringIsNumber(self):
        self.assertTrue(SettingsManager.stringIsNumber('42'))
        self.assertTrue(SettingsManager.stringIsNumber(' -1.5 '))
        self.assertFalse(SettingsManager.stringIsNumber('x'))
        self.assertFalse(SettingsManager.stringIsNumber(''))
        self.assertFalse(SettingsManager.stringIsNumber('   '))

    def test_empty_setting_value(self):
        manager = SettingsManager.SettingsManager()
        manager.updateSettingsFromConfigStr('foo =')
        self.assertEqual(manager.setting('foo'), '')


class MemoryCacheStoreTests(unittest.TestCase):
    def test_add(self):
        store = MemoryCacheStore()
        store.add('k', 'v')
        self.assertEqual(store.get('k'), 'v')
        self.assertRaises(CacheError, store.add, 'k', 'w')

    def test_replace_needs_the_key(self):
        store = MemoryCacheStore()
        self.assertRaises(CacheError, store.replace, 'k', 'v')

    def test_replace(self):
        store = MemoryCacheStore()
        store.set('k', 'v')
        store.replace('k', 'w')
        self.assertEqual(store.get('k'), 'w')


class CacheRegionTests(unittest.TestCase):
    def test_non_ascii_vary_by(self):
        region = CacheRegion('r')
        item = region.getCacheItem(u'M\xfcnchen')
        self.assertIs(region.getCacheItem(u'M\xfcnchen'), item)
        self.assertIsNot(region.getCacheItem(u'Berlin'), item)

    def test_key_is_stable_for_ascii(self):
        region = CacheRegion('r')
        self.assertIs(region.getCacheItem('x'), region.getCacheItem(u'x'))
