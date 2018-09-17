Directives: Error Handling
==========================


#try and #raise
---------------


The template:

::

    #import traceback
    #try
    #raise RuntimeError
    #except RuntimeError
    A runtime error occurred.
    #end try

    #try
    #raise RuntimeError("Hahaha!")
    #except RuntimeError
    #echo $sys.exc_info()[1]
    #end try

    #try
    #echo 1/0
    #except ZeroDivisionError
    You can't divide by zero, idiot!
    #end try

The output:

::

    A runtime error occurred.

    Hahaha!

    You can't divide by zero, idiot!

The generated code:

::

    try:
        raise RuntimeError
    except RuntimeError:
        write('A runtime error occurred.\n')
    write('\n')
    try:
        raise RuntimeError("Hahaha!")
    except RuntimeError:
        write(filter(VFN(sys,"exc_info",0)()[1]))
        write('\n')
    write('\n')
    try:
        write(filter(1/0))
        write('\n')
    except ZeroDivisionError:
        write("You can't divide by zero, idiot!\n")

{#finally} works just like in Python.

#assert
-------


The template:

::

    #assert False, "You lose, buster!"

The output:

::

    Traceback (most recent call last):
      File "x.py", line 117, in ?
        x().runAsMainProgram()
      File "/local/opt/Python/lib/python2.2/site-packages/Webware/Cheetah/
    Template.py", line 331, in runAsMainProgram
        CmdLineIface(templateObj=self).run()
      File "/local/opt/Python/lib/python2.2/site-packages/Webware/Cheetah/
    TemplateCmdLineIface.py", line 59, in run
        print self._template
      File "x.py", line 91, in respond
        assert False, "You lose, buster!"
    AssertionError: You lose, buster!

The generated code:

::

    assert False, "You lose, buster!"

#errorCatcher
-------------


No error catcher
~~~~~~~~~~~~~~~~


The template:

::

    $noValue

The output:

::

    Traceback (most recent call last):
      File "x.py", line 118, in ?
        x().runAsMainProgram()
      File "/local/opt/Python/lib/python2.2/site-packages/Webware/Cheetah/
    Template.py", line 331, in runAsMainProgram
        CmdLineIface(templateObj=self).run()
      File "/local/opt/Python/lib/python2.2/site-packages/Webware/Cheetah/
    TemplateCmdLineIface.py", line 59, in run
        print self._template
      File "x.py", line 91, in respond
        write(filter(VFS(SL,"noValue",1))) # generated from '$noValue' at line
    1, col 1.
    NameMapper.NotFound: noValue

The generated code:

::

    write(filter(VFS(SL,"noValue",1))) # generated from '$noValue' at line 1,
        # col 1.
    write('\n')

Echo and BigEcho
~~~~~~~~~~~~~~~~


The template:

::

    #errorCatcher Echo
    $noValue
    #errorCatcher BigEcho
    $noValue

The output:

::

    $noValue
    ===============&lt;$noValue could not be found&gt;===============

The generated code:

::

    if "Echo" in self._errorCatchers:
        self._errorCatcher = self._errorCatchers["Echo"]
    else:
        self._errorCatcher = self._errorCatchers["Echo"] = ErrorCatchers.Echo(self)
    write(filter(self.__errorCatcher1(localsDict=locals())))
        # generated from '$noValue' at line 2, col 1.
    write('\n')
    if "BigEcho" in self._errorCatchers:
        self._errorCatcher = self._errorCatchers["BigEcho"]
    else:
        self._errorCatcher = self._errorCatchers["BigEcho"] = \
            ErrorCatchers.BigEcho(self)
    write(filter(self.__errorCatcher1(localsDict=locals())))
            # generated from '$noValue' at line 4, col 1.
    write('\n')

ListErrors
~~~~~~~~~~


The template:

::

    #import pprint
    #errorCatcher ListErrors
    $noValue
    $anotherMissingValue.really
    $pprint.pformat($errorCatcher.listErrors)
    ## This is really self.errorCatcher().listErrors()

The output:

::

    $noValue
    $anotherMissingValue.really
    [{'code': 'VFS(SL,"noValue",1)',
      'exc_val': <NameMapper.NotFound instance at 0x8170ecc>,
      'lineCol': (3, 1),
      'rawCode': '$noValue',
      'time': 'Wed May 15 00:38:23 2002'},
     {'code': 'VFS(SL,"anotherMissingValue.really",1)',
      'exc_val': <NameMapper.NotFound instance at 0x816d0fc>,
      'lineCol': (4, 1),
      'rawCode': '$anotherMissingValue.really',
      'time': 'Wed May 15 00:38:23 2002'}]

The generated import:

::

    import pprint

Then in the generated class, we have our familiar {.respond} method
and several new methods:

::

    def __errorCatcher1(self, localsDict={}):
        """
        Generated from $noValue at line, col (3, 1).
        """

        try:
            return eval('''VFS(SL,"noValue",1)''', globals(), localsDict)
        except self._errorCatcher.exceptions(), e:
            return self._errorCatcher.warn(exc_val=e, code= 'VFS(SL,"noValue",1)' ,
            rawCode= '$noValue' , lineCol=(3, 1))

    def __errorCatcher2(self, localsDict={}):
        """
        Generated from $anotherMissingValue.really at line, col (4, 1).
        """

        try:
            return eval('''VFS(SL,"anotherMissingValue.really",1)''', globals(),
            localsDict)
        except self._errorCatcher.exceptions(), e:
            return self._errorCatcher.warn(exc_val=e,
            code= 'VFS(SL,"anotherMissingValue.really",1)' ,
            rawCode= '$anotherMissingValue.really' , lineCol=(4, 1))

    def __errorCatcher3(self, localsDict={}):
        """
        Generated from $pprint.pformat($errorCatcher.listErrors) at line, col
        (5, 1).
        """

        try:
            return eval('''VFN(pprint,"pformat",0)(VFS(SL,
            "errorCatcher.listErrors",1))''', globals(), localsDict)
        except self._errorCatcher.exceptions(), e:
            return self._errorCatcher.warn(exc_val=e, code=
            'VFN(pprint,"pformat",0)(VFS(SL,"errorCatcher.listErrors",1))' ,
            rawCode= '$pprint.pformat($errorCatcher.listErrors)' ,
            lineCol=(5, 1))

::

    def respond(self,
            trans=None,
            dummyTrans=False,
            VFS=valueFromSearchList,
            VFN=valueForName,
            getmtime=getmtime,
            currentTime=time.time):


        """
        This is the main method generated by Cheetah
        """

        if not trans:
            trans = DummyTransaction()
            dummyTrans = True
        write = trans.response().write
        SL = self._searchList
        filter = self._currentFilter
        globalSetVars = self._globalSetVars

        ########################################
        ## START - generated method body

        if exists(self._filePath) and getmtime(self._filePath) > self._fileMtime:
            self.compile(file=self._filePath)
            write(getattr(self, self._mainCheetahMethod_for_x)(trans=trans))
            if dummyTrans:
                return trans.response().getvalue()
            else:
                return ""
        if "ListErrors" in self._errorCatchers:
            self._errorCatcher = self._errorCatchers["ListErrors"]
        else:
            self._errorCatcher = self._errorCatchers["ListErrors"] = \
            ErrorCatchers.ListErrors(self)
        write(filter(self.__errorCatcher1(localsDict=locals())))
            # generated from '$noValue' at line 3, col 1.
        write('\n')
        write(filter(self.__errorCatcher2(localsDict=locals())))
            # generated from '$anotherMissingValue.really' at line 4, col 1.
        write('\n')
        write(filter(self.__errorCatcher3(localsDict=locals())))
            # generated from '$pprint.pformat($errorCatcher.listErrors)' at line
        # 5, col 1.
        write('\n')
        #  This is really self.errorCatcher().listErrors()

        ########################################
        ## END - generated method body

        if dummyTrans:
            return trans.response().getvalue()
        else:
            return ""

So whenever an error catcher is active, each placeholder gets
wrapped in its own method. No wonder error catchers slow down the
system!


