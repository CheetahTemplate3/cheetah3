import gettext
_ = gettext.gettext


class I18n(object):
    def __init__(self, parser):
        pass

    def __call__(self,
                 src,  # aka message,
                 plural=None,
                 # should be a string representing the name of the '$var'
                 # rather than $var itself
                 n=None,
                 id=None,
                 domain=None,
                 source=None,
                 target=None,
                 comment=None,

                 # args that are automatically supplied by the parser when the
                 # macro is called:
                 parser=None,
                 macros=None,
                 isShortForm=False,
                 EOLCharsInShortForm=None,
                 startPos=None,
                 endPos=None,
                 ):
        """This is just a stub at this time.

           plural = the plural form of the message
           n = a sized argument to distinguish between single and plural forms

           id = msgid in the translation catalog
           domain = translation domain
           source = source lang
           target = a specific target lang
           comment = a comment to the translation team

        See the following for some ideas
        http://www.zope.org/DevHome/Wikis/DevSite/Projects/ComponentArchitecture/ZPTInternationalizationSupport

        Other notes:
        - There is no need to replicate the i18n:name attribute
          from plone/PTL, as cheetah placeholders serve the same purpose.
       """

        # print macros['i18n']
        src = _(src)
        if isShortForm and endPos < len(parser):
            return src + EOLCharsInShortForm
        else:
            return src
