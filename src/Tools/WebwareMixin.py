#!/usr/bin/env python
"""WebwareMixin.py -- convenience class for Cheetah/Webware servlets.

This module is *not* required to access Webware features in your template.

Last update: 29-Nov-2001.  Maintained by Mike Orr <iron@mso.oz.net>.
"""



class WebwareMixin:
    def cgiImport(self, keys, what='fields', default=KeyError):
        """Import stuff from the web environment into the searchList.
        
        in : keys, list of strings, the keys to import.
             what, string, one of "fields", "cookies", "sessions", "values". 
               You may also use the singular word (e.g., "field").
               "values" means "fields or cookies".  "sessions" means session
               VALUES.
             default, anything, used as the default value if any key is missing.
               If a subclass of Exception, raise it instead.
        out: None.
        act: Adds a dictionary namespace to the searchList containing the
               specified keys and values from the specified source.
        exc: TypeError if 'what' is an unrecognized parameter type.
        """
        dst = {} # Destination.       
        if   what in ('field', 'fields'):
            src = self.request().fields() # Source.
        elif what in ('cookie', 'cookies'):
            src = self.request().cookies()
        elif what in ('value', 'values'):
            src = self.request().cookies()
        elif what in ('session', 'sessions'):
            src = self.request().session().values()
        else:
            raise TypeError("arg 'what' refers to an unknown parameter type")
        raiseIt = issubclass(default, Exception)
        dst = {} # Destination.
        for key in keys:
            try:
                dst[key] = src[key]
            except KeyError:
                if raiseIt:
                    reason = "%s key '%s'" % (what, key)
                    raise default(reason)
                else:
                    dst[key] = default
        self.addToSearchList(dst)
