Vocabulary
==========

(glossary) (vocabulary)

{ Template} is an informal term meaning a template definition, a
template instance or a template class. A { template definition} is
what the human { template maintainer} writes: a string consisting
of text, placeholders and directives. { Placeholders} are variables
that will be looked up when the template is filled. { Directives}
are commands to be executed when the template is filled, or
instructions to the Cheetah compiler. The conventional suffix for a
file containing a template definition is { .tmpl}.

There are two things you can do with a template: compile it or fill
it. { Filling} is the reason you have a template in the first
place: to get a finished string out of it. Compiling is a necessary
prerequisite: the { Cheetah compiler} takes a template definition
and produces Python code to create the finished string. Cheetah
provides several ways to compile and fill templates, either as one
step or two.

Cheetah's compiler produces a subclass of {Cheetah.Template}
specific to that template definition; this is called the {
generated class}. A { template instance} is an instance of a
generated class.

If the user calls the {Template} constructor directly (rather than
a subclass constructor), s/he will get what appears to be an
instance of {Template} but is actually a subclass created
on-the-fly.

The user can make the subclass explicit by using the
"cheetah compile" command to write the template class to a Python
module. Such a module is called a { .py template module}.

The { Template Definition Language} - or the "Cheetah language" for
short - is the syntax rules governing placeholders and directives.
These are discussed in sections language and following in this
Guide.

To fill a template, you call its { main method}. This is normally
{.respond()}, but it may be something else, and you can use the
{#implements} directive to choose the method name. (Section
inheritanceEtc.implements.

A { template-servlet} is a .py template module in a Webware servlet
directory. Such templates can be filled directly through the web by
requesting the URL. "Template-servlet" can also refer to the
instance being filled by a particular web request. If a Webware
servlet that is not a template-servlet invokes a template, that
template is not a template-servlet either.

A { placeholder tag} is the substring in the template definition
that is the placeholder, including the start and end delimeters (if
there is an end delimeter). The { placeholder name} is the same but
without the delimeters.

Placeholders consist of one or more { identifiers} separated by
periods (e.g., {a.b}). Each identifier must follow the same rules
as Python identifiers; that is, a letter or underscore followed by
one or more letters, digits or underscores. (This is the regular
expression ``[A-Za-z_][A-Za-z0-9_]*``.)

The first (or only) identifier of a placeholder name represents a {
variable} to be looked up. Cheetah looks up variables in various {
namespaces}: the searchList, local variables, and certain other
places. The searchList is a list of objects ({ containers}) with
attributes and/or keys: each container is a namespace. Every
template instance has exactly one searchList. Identifiers after the
first are looked up only in the parent object. The final value
after all lookups have been performed is the { placeholder value}.

Placeholders may occur in three positions: top-level, expression
and LVALUE. { Top-level} placeholders are those in ordinary text
("top-level text"). { Expression} placeholders are those in Python
expressions. { LVALUE} placeholders are those naming a variable to
receive a value. (LVALUE is computerese for
"the left side of the equal sign".) Section
language.placeholders.positions explains the differences between
these three positions.

The routine that does the placeholder lookups is called the {
NameMapper}. Cheetah's NameMapper supports universal dotted
notation and autocalling. { Universal dotted notation} means that
keys may be written as if they were attributes: {a.b} instead of
{a['b']}. { Autocalling} means that if any identifier's value is
found to be a function or method, Cheetah will call it without
arguments if there is no ``()`` following. More about the
NameMapper is in section language.namemapper.

Some directives are multi-line, meaning they have a matching {
#end} tag. The lines of text between the start and end tags is the
{ body} of the directive. Arguments on the same line as the start
tag, in contrast, are considered part of the directive tag. More
details are in section language.directives.syntax (Directive Syntax
Rules).


