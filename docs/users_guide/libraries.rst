Batteries included: templates and other libraries
=================================================


Cheetah comes "batteries included" with libraries of templates,
functions, classes and other objects you can use in your own
programs. The different types are listed alphabetically below,
followed by a longer description of the SkeletonPage framework.
Some of the objects are classes for specific purposes (e.g.,
filters or error catchers), while others are standalone and can be
used without Cheetah.

If you develop any objects which are generally useful for Cheetah
sites, please consider posting them on the wiki with an
announcement on the mailing list so we can incorporate them into
the standard library. That way, all Cheetah users will benefit, and
it will encourage others to contribute their objects, which might
include something you want.

ErrorCatchers
-------------


Module {Cheetah.ErrorCatchers} contains error-handling classes
suitable for the {#errorCatcher} directive. These are debugging
tools that are not intended for use in production systems. See
section errorHandling.errorCatcher for a description of the error
catchers bundled with Cheetah.

FileUtils
---------


Module {Cheetah.FileUtils} contains generic functions and classes
for doing bulk search-and-replace on several files, and for finding
all the files in a directory hierarchy whose names match a glob
pattern.

Filters
-------


Module {Filters} contains filters suitable for the {#Filter}
directive. See section output.filter for a description of the
filters bundled with Cheetah.

SettingsManager
---------------


The {SettingsManager} class in the {Cheetah.SettingsManager} module
is a baseclass that provides facilities for managing application
settings. It facilitates the use of user-supplied configuration
files to fine tune an application. A setting is a key/value pair
that an application or component (e.g., a filter, or your own
servlets) looks up and treats as a configuration value to modify
its (the component's) behaviour.

SettingsManager is designed to:


-  work well with nested settings dictionaries of any depth

-  read/write {.ini style config files} (or strings)

-  read settings from Python source files (or strings) so that
   complex Python objects can be stored in the application's settings
   dictionary. For example, you might want to store references to
   various classes that are used by the application, and plugins to
   the application might want to substitute one class for another.

-  allow sections in {.ini config files} to be extended by settings
   in Python source files. If a section contains a setting like
   "{importSettings=mySettings.py}", {SettingsManager} will merge all
   the settings defined in "{mySettings.py}" with the settings for
   that section that are defined in the {.ini config file}.

-  maintain the case of setting names, unlike the ConfigParser
   module


Cheetah uses {SettingsManager} to manage its configuration
settings. {SettingsManager} might also be useful in your own
applications. See the source code and docstrings in the file
{Cheetah/SettingsManager.py} for more information.

Templates
---------


Package {Cheetah.Templates} contains stock templates that you can
either use as is, or extend by using the {#def} directive to
redefine specific { blocks}. Currently, the only template in here
is SkeletonPage, which is described in detail below in section
libraries.templates.skeletonPage. (Contributed by Tavis Rudd.)

Tools
-----


Package {Cheetah.Tools} contains functions and classes contributed
by third parties. Some are Cheetah-specific but others are generic
and can be used standalone. None of them are imported by any other
Cheetah component; you can delete the Tools/ directory and Cheetah
will function fine.

Some of the items in Tools/ are experimental and have been placed
there just to see how useful they will be, and whether they attract
enough users to make refining them worthwhile (the tools, not the
users :).

Nothing in Tools/ is guaranteed to be: (A) tested, (B) reliable,
(C) immune from being deleted in a future Cheetah version, or (D)
immune from backwards-incompatable changes. If you depend on
something in Tools/ on a production system, consider making a copy
of it outside the Cheetah/ directory so that this version won't be
lost when you upgrade Cheetah. Also, learn enough about Python and
about the Tool so that you can maintain it and bugfix it if
necessary.

If anything in Tools/ is found to be necessary to Cheetah's
operation (i.e., if another Cheetah component starts importing it),
it will be moved to the {Cheetah.Utils} package.

Current Tools include:

    an ambitious class useful when iterating over records of data
    ({#for} loops), displaying one pageful of records at a time (with
    previous/next links), and printing summary statistics about the
    records or the current page. See {MondoReportDoc.txt} in the same
    directory as the module. Some features are not implemented yet.
    {MondoReportTest.py} is a test suite (and it shows there are
    currently some errors in MondoReport, hmm). Contributed by Mike
    Orr.

    Nothing, but in a friendly way. Good for filling in for objects you
    want to hide. If {$form.f1} is a RecursiveNull object, then
    {$form.f1.anything["you"].might("use")} will resolve to the empty
    string. You can also put a {RecursiveNull} instance at the end of
    the searchList to convert missing values to '' rather than raising
    a {NotFound} error or having a (less efficient) errorCatcher handle
    it. Of course, maybe you prefer to get a {NotFound} error...
    Contributed by Ian Bicking.

    Provides navigational links to this page's parents and children.
    The constructor takes a recursive list of (url,description) pairs
    representing a tree of hyperlinks to every page in the site (or
    section, or application...), and also a string containing the
    current URL. Two methods 'menuList' and 'crumbs' return
    output-ready HTML showing an indented menu (hierarchy tree) or
    crumbs list (Yahoo-style bar: home > grandparent > parent >
    currentURL). Contributed by Ian Bicking.


Utils
-----


Package {Cheetah.Utils} contains non-Cheetah-specific functions and
classes that are imported by other Cheetah components. Many of
these utils can be used standalone in other applications too.

Current Utils include:

    This is inherited by {Template} objects, and provides the method,
    {.cgiImport} method (section webware.cgiImport).

    A catch-all module for small functions.

        Raise 'thing' if it's a subclass of Exception, otherwise return it.
        Useful when one argument does double duty as a default value or an
        exception to throw. Contribyted by Mike Orr.

        Verifies the dictionary does not contain any keys not listed in
        'legalKeywords'. If it does, raise TypeError. Useful for checking
        the keyword arguments to a function. Contributed by Mike Orr.


    Not implemented yet, but will contain the {.uploadFile} method (or
    three methods) to "safely" copy a form-uploaded file to a local
    file, to a searchList variable, or return it. When finished, this
    will be inherited by {Template}, allowing all templates to do this.
    If you want this feature, read the docstring in the source and let
    us know on the mailing list what you'd like this method to do.
    Contributed by Mike Orr.

    Functions to verify the type of a user-supplied function argument.
    Contributed by Mike Orr.


Cheetah.Templates.SkeletonPage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


A stock template class that may be useful for web developers is
defined in the {Cheetah.Templates.SkeletonPage} module. The
{SkeletonPage} template class is generated from the following
Cheetah source code:

::

    ##doc-module: A Skeleton HTML page template, that provides basic structure and utility methods.
    ################################################################################
    #extends Cheetah.Templates._SkeletonPage
    #implements respond
    ################################################################################
    #cache id='header'
    $docType
    $htmlTag
    <!-- This document was autogenerated by Cheetah (https://cheetahtemplate.org/).
    Do not edit it directly!

    Copyright $currentYr - $siteCopyrightName - All Rights Reserved.
    Feel free to copy any javascript or html you like on this site,
    provided you remove all links and/or references to $siteDomainName
    However, please do not copy any content or images without permission.

    $siteCredits

    -->


    #block writeHeadTag
    <head>
    <title>$title</title>
    $metaTags
    $stylesheetTags
    $javascriptTags
    </head>
    #end block writeHeadTag

    #end cache header
    #################

    $bodyTag

    #block writeBody
    This skeleton page has no flesh. Its body needs to be implemented.
    #end block writeBody

    </body>
    </html>

You can redefine any of the blocks defined in this template by
writing a new template that {#extends} SkeletonPage. (As you
remember, using {#extends} makes your template implement the
{.writeBody()} method instead of {.respond()} - which happens to be
the same method SkeletonPage expects the page content to be (note
the writeBody block in SkeletonPage).)

::

    #def bodyContents
    Here's my new body. I've got some flesh on my bones now.
    #end def bodyContents

All of the $placeholders used in the {SkeletonPage} template
definition are attributes or methods of the {SkeletonPage} class.
You can reimplement them as you wish in your subclass. Please read
the source code of the file {Cheetah/Templates/\_SkeletonPage.py}
before doing so.

You'll need to understand how to use the following methods of the
{SkeletonPage} class: {$metaTags()}, {$stylesheetTags()},
{$javascriptTags()}, and {$bodyTag()}. They take the data you
define in various attributes and renders them into HTML tags.


-  { metaTags()} - Returns a formatted vesion of the
   self.\_metaTags dictionary, using the formatMetaTags function from
   {\_SkeletonPage.py}.

-  { stylesheetTags()} - Returns a formatted version of the
   {self.\_stylesheetLibs} and {self.\_stylesheets} dictionaries. The
   keys in {self.\_stylesheets} must be listed in the order that they
   should appear in the list {self.\_stylesheetsOrder}, to ensure that
   the style rules are defined in the correct order.

-  { javascriptTags()} - Returns a formatted version of the
   {self.\_javascriptTags} and {self.\_javascriptLibs} dictionaries.
   Each value in {self.\_javascriptTags} should be a either a code
   string to include, or a list containing the JavaScript version
   number and the code string. The keys can be anything. The same
   applies for {self.\_javascriptLibs}, but the string should be the
   SRC filename rather than a code string.

-  { bodyTag()} - Returns an HTML body tag from the entries in the
   dict {self.\_bodyTagAttribs}.


The class also provides some convenience methods that can be used
as $placeholders in your template definitions:


-  { imgTag(self, src, alt='', width=None, height=None, border=0)}
   - Dynamically generate an image tag. Cheetah will try to convert
   the "{src}" argument to a WebKit serverSidePath relative to the
   servlet's location. If width and height aren't specified they are
   calculated using PIL or ImageMagick if either of these tools are
   available. If all your images are stored in a certain directory you
   can reimplement this method to append that directory's path to the
   "{src}" argument. Doing so would also insulate your template
   definitions from changes in your directory structure.



