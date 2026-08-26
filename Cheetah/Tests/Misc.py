import unittest

from Cheetah import SettingsManager


class SettingsManagerTests(unittest.TestCase):
    def test_mergeDictionaries(self):
        left = {'foo': 'bar', 'abc': {'a': 1, 'b': 2, 'c': (3,)}}
        right = {'xyz': (10, 9)}
        expect = {
            'xyz': (10, 9), 'foo': 'bar', 'abc': {'a': 1, 'c': (3,), 'b': 2}
        }
        result = SettingsManager.mergeNestedDictionaries(left, right)
        self.assertEqual(result, expect)

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
