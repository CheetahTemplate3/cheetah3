#!/usr/bin/env python
# $Id: NameMapper.py,v 1.4 2001/12/19 02:10:25 tavis_rudd Exp $
"""NameMapper Tests

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>,
Version: $Revision: 1.4 $
Start Date: 2001/10/01
Last Revision Date: $Date: 2001/12/19 02:10:25 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__revision__ = "$Revision: 1.4 $"[11:-2]


##################################################
## DEPENDENCIES ##

import sys
import types
import os
import os.path
import unittest_local_copy as unittest

# We exist in src/Tests (uninstalled) or Cheetah/Tests (installed)
# Here we fix up sys.path to make sure we get the Cheetah we
# belong to and not some other Cheetah.

newPath = os.path.abspath(os.path.join(os.pardir, os.pardir))
sys.path.insert(1, newPath)

if os.path.exists(os.path.join(newPath, 'src')):
    from src.NameMapper import NotFound, valueForName, valueFromSearchList
elif os.path.exists(os.path.join(newPath, 'Cheetah')):
    from Cheetah.NameMapper import NotFound, valueForName, valueFromSearchList
else:
    raise Exception, "Not sure where to find Cheetah. I do not see src/ or" + \
	  " Cheetah/ two directories up."

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)


##################################################
## TEST DATA FOR USE IN THE TEMPLATES ##

class DummyClass:
    classVar1 = 123
    _classVar2 = 321

    def __init__(self):
        self.instanceVar1 = 123
        self._instanceVar2 = 321
        
    def __str__(self):
        return 'object'

    def meth(self, arg="arff"):
        return str(arg)

    def meth1(self, arg="doo"):
        return arg

    def meth2(self, arg1="a1", arg2="a2"):
        raise ValueError

    def meth3(self):
        """Tests a bug that Jeff Johnson reported on Oct 1, 2001"""
        
        x = 'A string'
        try:
            for i in [1,2,3,4]:
                if x == 2:	
                    pass
                
                if x == 'xx':
                    pass
            return x
        except:
            raise


def dummyFunc(arg="Scooby"):
    return arg

def funcThatRaises():
    raise ValueError

testNamespace = {
    'aStr':'blarg',
    'anInt':1,
    'aFloat':1.5,
    'aDict': {'one':'item1',
              'two':'item2',
              'nestedDict':{'one':'nestedItem1',
                            'two':'nestedItem2',
                            'funcThatRaises':funcThatRaises,
                            'aClass': DummyClass,
                            },
              'nestedFunc':dummyFunc,
              },
    'aClass': DummyClass,    
    'aFunc': dummyFunc,
    'anObj': DummyClass(),
    'aMeth': DummyClass().meth1,
    'none' : None,  
    'emptyString':'',
    'funcThatRaises':funcThatRaises,
    }
autoCallResults = {'aFunc':'Scooby',
                   'aMeth':'doo',
                   }

nestingResults =  {'anObj.meth1':'doo',
                   'aDict.one':'item1',
                   'aDict.nestedDict':testNamespace['aDict']['nestedDict'],
                   'aDict.nestedDict.one':'nestedItem1',
                   'aDict.nestedDict.aClass':DummyClass,
                   'aDict.nestedFunc':'Scooby',
                   'aClass.classVar1':123,
                   'aClass.classVar2':321,
                   'anObj.instanceVar1':123,
                   'anObj.instanceVar2':321,
                   'anObj.meth3':'A string',
                   }

##################################################
## TEST BASE CLASSES

class NameMapperTest(unittest.TestCase):
    failureException = (NotFound,AssertionError)
    _testNamespace = testNamespace
    
    def namespace(self):
        return self._testNamespace

    def VFN(self, name, autocall=True):
        return valueForName(self.namespace(), name, autocall)

    def VFS(self, searchList, name, autocall=True):
        return valueFromSearchList(searchList, name, autocall)

    # alias to be overriden later
    get = VFN

    def check(self, name):
        got = self.get(name)
        if autoCallResults.has_key(name):
            expected = autoCallResults[name]
        elif self.namespace().has_key(name):
            expected = self.namespace()[name]
        else:
            expected = nestingResults[name]
        assert got == expected
        

##################################################
## TEST CASE CLASSES

class VFN(NameMapperTest):

    def test1(self):
        """string in dict lookup"""
        self.check('aStr')

    def test2(self):
        """string in dict lookup in a loop"""
        for i in range(10):
            self.check('aStr')
            
    def test3(self):
        """int in dict lookup"""
        self.check('anInt')

    def test4(self):
        """int in dict lookup in a loop"""
        for i in range(10):
            self.check('anInt')

    def test5(self):
        """float in dict lookup"""
        self.check('aFloat')

    def test6(self):
        """float in dict lookup in a loop"""
        for i in range(10):
            self.check('aFloat')
          
    def test7(self):
        """class in dict lookup"""
        self.check('aClass')

    def test8(self):
        """class in dict lookup in a loop"""
        for i in range(10):
            self.check('aClass')
            
    def test9(self):
        """aFunc in dict lookup"""
        self.check('aFunc')

    def test10(self):
        """aFunc in dict lookup in a loop"""
        for i in range(10):
            self.check('aFunc')

    def test11(self):
        """aMeth in dict lookup"""
        self.check('aMeth')

    def test12(self):
        """aMeth in dict lookup in a loop"""
        for i in range(10):
            self.check('aMeth')

    def test13(self):
        """aMeth in dict lookup"""
        self.check('aMeth')

    def test14(self):
        """aMeth in dict lookup in a loop"""
        for i in range(10):
            self.check('aMeth')

    def test15(self):
        """anObj in dict lookup"""
        self.check('anObj')

    def test16(self):
        """anObj in dict lookup in a loop"""
        for i in range(10):
            self.check('anObj')

    def test17(self):
        """aDict in dict lookup"""
        self.check('aDict')

    def test18(self):
        """aDict in dict lookup in a loop"""
        for i in range(10):
            self.check('aDict')

    def test17(self):
        """aDict in dict lookup"""
        self.check('aDict')

    def test18(self):
        """aDict in dict lookup in a loop"""
        for i in range(10):
            self.check('aDict')

    def test19(self):
        """aClass.classVar1 in dict lookup"""
        self.check('aClass.classVar1')

    def test20(self):
        """aClass.classVar1 in dict lookup in a loop"""
        for i in range(10):
            self.check('aClass.classVar1')

    def test21(self):
        
        """aClass._classVar2 in dict lookup"""
        self.check('aClass.classVar2')

    def test22(self):
        """aClass._classVar2 in dict lookup in a loop"""
        for i in range(10):
            self.check('aClass.classVar2')

    def test23(self):
        """anObj.instanceVar1 in dict lookup"""
        self.check('anObj.instanceVar1')

    def test24(self):
        """anObj.instanceVar1 in dict lookup in a loop"""
        for i in range(10):
            self.check('anObj.instanceVar1')

    def test25(self):
        
        """anObj._instanceVar2 in dict lookup"""
        self.check('anObj.instanceVar2')

    def test26(self):
        """anObj._instanceVar2 in dict lookup in a loop"""
        for i in range(10):
            self.check('anObj.instanceVar2')

    def test27(self):
        """anObj.meth1 in dict lookup"""
        self.check('anObj.meth1')

    def test28(self):
        """anObj.meth1 in dict lookup in a loop"""
        for i in range(10):
            self.check('anObj.meth1')

    def test29(self):
        """aDict.one in dict lookup"""
        self.check('aDict.one')

    def test30(self):
        """aDict.one in dict lookup in a loop"""
        for i in range(10):
            self.check('aDict.one')

    def test31(self):
        """aDict.nestedDict in dict lookup"""
        self.check('aDict.nestedDict')

    def test32(self):
        """aDict.nestedDict in dict lookup in a loop"""
        for i in range(10):
            self.check('aDict.nestedDict')
            
    def test33(self):
        """aDict.nestedDict.one in dict lookup"""
        self.check('aDict.nestedDict.one')

    def test34(self):
        """aDict.nestedDict.one in dict lookup in a loop"""
        for i in range(10):
            self.check('aDict.nestedDict.one')
            
    def test35(self):
        """aDict.nestedFunc in dict lookup"""
        self.check('aDict.nestedFunc')

    def test36(self):
        """aDict.nestedFunc in dict lookup in a loop"""
        for i in range(10):
            self.check('aDict.nestedFunc')

    def test37(self):
        """aDict.nestedFunc in dict lookup - without autocalling"""
        assert self.get('aDict.nestedFunc', False) == dummyFunc

    def test38(self):
        """aDict.nestedFunc in dict lookup in a loop - without autocalling"""
        for i in range(10):
            assert self.get('aDict.nestedFunc', False) == dummyFunc

    def test39(self):
        """aMeth in dict lookup - without autocalling"""
        assert self.get('aMeth', False) == self.namespace()['aMeth']

    def test40(self):
        """aMeth in dict lookup in a loop - without autocalling"""
        for i in range(10):
            assert self.get('aMeth', False) == self.namespace()['aMeth']

    def test41(self):
        """anObj.meth3 in dict lookup"""
        self.check('anObj.meth3')

    def test42(self):
        """aMeth in dict lookup in a loop"""
        for i in range(10):
            self.check('anObj.meth3')

    def test43(self):
        """NotFound test"""

        def test(self=self):
            self.get('anObj.methX')    
        self.assertRaises(NotFound,test)
        
    def test44(self):
        """NotFound test in a loop"""
        def test(self=self):
            self.get('anObj.methX')    

        for i in range(10):
            self.assertRaises(NotFound,test)
            
    def test45(self):
        """Other exception from meth test"""

        def test(self=self):
            self.get('anObj.meth2')    
        self.assertRaises(ValueError, test)
        
    def test46(self):
        """Other exception from meth test in a loop"""
        def test(self=self):
            self.get('anObj.meth2')    

        for i in range(10):
            self.assertRaises(ValueError,test)

    def test47(self):
        """None in dict lookup"""
        self.check('none')

    def test48(self):
        """None in dict lookup in a loop"""
        for i in range(10):
            self.check('none')
            
    def test49(self):
        """EmptyString in dict lookup"""
        self.check('emptyString')

    def test50(self):
        """EmptyString in dict lookup in a loop"""
        for i in range(10):
            self.check('emptyString')

    def test51(self):
        """Other exception from func test"""

        def test(self=self):
            self.get('funcThatRaises')    
        self.assertRaises(ValueError, test)
        
    def test52(self):
        """Other exception from func test in a loop"""
        def test(self=self):
            self.get('funcThatRaises')    

        for i in range(10):
            self.assertRaises(ValueError,test)


    def test53(self):
        """Other exception from func test"""

        def test(self=self):
            self.get('aDict.nestedDict.funcThatRaises')    
        self.assertRaises(ValueError, test)
        
    def test54(self):
        """Other exception from func test in a loop"""
        def test(self=self):
            self.get('aDict.nestedDict.funcThatRaises')    

        for i in range(10):
            self.assertRaises(ValueError,test)

    def test55(self):
        """aDict.nestedDict.aClass in dict lookup"""
        self.check('aDict.nestedDict.aClass')

    def test56(self):
        """aDict.nestedDict.aClass in dict lookup in a loop"""
        for i in range(10):
            self.check('aDict.nestedDict.aClass')

    def test57(self):
        """aDict.nestedDict.aClass in dict lookup - without autocalling"""
        assert self.get('aDict.nestedDict.aClass', False) == DummyClass

    def test58(self):
        """aDict.nestedDict.aClass in dict lookup in a loop - without autocalling"""
        for i in range(10):
            assert self.get('aDict.nestedDict.aClass', False) == DummyClass

    def test59(self):
        """Other exception from func test -- but without autocalling shouldn't raise"""

        self.get('aDict.nestedDict.funcThatRaises', False)    
        
    def test60(self):
        """Other exception from func test in a loop -- but without autocalling shouldn't raise"""

        for i in range(10):
            self.get('aDict.nestedDict.funcThatRaises', False)    

class VFS(VFN):
    def searchList(self):
        return [self.namespace()]
    
    def get(self, name, autocall=True):
        return self.VFS(self.searchList(), name, autocall)
        
class VFS_2namespaces(VFS):
    def searchList(self):
        return [self.namespace(),{'dummy':1234}]
    
class VFS_3namespaces(VFS):
    def searchList(self):
        return [{'dummy':1234}, self.namespace(),{'dummy':1234}]

class VFS_4namespaces(VFS):
    def searchList(self):
        class Test:
            pass
        return [Test(),{'dummy':1234}, self.namespace(),{'dummy':1234}]

##################################################
## if run from the command line ##
        
if __name__ == '__main__':
    unittest.main()
