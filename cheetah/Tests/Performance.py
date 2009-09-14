#!/usr/bin/env python

import Cheetah.NameMapper 
import Cheetah.Template
from Cheetah.Utils import statprof

import os
import sys
import unittest

from test import pystone
import time

# This can be turned on with the `--debug` flag when running the test
# and will cause the tests to all just dump out how long they took
# insteasd of asserting on duration
DEBUG = False

# TOLERANCE in Pystones
kPS = 1000
TOLERANCE = 0.5*kPS 

class DurationError(AssertionError):
    pass

_pystone_calibration_mark = None
def _pystone_calibration():
    global _pystone_calibration_mark
    if not _pystone_calibration_mark:
        _pystone_calibration_mark = pystone.pystones(loops=pystone.LOOPS)
    return _pystone_calibration_mark

def perftest(max_num_pystones, current_pystone=None):
    '''
        Performance test decorator based off the 'timedtest' 
        decorator found in this Active State recipe:
            http://code.activestate.com/recipes/440700/
    '''
    if not isinstance(max_num_pystones, float):
        max_num_pystones = float(max_num_pystones)

    if not current_pystone:
        current_pystone = _pystone_calibration()

    def _test(function):
        def wrapper(*args, **kw):
            start_time = time.time()
            try:
                return function(*args, **kw)
            finally:
                total_time = time.time() - start_time
                if total_time == 0:
                    pystone_total_time = 0
                else:
                    pystone_rate = current_pystone[0] / current_pystone[1]
                    pystone_total_time = total_time / pystone_rate
                global DEBUG
                if DEBUG:
                    print 'The test "%s" took: %s pystones' % (function.func_name,
                        pystone_total_time)
                else:
                    if pystone_total_time > (max_num_pystones + TOLERANCE):
                        raise DurationError((('Test too long (%.2f Ps, '
                                        'need at most %.2f Ps)')
                                        % (pystone_total_time,
                                            max_num_pystones)))
        return wrapper
    return _test


class DynamicTemplatePerformanceTest(unittest.TestCase):
    loops = 10
    #@perftest(1200)
    def test_BasicDynamic(self):
        template = '''
            #def foo(arg1, arg2)
                #pass
            #end def
        '''
        for i in xrange(self.loops):
            klass = Cheetah.Template.Template.compile(template)
            assert klass
    test_BasicDynamic = perftest(1200)(test_BasicDynamic)

class PerformanceTest(unittest.TestCase):
    iterations = 1000000
    display = False
    def setUp(self):
        super(PerformanceTest, self).setUp()
        statprof.start()

    def runTest(self):
        for i in xrange(self.iterations):
            if hasattr(self, 'performanceSample'):
                self.display = True
                self.performanceSample()

    def tearDown(self):
        super(PerformanceTest, self).tearDown()
        statprof.stop()
        if self.display:
            print '>>> %s (%d iterations) ' % (self.__class__.__name__,
                    self.iterations)
            statprof.display()

class DynamicMethodCompilationTest(PerformanceTest):
    def performanceSample(self):
        template = '''
            #import sys
            #import os
            #def testMethod()
                #set foo = [1, 2, 3, 4]
                #return $foo[0]
            #end def
        '''
        template = Cheetah.Template.Template.compile(template, 
            keepRefToGeneratedCode=False)
        template = template()
        value = template.testMethod()

class DynamicSimpleCompilationTest(PerformanceTest):
    def performanceSample(self):
        template = '''
            #import sys
            #import os
            #set foo = [1,2,3,4]

            Well hello there! This is basic.

            Here's an array too: $foo
        '''
        template = Cheetah.Template.Template.compile(template, 
            keepRefToGeneratedCode=False)
        template = template()
        template = unicode(template)


class FilterTest(PerformanceTest):
    template = None
    def setUp(self):
        super(FilterTest, self).setUp()
        template = '''
            #import sys
            #import os
            #set foo = [1, 2, 3, 4]

            $foo, $foo, $foo
        '''
        template = Cheetah.Template.Template.compile(template, 
            keepRefToGeneratedCode=False)
        self.template = template()

    def performanceSample(self):
        value = unicode(self.template)


class LongCompileTest(PerformanceTest):
    ''' Test the compilation on a sufficiently large template '''
    def compile(self, template):
        return Cheetah.Template.Template.compile(template, keepRefToGeneratedCode=False)

    def performanceSample(self):
        template = '''
            #import sys
            #import Cheetah.Template

            #extends Cheetah.Template.Template

            #def header()
                <center><h2>This is my header</h2></center>
            #end def
            
            #def footer()
                #return "Huzzah"
            #end def

            #def scripts()
                #pass
            #end def

            #def respond()
                <html>
                    <head>
                        <title>${title}</title>
                        
                        $scripts()
                    </head>
                    <body>
                        $header()

                        #for $i in $xrange(10)
                            This is just some stupid page!
                            <br/>
                        #end for

                        <br/>
                        $footer()
                    </body>
                    </html>
            #end def
            
        '''
        return self.compile(template)

class LongCompile_CompilerSettingsTest(LongCompileTest):
    def compile(self, template):
        return Cheetah.Template.Template.compile(template, keepRefToGeneratedCode=False,
            compilerSettings={'useStackFrames' : True, 'useAutocalling' : True})

class LongCompileAndRun(LongCompileTest):
    def performanceSample(self):
        template = super(LongCompileAndRun, self).performanceSample()
        template = template(searchList=[{'title' : 'foo'}])
        template = template.respond()
            

if __name__ == '__main__':
    if '--debug' in sys.argv:
        DEBUG = True
        sys.argv = [arg for arg in sys.argv if not arg == '--debug']
    unittest.main()
