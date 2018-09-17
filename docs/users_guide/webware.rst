Using Cheetah with Webware
==========================


{ Webware for Python} is a 'Python-Powered Internet Platform' that
runs servlets in a manner similar to Java servlets. { WebKit} is
the name of Webware's application server. For more details, please
visit https://cito.github.io/w4py/.

All comments below refer to the official version of Webware, the
DamnSimple! offshoot at ?, and the now-abandoned
WebwareExperimental implementation at
http://sourceforge.net/projects/expwebware/, except where noted.
All the implementations are 95% identical to the servlet writer:
their differences lie in their internal structure and configuration
files. One difference is that the executable you run to launch
standard Webware is called {AppServer}, whereas in
WebwareExperimental it's called {webkit}. But to servlets they're
both "WebKit, Webware's application server", so it's one half dozen
to the other. In this document, we generally use the term { WebKit}
to refer to the currently-running application server.

Installing Cheetah on a Webware system
--------------------------------------


Install Cheetah after you have installed Webware, following the
instructions in chapter gettingStarted.

The standard Cheetah test suite ('cheetah test') does not test
Webware features. We plan to build a test suite that can run as a
Webware servlet, containing Webware-specific tests, but that has
not been built yet. In the meantime, you can make a simple template
containing something like "This is a very small template.", compile
it, put the \*.py template module in a servlet directory, and see
if Webware serves it up OK.

{ You must not have a Webware context called "Cheetah".} If you do,
Webware will mistake that directory for the Cheetah module
directory, and all template-servlets will bomb out with a
"ImportError: no module named Template". (This applies only to the
standard Webware; WebwareExperimental does not have contexts.)

If Webware complains that it cannot find your servlet, make sure
'.tmpl' is listed in 'ExtensionsToIgnore' in your
'Application.config' file.

Containment vs Inheritance
--------------------------


Because Cheetah's core is flexible, there are many ways to
integrate it with Webware servlets. There are two broad strategies:
the { Inheritance approach} and the { Containment approach}. The
difference is that in the Inheritance approach, your template
object { is} the servlet, whereas in the Containment approach, the
servlet is not a template but merely { uses} template(s) for
portion(s) of its work.

The Inheritance approach is recommended for new sites because it's
simpler, and because it scales well for large sites with a
site->section->subsection->servlet hierarchy. The Containment
approach is better for existing servlets that you don't want to
restructure. For instance, you can use the Containment approach to
embed a discussion-forum table at the bottom of a web page.

However, most people who use Cheetah extensively seem to prefer the
Inheritance approach because even the most analytical servlet needs
to produce { some} output, and it has to fit the site's look and
feel { anyway}, so you may as well use a template-servlet as the
place to put the output. Especially since it's so easy to add a
template-servlet to a site once the framework is established. So we
recommend you at least evaluate the effort that would be required
to convert your site framework to template superclasses as
described below, vs the greater flexibility and manageability it
might give the site over the long term. You don't necessarily have
to convert all your existing servlets right away: just build common
site templates that are visually and behaviorally compatible with
your specification, and use them for new servlets. Existing
servlets can be converted later, if at all.

Edmund Liam is preparing a section on a hybrid approach, in which
the servlet is not a template, but still calls template(s) in an
inheritance chain to produce the output. The advantage of this
approach is that you aren't dealing with {Template} methods and
Webware methods in the same object.

The Containment Approach
~~~~~~~~~~~~~~~~~~~~~~~~


