Cheetah vs. Other Template Engines
==================================


This appendix compares Cheetah with various other template/emdedded
scripting languages and Internet development frameworks. As Cheetah
is similar to Velocity at a superficial level, you may also wish to
read comparisons between Velocity and other languages at
http://jakarta.apache.org/velocity/ymtd/ymtd.html.

Which features are unique to Cheetah
------------------------------------



-  The { block framework} (section inheritanceEtc.block)

-  Cheetah's powerful yet simple { caching framework} (section
   output.caching)

-  Cheetah's { Unified Dotted Notation} and { autocalling}
   (sections language.namemapper.dict and
   language.namemapper.autocalling)

-  Cheetah's searchList (section language.searchList) information.

-  Cheetah's {#raw} directive (section output.raw)

-  Cheetah's {#slurp} directive (section output.slurp)

-  Cheetah's tight integration with Webware for Python (section
   webware)

-  Cheetah's { SkeletonPage framework} (section
   libraries.templates.skeletonPage)

-  Cheetah's ability to mix PSP-style code with Cheetah Language
   syntax (section tips.PSP) Because of Cheetah's design and Python's
   flexibility it is relatively easy to extend Cheetah's syntax with
   syntax elements from almost any other template or embedded
   scripting language.


Cheetah vs. Velocity
--------------------


For a basic introduction to Velocity, visit
http://jakarta.apache.org/velocity.

Velocity is a Java template engine. It's older than Cheetah, has a
larger user base, and has better examples and docs at the moment.
Cheetah, however, has a number of advantages over Velocity:


-  Cheetah is written in Python. Thus, it's easier to use and
   extend.

-  Cheetah's syntax is closer to Python's syntax than Velocity's is
   to Java's.

-  Cheetah has a powerful caching mechanism. Velocity has no
   equivalent.

-  It's far easier to add data/objects into the namespace where
   $placeholder values are extracted from in Cheetah. Velocity calls
   this namespace a 'context'. Contexts are dictionaries/hashtables.
   You can put anything you want into a context, BUT you have to use
   the .put() method to populate the context; e.g.,

   ::

       VelocityContext context1 = new VelocityContext();
       context1.put("name","Velocity");
       context1.put("project", "Jakarta");
       context1.put("duplicate", "I am in context1");

   Cheetah takes a different approach. Rather than require you to
   manually populate the 'namespace' like Velocity, Cheetah will
   accept any existing Python object or dictionary AS the 'namespace'.
   Furthermore, Cheetah allows you to specify a list namespaces that
   will be searched in sequence to find a varname-to-value mapping.
   This searchList can be extended at run-time.

   If you add a 'foo' object to the searchList and the 'foo' has an
   attribute called 'bar', you can simply type {$bar} in the template.
   If the second item in the searchList is dictionary 'foofoo'
   containing {{'spam':1234, 'parrot':666}}, Cheetah will first look
   in the 'foo' object for a 'spam' attribute. Not finding it, Cheetah
   will then go to 'foofoo' (the second element in the searchList) and
   look among its dictionary keys for 'spam'. Finding it, Cheetah will
   select {foofoo['spam']} as {$spam}'s value.

-  In Cheetah, the tokens that are used to signal the start of
   $placeholders and #directives are configurable. You can set them to
   any character sequences, not just $ and #.


Cheetah vs. WebMacro
--------------------


For a basic introduction to WebMacro, visit http://webmacro.org.

The points discussed in section comparisons.velocity also apply to
the comparison between Cheetah and WebMacro. For further
differences please refer to
http://jakarta.apache.org/velocity/differences.html.

Cheetah vs. Zope's DTML
-----------------------


For a basic introduction to DTML, visit
http://www.zope.org/Members/michel/ZB/DTML.dtml.


-  Cheetah is faster than DTML.

-  Cheetah does not use HTML-style tags; DTML does. Thus, Cheetah
   tags are visible in rendered HTML output if something goes wrong.

-  DTML can only be used with ZOPE for web development; Cheetah can
   be used as a standalone tool for any purpose.

-  Cheetah's documentation is more complete than DTML's.

-  Cheetah's learning curve is shorter than DTML's.

