import unittest

from Cheetah import SettingsManager
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
