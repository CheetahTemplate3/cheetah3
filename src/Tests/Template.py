#!/usr/bin/env python
# $Id: Template.py,v 1.10 2006/01/29 02:49:52 tavis_rudd Exp $
"""Tests of the Template class API

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@damnsimple.com>,
Version: $Revision: 1.10 $
Start Date: 2001/10/01
Last Revision Date: $Date: 2006/01/29 02:49:52 $
"""
__author__ = "Tavis Rudd <tavis@damnsimple.com>"
__revision__ = "$Revision: 1.10 $"[11:-2]


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


    def test_moduleFileCaching(self):
        tmpDir = tempfile.mkdtemp()
        try:
            #print tmpDir
            assert os.path.exists(tmpDir)
            klass = Template.compile(source='$foo',
                                     cacheModuleFilesForTracebacks=True,
                                     cacheDirForModuleFiles=tmpDir
                                     )
            mod = sys.modules[klass.__module__]
            #print mod.__file__
            assert os.path.exists(mod.__file__)
        finally:
            shutil.rmtree(tmpDir, True)

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
