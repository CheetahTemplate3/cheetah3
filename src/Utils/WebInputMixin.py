#!/usr/bin/env python
# $Id: WebInputMixin.py,v 1.8 2005/01/03 18:12:20 tavis_rudd Exp $
"""Mixin for Cheetah.Servlet for importing web transaction variables in bulk.

This works for GET/POST fields both in Webware servlets and in CGI scripts, 
and for cookies and session variables in Webware servlets.  If you try to
read a cookie or session variable in a CGI script, you'll get a RuntimeError.
'In a CGI script' here means 'not running as a Webware servlet'.  If the CGI
environment is not properly set up, Cheetah will act like there's no input.

The public method provided is:

    def webInput(self, names, namesMulti=(), default='', src='f',
        defaultInt=0, defaultFloat=0.00, badInt=0, badFloat=0.00, debug=False):

This method places the specified GET/POST fields, cookies or session variables
into a dictionary, which is both returned and put at the beginning of the
searchList.  It handles:
    * single vs multiple values
    * conversion to integer or float for specified names
    * default values/exceptions for missing or bad values
    * printing a snapshot of all values retrieved for debugging
All the 'default*' and 'bad*' arguments have 'use or raise' behavior, meaning 
that if they're a subclass of Exception, they're raised.  If they're anything
else, that value is substituted for the missing/bad value.  


The simplest usage is:

    #silent $webInput(['choice'])
    $choice

    dic = self.webInput(['choice'])
    write(dic['choice'])

Both these examples retrieves the GET/POST field 'choice' and print it.  If you
leave off the '#silent', all the values would be printed too.  But a better way
to preview the values is

    #silent $webInput(['name'], $debug=1)

because this pretty-prints all the values inside HTML <PRE> tags.

** KLUDGE: 'debug' is supposed to insert into the template output, but it
wasn't working so I changed it to a 'print' statement.  So the debugging
output will appear wherever standard output is pointed, whether at the
terminal, in a Webware log file, or whatever. ***

Since we didn't specify any coversions, the value is a string.  It's a 'single'
value because we specified it in 'names' rather than 'namesMulti'.  Single
values work like this:
    * If one value is found, take it.
    * If several values are found, choose one arbitrarily and ignore the rest.
    * If no values are found, use or raise the appropriate 'default*' value.

Multi values work like this:
    * If one value is found, put it in a list.
    * If several values are found, leave them in a list.
    * If no values are found, use the empty list ([]).  The 'default*' 
      arguments are *not* consulted in this case.

Example: assume 'days' came from a set of checkboxes or a multiple combo box
on a form, and the user chose 'Monday', 'Tuesday' and 'Thursday'.

    #silent $webInput([], ['days'])
    The days you chose are: #slurp
    #for $day in $days
    $day #slurp
    #end for

    dic = self.webInput([], ['days'])
    write('The days you chose are: ')
    for day in dic['days']:
        write(day + ' ')

Both these examples print:  'The days you chose are: Monday Tuesday Thursday'.

By default, missing strings are replaced by '' and missing/bad numbers by zero.
(A 'bad number' means the converter raised an exception for it, usually because
of non-numeric characters in the value.)  This mimics Perl/PHP behavior, and
simplifies coding for many applications where missing/bad values *should* be
blank/zero.  In those relatively few cases where you must distinguish between
''/zero on the one hand and missing/bad on the other, change the appropriate
'default*' and 'bad*' arguments to something like: 
    * None
    * another constant value
    * $NonNumericInputError/self.NonNumericInputError
    * $ValueError/ValueError
(NonNumericInputError is defined in this class and is useful for
distinguishing between bad input vs a TypeError/ValueError
thrown for some other rason.)

Here's an example using multiple values to schedule newspaper deliveries.
'checkboxes' comes from a form with checkboxes for all the days of the week.
The days the user previously chose are preselected.  The user checks/unchecks
boxes as desired and presses Submit.  The value of 'checkboxes' is a list of
checkboxes that were checked when Submit was pressed.  Our task now is to
turn on the days the user checked, turn off the days he unchecked, and leave
on or off the days he didn't change.

    dic = self.webInput([], ['dayCheckboxes'])
    wantedDays = dic['dayCheckboxes'] # The days the user checked.
    for day, on in self.getAllValues():
        if   not on and wantedDays.has_key(day):
            self.TurnOn(day)
            # ... Set a flag or insert a database record ...
        elif on and not wantedDays.has_key(day):
            self.TurnOff(day)
            # ... Unset a flag or delete a database record ...

'source' allows you to look up the variables from a number of different
sources:
    'f'   fields (CGI GET/POST parameters)
    'c'   cookies
    's'   session variables
    'v'   'values', meaning fields or cookies

In many forms, you're dealing only with strings, which is why the
'default' argument is third and the numeric arguments are banished to
the end.  But sometimes you want automatic number conversion, so that
you can do numeric comparisions in your templates without having to
write a bunch of conversion/exception handling code.  Example:

    #silent $webInput(['name', 'height:int'])
    $name is $height cm tall.
    #if $height >= 300
    Wow, you're tall!
    #else
    Pshaw, you're short.
    #end if

    dic = self.webInput(['name', 'height:int'])
    name = dic[name]
    height = dic[height]
    write('%s is %s cm tall.' % (name, height))
    if height > 300:
        write('Wow, you're tall!')
    else:
        write('Pshaw, you're short.')

To convert a value to a number, suffix ':int' or ':float' to the name.  The
method will search first for a 'height:int' variable and then for a 'height'
variable.  (It will be called 'height' in the final dictionary.)  If a numeric
conversion fails, use or raise 'badInt' or 'badFloat'.  Missing values work
the same way as for strings, except the default is 'defaultInt' or
'defaultFloat' instead of 'default'.

If a name represents an uploaded file, the entire file will be read into 
memory.  For more sophistocated file-upload handling, leave that name out of
the list and do your own handling, or wait for Cheetah.Utils.UploadFileMixin.

This mixin class works only in a subclass that also inherits from 
Webware's Servlet or HTTPServlet.  Otherwise you'll get an AttributeError
on 'self.request'.

EXCEPTIONS: ValueError if 'source' is not one of the stated characters.
TypeError if a conversion suffix is not ':int' or ':float'.

FUTURE EXPANSION: a future version of this method may allow source
cascading; e.g., 'vs' would look first in 'values' and then in session
variables.

Meta-Data
================================================================================
Author: Mike Orr <iron@mso.oz.net>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.8 $
Start Date: 2002/03/17
Last Revision Date: $Date: 2005/01/03 18:12:20 $
""" 
__author__ = "Mike Orr <iron@mso.oz.net>"
__revision__ = "$Revision: 1.8 $"[11:-2]

