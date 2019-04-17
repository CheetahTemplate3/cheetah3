.. Cheetah Template Engine documentation master file, created by
   sphinx-quickstart on Sun May 31 22:23:43 2009.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Cheetah3, the Python-Powered Template Engine
============================================

Introduction
------------
Cheetah3 is a free and `open source
<https://github.com/CheetahTemplate3/cheetah3>`_ template engine and
code-generation tool written in `Python <http://python.org>`_. Cheetah can be
used unto itself, or incorporated with other technologies and stacks regardless
of whether they're written in Python or not.

At its core, Cheetah is a domain-specific language for markup generation and
templating which allows for full integration with existing Python code but also
offers extensions to traditional Python syntax to allow for easier text-generation.

It's a fork of the `original <https://github.com/cheetahtemplate/cheetah>`_
CheetahTemplate library.

Talk Cheetah
^^^^^^^^^^^^
You can get involved and talk with Cheetah developers on the `Cheetah3 issue
tracker <https://github.com/CheetahTemplate3/cheetah3/issues>`_.

Contents
^^^^^^^^^

.. toctree::
   :maxdepth: 2

   authors.rst
   news.rst
   developers.rst
   download.rst
   users_guide/index.rst
   documentation.rst
   roadmap.rst
   dev_guide/index.rst
   chep.rst


Cheetah in a nutshell
---------------------
Below is a simple example of some Cheetah code, as you can see it's practically
Python. You can import, inherit and define methods just like in a regular Python
module, since that's what your Cheetah templates are compiled to :) ::

    #from Cheetah.Template import Template
    #extends Template

    #set $people = [{'name' : 'Tom', 'mood' : 'Happy'}, {'name' : 'Dick',
                            'mood' : 'Sad'}, {'name' : 'Harry', 'mood' : 'Hairy'}]

    <strong>How are you feeling?</strong>
    <ul>
        #for $person in $people
            <li>
                $person['name'] is $person['mood']
            </li>
        #end for
    </ul>


Why Cheetah?
------------

* Cheetah is supported by every major Python web framework.
* It is fully documented and is supported by an active user community.
* It can output/generate any text-based format.
* Cheetah compiles templates into optimized, yet readable, Python code.
* It blends the power and flexibility of Python with a simple template language that non-programmers can understand.
* It gives template authors full access to any Python data structure, module, function, object, or method in their templates. Meanwhile, it provides a way for administrators to selectively restrict access to Python when needed.
* Cheetah makes code reuse easy by providing an object-oriented interface to templates that is accessible from Python code or other Cheetah templates. One template can subclass another and selectively reimplement sections of it. Cheetah templates can be subclasses of any Python class and vice-versa.
* It provides a simple, yet powerful, caching mechanism that can dramatically improve the performance of a dynamic website.
* It encourages clean separation of content, graphic design, and program code. This leads to highly modular, flexible, and reusable site architectures, shorter development time, and HTML and program code that is easier to understand and maintain. It is particularly well suited for team efforts.
* Cheetah can be used to generate static html via its command-line tool.


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

