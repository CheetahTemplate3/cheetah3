non-Webware HTML output
=======================


Cheetah can be used with all types of HTML output, not just with
Webware.

Static HTML Pages
-----------------


Some sites like Linux Gazette (http://www.linuxgazette.com/)
require completely static pages because they are mirrored on
servers running completely different software from the main site.
Even dynamic sites may have one or two pages that are static for
whatever reason, and the site administrator may wish to generate
those pages from Cheetah templates.

There's nothing special here. Just create your templates as usual.
Then compile and fill them whenever the template definition
changes, and fill them again whenever the placeholder values
change. You may need an extra step to copy the .html files to their
final location. A Makefile (chapter tips.Makefile) can help
encapsulate these steps.


