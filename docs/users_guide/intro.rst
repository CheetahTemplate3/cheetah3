Introduction
===============

Who should read this Guide?
---------------------------

This Users' Guide provides a technical overview and reference for
the Cheetah template system. Knowledge of Python and
object-oriented programming is assumed. The emphasis in this Guide
is on features useful in a wide variety of situations. Information
on less common situations and troubleshooting tips are gradually
being moved to the Cheetah FAQ. There is also a Cheetah Developer's
Guide for those who want to know what goes on under the hood.

What is Cheetah?
----------------

Cheetah is a Python-powered template engine and code generator. It
may be used as a standalone utility or combined with other tools.
Cheetah has many potential uses, but web developers looking for a
viable alternative to ASP, JSP, PHP and PSP are expected to be its
principle user group.

Cheetah:


-  generates HTML, SGML, XML, SQL, Postscript, form email, LaTeX,
   or any other text-based format. It has also been used to produce
   Python, Java and PHP source code.

-  cleanly separates content, graphic design, and program code.
   This leads to highly modular, flexible, and reusable site
   architectures; faster development time; and HTML and program code
   that is easier to understand and maintain. It is particularly well
   suited for team efforts.

-  blends the power and flexibility of Python with a simple
   template language that non-programmers can understand.

-  gives template writers full access in their templates to any
   Python data structure, module, function, object, or method.

-  makes code reuse easy by providing an object-oriented interface
   to templates that is accessible from Python code or other Cheetah
   templates. One template can subclass another and selectively
   reimplement sections of it. A compiled template **is** a Python
   class, so it can subclass a pure Python class and vice-versa.

-  provides a simple yet powerful caching mechanism

Like its namesake, Cheetah is fast, flexible and powerful.


What is the philosophy behind Cheetah?
--------------------------------------
Cheetah's design was guided by these principles:


-  Python for the back end, Cheetah for the front end. Cheetah was
   designed to complement Python, not replace it.

-  Cheetah's core syntax should be easy for non-programmers to
   learn.

-  Cheetah should make code reuse easy by providing an
   object-oriented interface to templates that is accessible from
   Python code or other Cheetah templates.

-  Python objects, functions, and other data structures should be
   fully accessible in Cheetah.

-  Cheetah should provide flow control and error handling. Logic
   that belongs in the front end shouldn't be relegated to the back
   end simply because it's complex.

-  It should be easy to **separate** content, graphic design, and
   program code, but also easy to **integrate**  them.

   A clean separation makes it easier for a team of content writers,
   HTML/graphic designers, and programmers to work together without
   stepping on each other's toes and polluting each other's work. The
   HTML framework and the content it contains are two separate things,
   and analytical calculations (program code) is a third thing. Each
   team member should be able to concentrate on their specialty and to
   implement their changes without having to go through one of the
   others (i.e., the dreaded "webmaster bottleneck").

   While it should be easy to develop content, graphics and program
   code separately, it should be easy to integrate them together into
   a website. In particular, it should be easy:


   -  for **programmers** to create reusable components and functions
      that are accessible and understandable to designers.

   -  for **designers** to mark out placeholders for content and
      dynamic components in their templates.

   -  for **designers** to soft-code aspects of their design that are
      either repeated in several places or are subject to change.

   -  for **designers** to reuse and extend existing templates and thus
      minimize duplication of effort and code.

   -  and, of course, for **content writers** to use the templates that
      designers have created.



Why Cheetah doesn't use HTML-style tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cheetah does not use HTML/XML-style tags like some other template
languages for the following reasons: Cheetah is not limited to
HTML, HTML-style tags are hard to distinguish from real HTML tags,
HTML-style tags are not visible in rendered HTML when something
goes wrong, HTML-style tags often lead to invalid HTML (e.g., ``<img
src="<template-directive>">``), Cheetah tags are less verbose and
easier to understand than HTML-style tags, and HTML-style tags
aren't compatible with most WYSIWYG editors

Besides being much more compact, Cheetah also has some advantages
over languages that put information inside the HTML tags, such as
Zope Page Templates or PHP: HTML or XML-bound languages do not work
well with other languages, While ZPT-like syntaxes work well in
many ways with WYSIWYG HTML editors, they also give up a
significant advantage of those editors - concrete editing of the
document. When logic is hidden away in (largely inaccessible) tags
it is hard to understand a page simply by viewing it, and it is
hard to confirm or modify that logic.

Give me an example!
-------------------

Here's a very simple example that illustrates some of Cheetah's
basic syntax:

::

    <HTML>
    <HEAD><TITLE>$title</TITLE></HEAD>
    <BODY>

    <TABLE>
    #for $client in $clients
    <TR>
    <TD>$client.surname, $client.firstname</TD>
    <TD><A HREF="mailto:$client.email">$client.email</A></TD>
    </TR>
    #end for
    </TABLE>

    </BODY>
    </HTML>