In the Containment approach, your servlet is not a template.
Instead, it it makes its own arrangements to create and use
template object(s) for whatever it needs. The servlet must
explicitly call the template objects' {.respond()} (or
{.\_\_str\_\_()}) method each time it needs to fill the template.
This does not present the output to the user; it merely gives the
output to the servlet. The servlet then calls its
{#self.response().write()} method to send the output to the user.

The developer has several choices for managing her templates. She
can store the template definition in a string, file or database and
call {Cheetah.Template.Template} manually on it. Or she can put the
template definition in a \*.tmpl file and use { cheetah compile}
(section howWorks.cheetah-compile) to convert it to a Python class
in a \*.py module, and then import it into her servlet.

Because template objects are not thread safe, you should not store
one in a module variable and allow multiple servlets to fill it
simultaneously. Instead, each servlet should instantiate its own
template object. Template { classes}, however, are thread safe,
since they don't change once created. So it's safe to store a
template class in a module global variable.

The Inheritance Approach
~~~~~~~~~~~~~~~~~~~~~~~~


In the Inheritance approach, your template object doubles as as
Webware servlet, thus these are sometimes called {
template-servlets}. { cheetah compile} (section
howWorks.cheetah-compile) automatically creates modules containing
valid Webware servlets. A servlet is a subclass of Webware's
{WebKit.HTTPServlet} class, contained in a module with the same
name as the servlet. WebKit uses the request URL to find the
module, and then instantiates the servlet/template. The servlet
must have a {.respond()} method (or {.respondToGet()},
{.respondToPut()}, etc., but the Cheetah default is {.respond()}).
Servlets created by {cheetah compile} meet all these requirements.

(Cheetah has a Webware plugin that automatically converts a {.tmpl
servlet file} into a {.py servlet file} when the {.tmpl servlet
file} is requested by a browser. However, that plugin is currently
unavailable because it's being redesigned. For now, use {cheetah
compile} instead.)

What about logic code? Cheetah promises to keep content (the
placeholder values), graphic design (the template definition and is
display logic), and algorithmic logic (complex calculations and
side effects) separate. How? Where do you do form processing?

