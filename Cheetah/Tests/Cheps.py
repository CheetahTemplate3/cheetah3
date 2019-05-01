# import unittest

import Cheetah
import Cheetah.Parser
import Cheetah.Template


# class Chep_2_Conditionalized_Import_Behavior(unittest.TestCase):
class Chep_2_Conditionalized_Import_Behavior():
    def test_ModuleLevelImport(self):
        ''' Verify module level (traditional) import behavior '''
        pass

    def test_InlineImport(self):
        ''' Verify (new) inline import behavior works '''
        template = '''
            #def funky($s)
                #try
                    #import urllib
                #except ImportError
                    #pass
                #end try
                #return urllib.quote($s)
            #end def
        '''
        try:
            template = Cheetah.Template.Template.compile(template)
        except Cheetah.Parser.ParseError as ex:
            self.fail('Failed to properly generate code %s' % ex)
        template = template()
        rc = template.funky('abc def')
        assert rc == 'abc+def'

    def test_LegacyMode(self):
        ''' Verify disabling of CHEP #2 works '''
        pass