Compare this with PSP:

::

    <HTML>
    <HEAD><TITLE><%=title%></TITLE></HEAD>
    <BODY>

    <TABLE>
    <% for client in clients: %>
    <TR>
    <TD><%=client['surname']%>, <%=client['firstname']%></TD>
    <TD><A HREF="mailto:<%=client['email']%>"><%=client['email']%></A></TD>
    </TR>
    <%end%>
    </TABLE>

    </BODY>
    </HTML>

Section gettingStarted.tutorial has a more typical example that
shows how to get the plug-in values **into** Cheetah, and section
howWorks.cheetah-compile explains how to turn your template
definition into an object-oriented Python module.

Give me an example of a Webware servlet!
----------------------------------------

This example uses an HTML form to ask the user's name, then invokes
itself again to display a **personalized** friendly greeting.

::

    <HTML><HEAD><TITLE>My Template-Servlet</TITLE></HEAD><BODY>
    #set $name = $request.field('name', None)
    #if $name
    Hello $name
    #else
    <FORM ACTION="" METHOD="GET">
    Name: <INPUT TYPE="text" NAME="name"><BR>
    <INPUT TYPE="submit">
    </FORM>
    #end if
    </BODY></HTML>

To try it out for yourself on a Webware system:


#. copy the template definition to a file **test.tmpl** in your
   Webware servlet directory.

#. Run ``cheetah compile test.tmpl``. This produces ``test.py`` (a
   .py template module) in the same directory.

#. In your web browser, go to ``test.py``, using whatever site and
   directory is appropriate.

At the first request, field 'name' will be blank (false) so the
"#else" portion will execute and present a form. You type your name
and press submit. The form invokes the same page. Now 'name' is
true so the "#if" portion executes, which displays the greeting.
The "#set" directive creates a local variable that lasts while the
template is being filled.

How mature is Cheetah?
----------------------

Cheetah is stable, production quality, post-beta code. Cheetah's
syntax, semantics and performance have been generally stable since
a performance overhaul in mid 2001. Most of the changes since
October 2001 have been in response to specific requests by
production sites, things they need that we hadn't considered.

As of summer 2003, we are putting in the final touches before the
1.0 release.


Where can I get news?
---------------------

Cheetah releases can be obtained from the `Cheetah
website <https://cheetahtemplate.org/>`_

If you encounter difficulties, or are unsure about how to do something, please
post a detailed message to the `bug tracker
<https://github.com/CheetahTemplate3/cheetah3/issues>`.

How can I contribute?
---------------------

Cheetah is the work of many volunteers. If you use Cheetah please
share your experiences, tricks, customizations, and frustrations.

Bug reports and patches
~~~~~~~~~~~~~~~~~~~~~~~

If you think there is a bug in Cheetah, send a message to the
e-mail list with the following information:


#. a description of what you were trying to do and what happened

#. all tracebacks and error output

#. your version of Cheetah

#. your version of Python

#. your operating system

#. whether you have changed anything in the Cheetah installation


Template libraries and function libraries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We hope to build up a framework of Template libraries (see section
libraries.templates) to distribute with Cheetah and would
appreciate any contributions.

Test cases
~~~~~~~~~~

Cheetah is packaged with a regression testing suite that is run
with each new release to ensure that everything is working as
expected and that recent changes haven't broken anything. The test
cases are in the Cheetah.Tests module. If you find a reproduceable
bug please consider writing a test case that will pass only when
the bug is fixed. Send any new test cases to the email list with
the subject-line "new test case for Cheetah."

Publicity
~~~~~~~~~

Help spread the word ... recommend it to others, write articles
about it, etc.

Acknowledgements
----------------

Cheetah is one of several templating frameworks that grew out of a
'templates' thread on the Webware For Python email list. Tavis
Rudd, Mike Orr, Chuck Esterbrook and Ian Bicking are the core
developers.

We'd like to thank the following people for contributing valuable
advice, code and encouragement: Geoff Talvola, Jeff Johnson, Graham
Dumpleton, Clark C. Evans, Craig Kattner, Franz Geiger, Geir
Magnusson, Tom Schwaller, Rober Kuzelj, Jay Love, Terrel Shumway,
Sasa Zivkov, Arkaitz Bitorika, Jeremiah Bellomy, Baruch Even, Paul
Boddie, Stephan Diehl, Chui Tey, Michael Halle, Edmund Lian and
Aaron Held.

The Velocity, WebMacro and Smarty projects provided inspiration and
design ideas. Cheetah has benefitted from the creativity and energy
of their developers. Thank you.
