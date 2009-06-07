#!/usr/bin/env python

import Cheetah.NameMapper 
import Cheetah.Template

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
    @perftest(1200)
    def test_BasicDynamic(self):
        template = '''
            #def foo(arg1, arg2)
                #pass
            #end def
        '''
        for i in xrange(self.loops):
            klass = Cheetah.Template.Template.compile(template)
            assert klass

if __name__ == '__main__':
    if '--debug' in sys.argv:
        DEBUG = True
        sys.argv = [arg for arg in sys.argv if not arg == '--debug']
    unittest.main()
