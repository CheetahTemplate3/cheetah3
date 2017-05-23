Basic Inheritance
=================

Introduction
------------
Cheetah, like Python, is an object-oriented language if you so choose to
use it in that fashion. That is to say that you can use Cheetah in with
object-oriented principles *or* you can use Cheetah in a strictly functional
sense, like Python, Cheetah does not place restrictions on these barriers.

While Cheetah is not strictly Python, it was designed as such to interoperate,
particularly with the notion of classes, with Python itself. In effect you can
define Python classes that inherit and extend from Cheetah-derived classes and
vice versa. For this, Cheetah defines a few **directives** (denoted with the `\#`
hash-mark) that are of some help, the most important one being the `\#extends`
directive, with others playing important roles like `\#import`, `\#attr` and `\#super`

In this recipe/tutorial I intend to explain and define a few key inheritance
patterns with Cheetah, being:

* A Cheetah Template inheriting from Python
* Python inheriting from a Cheetah Template
* Cheetah Templates and "*mixins*"

This document also operates on the assumption that the reader is at least
somewhat familiar with the basic tenets of object-oriented programming in
Python.


Cheetah inheriting from Python
------------------------------
Whether or not you are aware of it, Cheetah templates are always inheriting from
a Python class by default. Unless otherwise denoted, Cheetah templates are compiled
to Python classes that subclass from the `Cheetah.Template.Template` class.

What if you would like to introduce your own Template base class? Easily acheived by
defining your own Template class in a Python module, for example::

    import Cheetah.Template

    class CookbookTemplate(Cheetah.Template.Template):
        _page = 'Cookbook'
        author = 'R. Tyler Ballance'
        def pageName(self):
            return self._page or 'Unknown'

**Figure 1. cookbook.py**

For this example, I want all my subclasses of the `CookbookTemplate` to define a
page author which will be used in some shared rendering code, to accomplish this
my templates will need to subclass from `CookbookTemplate` explicitly instead of
implicitly subclassing from `Cheetah.Template.Template`::

    #import cookbook
    #extends cookbook.CookbookTemplate
    #attr author = 'Tavis Rudd'

    ## The rest of my recipe template would be below

**Figure 2. recipe1.tmpl**