import cgi     # Used by WebInputMixin.cgiImport() if this is a CGI script.
import pprint
import types
from Cheetah.Utils.Misc import useOrRaise

class NonNumericInputError(ValueError):
    pass

##################################################
## PRIVATE FUNCTIONS AND CLASSES

# Cache of a cgi.FieldStorage() instance, maintained by .webInput().
_form = None

class _Converter:
    """A container object for info about type converters.
    .name, string, name of this converter (for error messages).
    .func, function, factory function.
    .default, value to use or raise if the real value is missing.
    .error, value to use or raise if .func() raises an exception.
    """
    def __init__(self, name, func, default, error):
        self.name = name
        self.func = func
        self.default = default
        self.error = error


def _lookup(name, func, multi, converters):
    """Look up a Webware field/cookie/value/session value.  Return
    '(realName, value)' where 'realName' is like 'name' but with any
    conversion suffix strips off.  Applies numeric conversion and
    single vs multi values according to the comments in the source.
    """
    # Step 1 -- split off the conversion suffix from 'name'; e.g. "height:int".
    # If there's no colon, the suffix is "".  'longName' is the name with the 
    # suffix, 'shortName' is without.    
    # XXX This implementation assumes "height:" means "height".
    colon = name.find(':')
    if colon != -1:
        longName = name
        shortName, ext = name[:colon], name[colon+1:]
    else:
        longName = shortName = name
        ext = ''

    # Step 2 -- look up the values by calling 'func'.
    if longName != shortName:
        values = func(longName, None) or func(shortName, None)
    else:
        values = func(shortName, None)
    # 'values' is a list of strings, a string or None.

    # Step 3 -- Coerce 'values' to a list of zero, one or more strings.
    if   values is None:
        values = []
    elif type(values) == types.StringType:
        values = [values]

    # Step 4 -- Find a _Converter object or raise TypeError.
    try:
        converter = converters[ext]
    except KeyError:
        fmt = "'%s' is not a valid converter name in '%s'"
        tup = (ext, longName)
        raise TypeError(fmt % tup)    

    # Step 5 -- if there's a converter func, run it on each element.
    # If the converter raises an exception, use or raise 'converter.error'.
    if converter.func is not None:
        tmp = values[:]
        values = []
        for elm in tmp:
            try:
                elm = converter.func(elm)
            except (TypeError, ValueError):
                tup = converter.name, elm
                errmsg = "%s '%s' contains invalid characters" % tup
                elm = useOrRaise(converter.error, errmsg)
            values.append(elm)
    # 'values' is now a list of strings, ints or floats.

    # Step 6 -- If we're supposed to return a multi value, return the list
    # as is.  If we're supposed to return a single value and the list is
    # empty, return or raise 'converter.default'.  Otherwise, return the
    # first element in the list and ignore any additional values.
    if   multi:
        return shortName, values
    if len(values) == 0:
        return shortName, useOrRaise(converter.default)
    return shortName, values[0]

    