The answer is that your template class can inherit from a pure
Python class containing the analytical logic. You can either use
the {#extends} directive in Cheetah to indicate the superclass(es),
or write a Python {class} statement to do the same thing. See the
template {Cheetah.Templates.SkeletonPage.tmpl} and its pure Python
class {Cheetah.Templates.\_SkeletonPage.py} for an example of a
template inheriting logic code. (See sections
inheritanceEtc.extends and inheritanceEtc.implements for more
information about {#extends} and {#implements}. They have to be
used a certain right way.)

If {#WebKit.HTTPServlet} is not available, Cheetah fakes it with a
dummy class to satisfy the dependency. This allows servlets to be
tested on the command line even on systems where Webware is not
installed. This works only with servlets that don't call back into
WebKit for information about the current web transaction, since
there is no web transaction. Trying to access form input, for
instance, will raise an exception because it depends on a live web
request object, and in the dummy class the request object is
{None}.

Because Webware servlets must be valid Python modules, and
"cheetah compile" can produce only valid module names, if you're
converting an existing site that has .html filenames with hyphens
(-), extra dots (.), etc, you'll have to rename them (and possibly
use redirects).

Site frameworks
---------------


Web sites are normally arranged hierarchically, with certain
features common to every page on the site, other features common to
certain sections or subsections, and others unique to each page.
You can model this easily with a hierarchy of classes, with
specific servlets inheriting from their more general superclasses.
Again, you can do this two ways, using Cheetah's { Containment}
approach or { Inheritance} approach.

In the Inheritance approach, parents provide {#block}s and children
override them using {#def}. Each child {#extend}s its immediate
parent. Only the leaf servlets need to be under WebKit's document
root directory. The superclass servlets can live anywhere in the
filesystem that's in the Python path. (You may want to modify your
WebKit startup script to add that library directory to your
{PYTHONPATH} before starting WebKit.)

Section libraries.templates.skeletonPage contains information on a
stock template that simplifies defining the basic HTML structure of
your web page templates.

In the Containment approach, your hierarchy of servlets are not
templates, but each uses one or more templates as it wishes.
Children provide callback methods to to produce the various
portions of the page that are their responsibility, and parents
call those methods. Webware's {WebKit.Page} and
{WebKit.SidebarPage} classes operate like this.

Note that the two approaches are not compatible! {WebKit.Page} was
not designed to intermix with {Cheetah.Templates.SkeletonPage}.
Choose either one or the other, or expect to do some integration
work.

If you come up with a different strategy you think is worth noting
in this chapter, let us know.

Directory structure
-------------------


Here's one way to organize your files for Webware+Cheetah.

::

    www/                         # Web root directory.
        site1.example.com/       # Site subdirectory.
            apache/              # Web server document root (for non-servlets).
            www/                 # WebKit document root.
               index.py          # http://site1.example.com/
               index.tmpl        # Source for above.
               servlet2.py       # http://site1.example.com/servlet2
               servlet2.tmpl     # Source for above.
            lib/                 # Directory for helper classes.
               Site.py           # Site superclass ("#extends Site").
               Site.tmpl         # Source for above.
               Logic.py          # Logic class inherited by some template.
            webkit.config        # Configuration file (for WebwareExperimental).
            Webware/             # Standard Webware's MakeAppWorkDir directory.
               AppServer         # Startup program (for standard Webware).
               Configs/          # Configuration directory (for standard Webware).
                   Application.config
                                 # Configuration file (for standard Webware).
        site2.example.org/       # Another virtual host on this computer....

Initializing your template-servlet with Python code
---------------------------------------------------


If you need a place to initialize variables or do calculations for
your template-servlet, you can put it in an {.awake()} method
because WebKit automatically calls that early when processing the
web transaction. If you do override {.awake()}, be sure to call the
superclass {.awake} method. You probably want to do that first so
that you have access to the web transaction data {Servlet.awake}
provides. You don't have to worry about whether your parent class
has its own {.awake} method, just call it anyway, and somebody up
the inheritance chain will respond, or at minimum {Servlet.awake}
will respond. Section tips.callingSuperclassMethods gives examples
of how to call a superclass method.

As an alternative, you can put all your calculations in your own
method and call it near the top of your template. ({#silent},
section output.silent).

Form processing
---------------


There are many ways to display and process HTML forms with Cheetah.
But basically, all form processing involves two steps.


#. Display the form.

#. In the next web request, read the parameters the user submitted,
   check for user errors, perform any side effects (e.g.,
   reading/writing a database or session data) and present the user an
   HTML response or another form.


The second step may involve choosing between several templates to
fill (or several servlets to redirect to), or a big
if-elif-elif-else construct to display a different portion of the
template depending on the situation.

In the oldest web applications, step 1 and step 2 were handled by
separate objects. Step 1 was a static HTML file, and step 2 was a
CGI script. Frequently, a better strategy is to have a single
servlet handle both steps. That way, the servlet has better control
over the entire situation, and if the user submits unacceptable
data, the servlet can redisplay the form with a "try again" error
message at the top and and all the previous input filled in. The
servlet can use the presence or absence of certain CGI parameters
(e.g., the submit button, or a hidden mode field) to determine
which step to take.

One neat way to build a servlet that can handle both the form
displaying and form processing is like this:


#. Put your form HTML into an ordinary template-servlet. In each
   input field, use a placeholder for the value of the {VALUE=}
   attribue. Place another placeholder next to each field, for that
   field's error message.

#. Above the form, put a {$processFormData} method call.

#. Define that method in a Python class your template {#extend}s.
   (Or if it's a simple method, you can define it in a {#def}.) The
   method should:


   #. Get the form input if any.

   #. If the input variable corresponding to the submit field is
      empty, there is no form input, so we're showing the form for the
      first time. Initialize all VALUE= variables to their default value
      (usually ""), and all error variables to "". Return "", which will
      be the value for {$processFormData}.

   #. If the submit variable is not empty, fill the VALUE= variables
      with the input data the user just submitted.

   #. Now check the input for errors and put error messages in the
      error placeholders.

   #. If there were any user errors, return a general error message
      string; this will be the value for {$processFormData}.

   #. If there were no errors, do whatever the form's job is (e.g.,
      update a database) and return a success message; this will be the
      value for {$processFormData}.


#. The top of the page will show your success/failure message (or
   nothing the first time around), with the form below. If there are
   errors, the user will have a chance to correct them. After a
   successful submit, the form will appear again, so the user can
   either review their entry, or change it and submit it again.
   Depending on the application, this may make the servlet update the
   same database record again, or it may generate a new record.


{FunFormKit} is a third-party Webware package that makes it easier
to produce forms and handle their logic. It has been successfully
been used with Cheetah. You can download FunFormKit from
http://colorstudy.net/software/funformkit/ and try it out for
yourself.

Form input, cookies, session variables and web server variables
---------------------------------------------------------------


General variable tips that also apply to servlets are in section
tips.placeholder.

To look up a CGI GET or POST parameter (with POST overriding):

::

    $request.field('myField')
    self.request().field('myField')

These will fail if Webware is not available, because {$request}
(aka {self.request()} will be {None} rather than a Webware
{WebKit.Request} object. If you plan to read a lot of CGI
parameters, you may want to put the {.fields} method into a local
variable for convenience:

::

    #set $fields = $request.fields
    $fields.myField

But remember to do complicated calculations in Python, and assign
the results to simple variables in the searchList for display.
These {$request} forms are useful only for occasions where you just
need one or two simple request items that going to Python for would
be overkill.

To get a cookie or session parameter, subsitute "cookie" or
"session" for "field" above. To get a dictionary of all CGI
parameters, substitute "fields" (ditto for "cookies"). To verify a
field exists, substitute "hasField" (ditto for "hasCookie").

Other useful request goodies:

::

    ## Defined in WebKit.Request
    $request.field('myField', 'default value')
    $request.time              ## Time this request began in Unix ticks.
    $request.timeStamp         ## Time in human-readable format ('asctime' format).
    ## Defined in WebKit.HTTPRequest
    $request.hasField.myField  ## Is a CGI parameter defined?
    $request.fields            ## Dictionary of all CGI parameters.
    $request.cookie.myCookie   ## A cookie parameter (also .hasCookie, .cookies).
    $request.value.myValue     ## A field or cookie variable (field overrides)
                               ## (also .hasValue).
    $request.session.mySessionVar  # A session variable.
    $request.extraURLPath      ## URL path components to right of servlet, if any.
    $request.serverDictionary  ## Dict of environmental vars from web server.
    $request.remoteUser        ## Authenticated username.  HTTPRequest.py source
                               ## suggests this is broken and always returns None.
    $request.remoteAddress  ## User's IP address (string).
    $request.remoteName     ## User's domain name, or IP address if none.
    $request.urlPath        ## URI of this servlet.
    $request.urlPathDir     ## URI of the directory containing this servlet.
    $request.serverSidePath ## Absolute path of this servlet on local filesystem.
    $request.serverURL      ## URL of this servlet, without "http://" prefix,
                            ## extra path info or query string.
    $request.serverURLDir   ## URL of this servlet's directory, without "http://".
    $log("message")         ## Put a message in the Webware server log.  (If you
                            ## define your own 'log' variable, it will override
                            ## this; use $self.log("message") in that case.

.webInput()
~~~~~~~~~~~


From the method docstring:

::

        def webInput(self, names, namesMulti=(), default='', src='f',
            defaultInt=0, defaultFloat=0.00, badInt=0, badFloat=0.00, debug=False):

    This method places the specified GET/POST fields, cookies or session variables
    into a dictionary, which is both returned and put at the beginning of the
    searchList.  It handles:
        * single vs multiple values
        * conversion to integer or float for specified names
        * default values/exceptions for missing or bad values
        * printing a snapshot of all values retrieved for debugging
    All the 'default*' and 'bad*' arguments have "use or raise" behavior, meaning
    that if they're a subclass of Exception, they're raised.  If they're anything
    else, that value is substituted for the missing/bad value.

    The simplest usage is:

        #silent $webInput(['choice'])
        $choice

        dic = self.webInput(['choice'])
        write(dic['choice'])

    Both these examples retrieves the GET/POST field 'choice' and print it.  If you
    leave off the "#silent", all the values would be printed too.  But a better way
    to preview the values is

        #silent $webInput(['name'], $debug=1)

    because this pretty-prints all the values inside HTML <PRE> tags.

    Since we didn't specify any coversions, the value is a string.  It's a "single"
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
    on a form, and the user chose "Monday", "Tuesday" and "Thursday".

        #silent $webInput([], ['days'])
        The days you chose are: #slurp
        #for $day in $days
        $day #slurp
        #end for

        dic = self.webInput([], ['days'])
        write("The days you chose are: ")
        for day in dic['days']:
            write(day + " ")

    Both these examples print:  "The days you chose are: Monday Tuesday Thursday".

    By default, missing strings are replaced by "" and missing/bad numbers by zero.
    (A "bad number" means the converter raised an exception for it, usually because
    of non-numeric characters in the value.)  This mimics Perl/PHP behavior, and
    simplifies coding for many applications where missing/bad values *should* be
    blank/zero.  In those relatively few cases where you must distinguish between
    ""/zero on the one hand and missing/bad on the other, change the appropriate
    'default*' and 'bad*' arguments to something like:
        * None
        * another constant value
        * $NonNumericInputError/self.NonNumericInputError
        * $ValueError/ValueError
    (NonNumericInputError is defined in this class and is useful for
    distinguishing between bad input vs a TypeError/ValueError
    thrown for some other reason.)

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
            if   not on and day in wantedDays:
                self.TurnOn(day)
                # ... Set a flag or insert a database record ...
            elif on and day not in wantedDays:
                self.TurnOff(day)
                # ... Unset a flag or delete a database record ...

    'source' allows you to look up the variables from a number of different
    sources:
        'f'   fields (CGI GET/POST parameters)
        'c'   cookies
        's'   session variables
        'v'   "values", meaning fields or cookies

    In many forms, you're dealing only with strings, which is why the
    'default' argument is third and the numeric arguments are banished to
    the end.  But sometimes you want automatic number conversion, so that
    you can do numeric comparisons in your templates without having to
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
        write("%s is %s cm tall." % (name, height))
        if height > 300:
            write("Wow, you're tall!")
        else:
            write("Pshaw, you're short.")

    To convert a value to a number, suffix ":int" or ":float" to the name.  The
    method will search first for a "height:int" variable and then for a "height"
    variable.  (It will be called "height" in the final dictionary.)  If a numeric
    conversion fails, use or raise 'badInt' or 'badFloat'.  Missing values work
    the same way as for strings, except the default is 'defaultInt' or
    'defaultFloat' instead of 'default'.

    If a name represents an uploaded file, the entire file will be read into
    memory.  For more sophisticated file-upload handling, leave that name out of
    the list and do your own handling, or wait for Cheetah.Utils.UploadFileMixin.

    This mixin class works only in a subclass that also inherits from
    Webware's Servlet or HTTPServlet.  Otherwise you'll get an AttributeError
    on 'self.request'.

    EXCEPTIONS: ValueError if 'source' is not one of the stated characters.
    TypeError if a conversion suffix is not ":int" or ":float".

More examples
-------------


Example A - a standalone servlet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Example B - a servlet under a site framework
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Example C - several servlets with a common template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Other Tips
----------


If your servlet accesses external files (e.g., via an {#include}
directive), remember that the current directory is not necessarily
directory the servlet is in. It's probably some other directory
WebKit chose. To find a file relative to the servlet's directory,
prefix the path with whatever {self.serverSidePath()} returns (from
{Servlet.serverSidePath()}.

If you don't understand how {#extends} and {#implements} work, and
about a template's main method, read the chapter on inheritance
(sections inheritanceEtc.extends and inheritanceEtc.implements).
This may help you avoid buggy servlets.


