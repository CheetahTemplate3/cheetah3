#!/usr/bin/env python
# $Id: Template.py,v 1.11 2006/01/29 04:35:50 tavis_rudd Exp $
"""Tests of the Template class API

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@damnsimple.com>,
Version: $Revision: 1.11 $
Start Date: 2001/10/01
Last Revision Date: $Date: 2006/01/29 04:35:50 $
"""
__author__ = "Tavis Rudd <tavis@damnsimple.com>"
__revision__ = "$Revision: 1.11 $"[11:-2]


##################################################
## DEPENDENCIES ##

import sys
import types
import os
import os.path
import tempfile
import shutil
import unittest_local_copy as unittest
from Cheetah.Template import Template

##################################################
## CONSTANTS & GLOBALS ##

try:
    True,False
except NameError:
    True, False = (1==1),(1==0)

##################################################
## TEST DATA FOR USE IN THE TEMPLATES ##

##################################################
## TEST BASE CLASSES

class TemplateTest(unittest.TestCase):
    pass

##################################################
## TEST CASE CLASSES

class ClassMethods_compile(TemplateTest):
    """I am using the same Cheetah source for each test to root out clashes
    caused by the compile caching in Template.compile().
    """
    
    def test_basicUsage(self):
        klass = Template.compile(source='$foo')
        t = klass(namespaces={'foo':1234})
        assert str(t)=='1234'

    def test_baseclassArg(self):
        klass = Template.compile(source='$foo', baseclass=dict)
        t = klass({'foo':1234})
        assert str(t)=='1234'

        klass2 = Template.compile(source='$foo', baseclass=klass)
        t = klass2({'foo':1234})
        assert str(t)=='1234'

        klass3 = Template.compile(source='#implements dummy\n$bar', baseclass=klass2)
        t = klass3({'foo':1234})
        assert str(t)=='1234'

        klass4 = Template.compile(source='$foo', baseclass='dict')
        t = klass4({'foo':1234})
        assert str(t)=='1234'

    def test_moduleFileCaching(self):
        tmpDir = tempfile.mkdtemp()
        try:
            #print tmpDir
            assert os.path.exists(tmpDir)
            klass = Template.compile(source='$foo',
                                     cacheModuleFilesForTracebacks=True,
                                     cacheDirForModuleFiles=tmpDir)
            mod = sys.modules[klass.__module__]
            #print mod.__file__
            assert os.path.exists(mod.__file__)
            assert os.path.dirname(mod.__file__)==tmpDir
        finally:
            shutil.rmtree(tmpDir, True)

    def test_classNameArg(self):
        klass = Template.compile(source='$foo', className='foo123')
        assert klass.__name__=='foo123'
        t = klass(namespaces={'foo':1234})
        assert str(t)=='1234'

    def test_moduleNameArg(self):
        klass = Template.compile(source='$foo', moduleName='foo99')
        mod = sys.modules['foo99']
        assert klass.__name__=='foo99'
        t = klass(namespaces={'foo':1234})
        assert str(t)=='1234'


        klass = Template.compile(source='$foo',
                                 moduleName='foo1',
                                 className='foo2')
        mod = sys.modules['foo1']
        assert klass.__name__=='foo2'
        t = klass(namespaces={'foo':1234})
        assert str(t)=='1234'


    def test_mainMethodNameArg(self):
        klass = Template.compile(source='$foo',
                                 className='foo123',
                                 mainMethodName='testMeth')
        assert klass.__name__=='foo123'
        t = klass(namespaces={'foo':1234})
        #print t.generatedClassCode()
        assert str(t)=='1234'
        assert t.testMeth()=='1234'

        klass = Template.compile(source='$foo',
                                 moduleName='fooXXX',                                 
                                 className='foo123',
                                 mainMethodName='testMeth',
                                 baseclass=dict)
        assert klass.__name__=='foo123'
        t = klass({'foo':1234})
        #print t.generatedClassCode()
        assert str(t)=='1234'
        assert t.testMeth()=='1234'



    def test_moduleGlobalsArg(self):
        klass = Template.compile(source='$foo',
                                 moduleGlobals={'foo':1234})
        t = klass()
        assert str(t)=='1234'

        klass2 = Template.compile(source='$foo', baseclass='Test1',
                                  moduleGlobals={'Test1':dict})
        t = klass2({'foo':1234})
        assert str(t)=='1234'

        klass3 = Template.compile(source='$foo', baseclass='Test1',
                                  moduleGlobals={'Test1':dict, 'foo':1234})
        t = klass3()
        assert str(t)=='1234'


    def test_keepRefToGeneratedCodeArg(self):
        klass = Template.compile(source='$foo',
                                 className='unique58',
                                 keepRefToGeneratedCode=False)
        t = klass(namespaces={'foo':1234})
        assert str(t)=='1234'
        assert not t.generatedClassCode()


        klass2 = Template.compile(source='$foo',
                                 className='unique58',
                                 keepRefToGeneratedCode=True)
        t = klass2(namespaces={'foo':1234})
        assert str(t)=='1234'
        assert t.generatedClassCode()


    def test_compilationCache(self):
        klass = Template.compile(source='$foo',
                                 className='unique111',
                                 cacheCompilationResults=False)
        t = klass(namespaces={'foo':1234})
        assert str(t)=='1234'
        assert not klass._CHEETAH_isInCompilationCache


        # this time it will place it in the cache
        klass = Template.compile(source='$foo',
                                 className='unique111',
                                 cacheCompilationResults=True)
        t = klass(namespaces={'foo':1234})
        assert str(t)=='1234'
        assert klass._CHEETAH_isInCompilationCache

        # by default it will be in the cache
        klass = Template.compile(source='$foo',
                                 className='unique999099')
        t = klass(namespaces={'foo':1234})
        assert str(t)=='1234'
        assert klass._CHEETAH_isInCompilationCache


class ClassMethods_subclass(TemplateTest):

    def test_basicUsage(self):
        klass = Template.compile(source='$foo', baseclass=dict)
        t = klass({'foo':1234})
        assert str(t)=='1234'

        klass2 = klass.subclass(source='$foo')
        t = klass2({'foo':1234})
        assert str(t)=='1234'

        klass3 = klass2.subclass(source='#implements dummy\n$bar')
        t = klass3({'foo':1234})
        assert str(t)=='1234'
        


##################################################
## if run from the command line ##
        
if __name__ == '__main__':
    unittest.main()
