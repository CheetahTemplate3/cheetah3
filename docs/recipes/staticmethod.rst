@staticmethod and @classmethod
==============================

Refer the Python's documentation if you're unfamiliar with either
`@staticmethod <http://docs.python.org/library/functions.html#staticmethod>`_ or
`@classmethod <http://docs.python.org/library/functions.html#classmethod>`_ and their uses in Python, as they
pertain to their uses in Cheetah as well. Using `@staticmethod <http://docs.python.org/library/functions.html#staticmethod>`_ it's
trivial to create *utility templates* which are common when using
Cheetah for web development. These *utility templates* might contain
a number of small functions which generate useful snippets of markup.

For example::

    #def copyright()
        #import time
        &copy; CheetahCorp, Inc. $time.strftime('%Y', time.gmtime())
    #end def

**Figure 1, util.tmpl**

Prior to version **v2.2.0** of Cheetah, there wasn't really an easy means
of filling templates with bunches of these small utility functions. In
**v2.2.0** however, you can decorate these methods with `#@staticmethod`
and use "proper" Python syntax for calling them, **fig 1** revisited::

    #@staticmethod
    #def copyright()
        #import time
        &copy; CheetahCorp, Inc. $time.strftime('%Y', time.gmtime())
    #end def

**Figure 1.1, util.tmpl**

With the addition of the `@staticmethod <http://docs.python.org/library/functions.html#staticmethod>`_ decorator, the `copyright()`
function can now be used without instantiating an instance of the `util`
template class. In effect::

    #from util import util

    <strong>This is my page</strong>
    <br/>
    <hr noshade/>
    $util.copyright()

**Figure 2, index.tmpl**


This approach is however no means to structure anything complex,
`@staticmethod <http://docs.python.org/library/functions.html#staticmethod>`_ and `@classmethod <http://docs.python.org/library/functions.html#classmethod>`_ use in Cheetah is not meant as a
replacement for properly structured class hierarchies (which
Cheetah supports). That said if you are building a web application
`@staticmethod <http://docs.python.org/library/functions.html#staticmethod>`_/`@classmethod <http://docs.python.org/library/functions.html#classmethod>`_ are quite useful for the little snippets
of markup, etc that are needed (Google AdSense blocks, footers,
banners, etc).
