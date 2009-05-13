#!/usr/bin/env python

'''
Provides dummy Transaction and Response classes is used by Cheetah in place
of real Webware transactions when the Template obj is not used directly as a
Webware servlet.
'''

import types

def flush():
    pass

class DummyResponse(object):
    '''
        A dummy Response class is used by Cheetah in place of real Webware
        Response objects when the Template obj is not used directly as a Webware
        servlet
    ''' 
    def __init__(self):
        self._outputChunks = outputChunks = []
        self.write = write = outputChunks.append
        def getvalue(outputChunks=outputChunks):
            return ''.join(outputChunks)
        self.getvalue = getvalue
            
        def writeln(txt):
            write(txt)
            write('\n')
        self.writeln = writeln        
        self.flush = flush

    def writelines(self, *lines):
        ## not used
        [self.writeln(ln) for ln in lines]
        
class DummyTransaction(object):
    '''
        A dummy Transaction class is used by Cheetah in place of real Webware
        transactions when the Template obj is not used directly as a Webware
        servlet.

        It only provides a response object and method.  All other methods and
        attributes make no sense in this context.
    '''
    def __init__(self, *args, **kwargs):
        self._response = None

    def response(self, resp=None):
        if self._response is None:
            self._response = resp or DummyResponse()
        return self._response

class TransformerResponse(object):
    def __init__(self, *args, **kwargs):
        self._output = []
        self._filter = None

    def write(self, value):
        self._output.append(value)

    def flush(self):
        pass

    def writeln(self, line):
        self.write(line)
        self.write('\n')

    def writelines(self, *lines):
        [self.writeln(line) for line in lines]

    def getvalue(self, **kwargs):
        output = kwargs.get('outputChunks') or self._output
        rc = ''.join(output)
        if self._filter:
            _filter = self._filter
            if isinstance(_filter, types.TypeType):
                _filter = _filter()
            return _filter.filter(rc)
        return rc


class TransformerTransaction(object):
    def __init__(self, *args, **kwargs):
        self._response = None
    def response(self):
        if self._response:
            return self._response
        return TransformerResponse()