##################################################
## PUBLIC CLASS

class WebInputMixin:
    """A mixin class for Cheetah.Template with a method for importing 
    web transaction variables in bulk.  Depends on a base class of
    Webware [HTTP]Servlet.
    """
    
    NonNumericInputError = NonNumericInputError

    def webInput(self, names, namesMulti=(), default='', src='f',
        defaultInt=0, defaultFloat=0.00, badInt=0, badFloat=0.00, debug=False):
        """Import web transaction variables in bulk.  See module docstring.
        """
        src = src.lower()
        isCgi = not self.isControlledByWebKit
        if   isCgi and src in ('f', 'v'):
            global _form
            if _form is None:
                _form = cgi.FieldStorage()
            source, func = 'field',   _form.getvalue
        elif isCgi and src == 'c':
            raise RuntimeError("can't get cookies from a CGI script")
        elif isCgi and src == 's':
            raise RuntimeError("can't get session variables from a CGI script")
        elif isCgi and src == 'v':
            source, func = 'value',   self.request().value
        elif isCgi and src == 's':
            source, func = 'session', self.request().session().value
        elif src == 'f':
            source, func = 'field',   self.request().field
        elif src == 'c':
            source, func = 'cookie',  self.request().cookie
        elif src == 'v':
            source, func = 'value',   self.request().value
        elif src == 's':
            source, func = 'session', self.request().session().value
        else:
            raise TypeError("arg 'src' invalid")
        sources = source + 's'
        converters = {
            ''     : _Converter('string', None, default,      default ),
            'int'  : _Converter('int',     int, defaultInt,   badInt  ),
            'float': _Converter('float', float, defaultFloat, badFloat),  }
        #pprint.pprint(locals());  return {}
        dic = {} # Destination.
        for name in names:
            k, v = _lookup(name, func, False, converters)
            dic[k] = v
        for name in namesMulti:
            k, v = _lookup(name, func, True, converters)
            dic[k] = v
        # At this point, 'dic' contains all the keys/values we want to keep.
        # We could split the method into a superclass
        # method for Webware/WebwareExperimental and a subclass for Cheetah.
        # The superclass would merely 'return dic'.  The subclass would
        # 'dic = super(ThisClass, self).webInput(names, namesMulti, ...)'
        # and then the code below.
        if debug:
           print "<PRE>\n" + pprint.pformat(dic) + "\n</PRE>\n\n"
        self.searchList().insert(0, dic)
        return dic


# vim: sw=4 ts=4 expandtab
