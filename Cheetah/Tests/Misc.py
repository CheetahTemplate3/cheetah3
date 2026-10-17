# -*- coding: utf-8 -*-

import unittest

from Cheetah import SettingsManager
from Cheetah.CacheRegion import CacheRegion
from Cheetah.CacheStore import Error as CacheError, MemoryCacheStore
from Cheetah.SourceReader import Error, SourceReader


class SettingsManagerTests(unittest.TestCase):
    def test_mergeDictionaries(self):
        left = {'foo': 'bar', 'abc': {'a': 1, 'b': 2, 'c': (3,)}}
        right = {'xyz': (10, 9)}
        expect = {
            'xyz': (10, 9), 'foo': 'bar', 'abc': {'a': 1, 'c': (3,), 'b': 2}
        }
        result = SettingsManager.mergeNestedDictionaries(left, right)
        self.assertEqual(result, expect)


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