-  DTML has no equivalent of Cheetah's blocks, caching framework,
   unified dotted notation, and {#raw} directive.


Here are some examples of syntax differences between DTML and
Cheetah:

::

    <ul>
    <dtml-in frogQuery>
     <li><dtml-var animal_name></li>
    </dtml-in>
    </ul>

::

    <ul>
    #for $animal_name in $frogQuery
     <li>$animal_name</li>
    #end for
    </ul>

::

    <dtml-if expr="monkeys > monkey_limit">
      <p>There are too many monkeys!</p>
    <dtml-elif expr="monkeys < minimum_monkeys">
      <p>There aren't enough monkeys!</p>
    <dtml-else>
      <p>There are just enough monkeys.</p>
    </dtml-if>

::

    #if $monkeys > $monkey_limit
      <p>There are too many monkeys!</p>
    #else if $monkeys < $minimum_monkeys
      <p>There aren't enough monkeys!</p>
    #else
      <p>There are just enough monkeys.</p>
    #end if

::

    <table>
    <dtml-in expr="objectValues('File')">
      <dtml-if sequence-even>
        <tr bgcolor="grey">
      <dtml-else>
        <tr>
      </dtml-if>
      <td>
      <a href="&dtml-absolute_url;"><dtml-var title_or_id></a>
      </td></tr>
    </dtml-in>
    </table>

::

    <table>
    #set $evenRow = 0
    #for $file in $files('File')
      #if $evenRow
        <tr bgcolor="grey">
        #set $evenRow = 0
      #else
        <tr>
        #set $evenRow = 1
      #end if
      <td>
      <a href="$file.absolute_url">$file.title_or_id</a>
      </td></tr>
    #end for
    </table>

The last example changed the name of {$objectValues} to {$files}
because that's what a Cheetah developer would write. The developer
would be responsible for ensuring {$files} returned a list (or
tuple) of objects (or dictionaries) containing the attributes (or
methods or dictionary keys) 'absolute\_url' and 'title\_or\_id'.
All these names ('objectValues', 'absolute\_url' and
'title\_or\_id') are standard parts of Zope, but in Cheetah the
developer is in charge of writing them and giving them a reasonable
behaviour.

Some of DTML's features are being ported to Cheetah, such as
{Cheetah.Tools.MondoReport}, which is based on the {<dtml-in>} tag.
We are also planning an output filter as flexible as the
{<dtml-var>} formatting options. However, neither of these are
complete yet.

Cheetah vs. Zope Page Templates
-------------------------------


For a basic introduction to Zope Page Templates, please visit
http://www.zope.org/Documentation/Articles/ZPT2.

Cheetah vs. PHP's Smarty templates
----------------------------------


PHP (http://www.php.net/) is one of the few scripting languages
expressly designed for web servlets. However, it's also a
full-fledged programming language with libraries similar to
Python's and Perl's. The syntax and functions are like a cross
between Perl and C plus some original ideas (e.g.; a single array
type serves as both a list and a dictionary, ``$arr[]="value";``
appends to an array).

Smarty (http://smarty.php.net/) is an advanced template engine for
PHP. ({ Note:} this comparision is based on Smarty's on-line
documentation. The author has not used Smarty. Please send
corrections or ommissions to the Cheetah mailing list.) Like
Cheetah, Smarty:


-  compiles to the target programming language (PHP).

-  has configurable delimeters.

-  passes if-blocks directly to PHP, so you can use any PHP
   expression in them.

-  allows you to embed PHP code in a template.

-  has a caching framework (although it works quite differently).

-  can read the template definition from any arbitrary source.


Features Smarty has that Cheetah lacks:


-  Preprocessors, postprocessors and output filters. You can
   emulate a preprocessor in Cheetah by running your template
   definition through a filter program or function before Cheetah sees
   it. To emulate a postprocessor, run a .py template module through a
   filter program/function. To emulate a Smarty output filter, run the
   template output through a filter program/function. If you want to
   use "cheetah compile" or "cheetah fill" in a pipeline, use {-} as
   the input file name and {-stdout} to send the result to standard
   output. Note that Cheetah uses the term "output filter" differently
   than Smarty: Cheetah output filters ({#filter}) operate on
   placeholders, while Smarty output filters operate on the entire
   template output. There has been a proposed {#sed} directive that
   would operate on the entire output line by line, but it has not
   been implemented.

-  Variable modifiers. In some cases, Python has equivalent string
   methods ({.strip}, {.capitalize}, {.replace(SEARCH, REPL)}), but in
   other cases you must wrap the result in a function call or write a
   custom output filter ({#filter}).

-  Certain web-specific functions, which can be emulated with
   third-party functions.

-  The ability to "plug in" new directives in a modular way.
   Cheetah directives are tightly bound to the compiler. However,
   third-party { functions} can be freely imported and called from
   placeholders, and { methods} can be mixed in via {#extends}. Part
   of this is because Cheetah distinguishes between functions and
   directives, while Smarty treats them all as "functions". Cheetah's
   design does not allow functions to have flow control effect outside
   the function (e.g., {#if} and {#for}, which operate on template
   body lines), so directives like these cannot be encoded as
   functions.

-  Configuration variables read from an .ini-style file. The
   {Cheetah.SettingsManager} module can parse such a file, but you'd
   have to invoke it manually. (See the docstrings in the module for
   details.) In Smarty, this feature is used for multilingual
   applications. In Cheetah, the developers maintain that everybody
   has their own preferred way to do this (such as using Python's
   {gettext} module), and it's not worth blessing one particular
   strategy in Cheetah since it's easy enough to integrate third-party
   code around the template, or to add the resulting values to the
   searchList.


Features Cheetah has that Smarty lacks:


-  Saving the compilation result in a Python (PHP) module for quick
   reading later.

-  Caching individual placeholders or portions of a template.
   Smarty caches only the entire template output as a unit.


Comparisions of various Smarty constructs:

::

    {assign var="name" value="Bob"} (#set has better syntax in the author's opinion)
    counter   (looks like equivalent to #for)
    eval      (same as #include with variable)
    fetch: insert file content into output   (#include raw)
    fetch: insert URL content into output    (no euqivalent, user can write
         function calling urllib, call as $fetchURL('URL') )
    fetch: read file into variable  (no equivalent, user can write function
         based on the 'open/file' builtin, or on .getFileContents() in
         Template.)
    fetch: read URL content into variable  (no equivalent, use above
         function and call as:  #set $var = $fetchURL('URL')
    html_options: output an HTML option list  (no equivalent, user can
         write custom function.  Maybe FunFormKit can help.)
    html_select_date: output three dropdown controls to specify a date
         (no equivalent, user can write custom function)
    html_select_time: output four dropdown controls to specify a time
         (no equvalent, user can write custom function)
    math: eval calculation and output result   (same as #echo)
    math: eval calculation and assign to variable  (same as #set)
    popup_init: library for popup windows  (no equivalent, user can write
         custom method outputting Javascript)


    Other commands:
    capture   (no equivalent, collects output into variable.  A Python
         program would create a StringIO instance, set sys.stdout to
         it temporarily, print the output, set sys.stdout back, then use
         .getvalue() to get the result.)
    config_load   (roughly analagous to #settings, which was removed
         from Cheetah.  Use Cheetah.SettingsManager manually or write
         a custom function.)
    include   (same as #include, but can include into variable.
         Variables are apparently shared between parent and child.)
    include_php: include a PHP script (e.g., functions)
         (use #extends or #import instead)
    insert   (same as #include not in a #cache region)
    {ldelim}{rdelim}   (escape literal $ and # with a backslash,
         use #compiler-settings to change the delimeters)
    literal  (#raw)
    php    (``<% %>'' tags)
    section  (#for $i in $range(...) )
    foreach  (#for)
    strip   (like the #sed tag which was never implemented.  Strips
         leading/trailing whitespace from lines, joins several lines
         together.)


    Variable modifiers:
    capitalize    ( $STRING.capitalize() )
    count_characters    (   $len(STRING)  )
    count_paragraphs/sentances/words   (no equivalent, user can write function)
    date_format    (use 'time' module or download Egenix's mx.DateTime)
    default    ($getVar('varName', 'default value') )
    escape: url encode    ($urllib.quote_plus(VALUE) )
    escape: hex encode   (no equivalent?  user can write function)
    escape: hex entity encode  (no equivalent?  user can write function)
    indent: indent all lines of a var's output  (may be part of future
         #indent directive)
    lower    ($STRING.lower() )
    regex_replace   ('re' module)
    replace    ($STRING.replace(OLD, NEW, MAXSPLIT) )
    spacify   (#echo "SEPARATOR".join(SEQUENCE) )
    string_format   (#echo "%.2f" % FLOAT , etc.)
    strip_tags  (no equivalent, user can write function to strip HTML tags,
         or customize the WebSafe filter)
    truncate   (no equivalent, user can write function)
    upper   ($STRING.upper() )
    wordwrap  ('writer' module, or a new module coming in Python 2.3)

Some of these modifiers could be added to the super output filter
we want to write someday.

Cheetah vs. PHPLib's Template class
-----------------------------------


PHPLib ((http://phplib.netuse.de/) is a collection of classes for
various web objects (authentication, shopping cart, sessions, etc),
but what we're interested in is the {Template} object. It's much
more primitive than Smarty, and was based on an old Perl template
class. In fact, one of the precursors to Cheetah was based on it
too. Differences from Cheetah:


-  Templates consist of text with {{placeholders}} in braces.

-  Instead of a searchList, there is one flat namespace. Every
   variable must be assigned via the {set\_var} method. However, you
   can pass this method an array (dictionary) of several variables at
   once.

-  You cannot embed lookups or calculations into the template.
   Every placeholder must be an exact variable name.

-  There are no directives. You must do all display logic (if, for,
   etc) in the calling routine.

-  There is, however, a "block" construct. A block is a portion of
   text between the comment markers {<!- BEGIN blockName -> ... <!-
   END blockName>}. The {set\_block} method extracts this text into a
   namespace variable and puts a placeholder referring to it in the
   template. This has a few parallels with Cheetah's {#block}
   directive but is overall quite different.

-  To do the equivalent of {#if}, extract the block. Then if true,
   do nothing. If false, assign the empty string to the namespace
   variable.

-  To do the equivalent of {#for}, extract the block. Set any
   namespace variables needed inside the loop. To parse one iteration,
   use the {parse} method to fill the block variable (a mini-template)
   into another namespace variable, appending to it. Refresh the
   namespace variables needed inside the loop and parse again; repeat
   for each iteration. You'll end up with a mini-result that will be
   plugged into the main template's placeholder.

-  To read a template definition from a file, use the {set\_file}
   method. This places the file's content in a namespace variable. To
   read a template definition from a string, assign it to a namespace
   variable.

-  Thus, for complicated templates, you are doing a lot of
   recursive block filling and file reading and parsing mini-templates
   all into one flat namespace as you finally build up values for the
   main template. In Cheetah, all this display logic can be embedded
   into the template using directives, calling out to Python methods
   for the more complicated tasks.

-  Although you can nest blocks in the template, it becomes tedious
   and arguably hard to read, because all blocks have identical
   syntax. Unless you choose your block names carefully and put
   comments around them, it's hard to tell which blocks are if-blocks
   and which are for-blocks, or what their nesting order is.

-  PHPLib templates do not have caching, output filters, etc.


Cheetah vs. PSP, PHP, ASP, JSP, Embperl, etc.
---------------------------------------------


Webware's PSP Component
    - http://webware.sourceforge.net/Webware/PSP/Docs/

Tomcat JSP Information
    - http://jakarta.apache.org/tomcat/index.html

ASP Information at ASP101
    - http://www.asp101.com/

Embperl
    - http://perl.apache.org/embperl/


Here's a basic Cheetah example:

::

    <TABLE>
    #for $client in $service.clients
    <TR>
    <TD>$client.surname, $client.firstname</TD>
    <TD><A HREF="mailto:$client.email" >$client.email</A></TD>
    </TR>
    #end for
    </TABLE>

Compare this with PSP:

::

    <TABLE>
    <% for client in service.clients(): %>
    <TR>
    <TD><%=client.surname()%>, <%=client.firstname()%></TD>
    <TD><A HREF="mailto:<%=client.email()%>"><%=client.email()%></A></TD>
    </TR>
    <%end%>
    </TABLE>


