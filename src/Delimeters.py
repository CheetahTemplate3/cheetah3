#!/usr/bin/env python
# $Id: Delimeters.py,v 1.3 2001/06/28 19:10:59 echuck Exp $
"""A dictionary of delimeter regular expressions that are used in Cheetah

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.3 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/06/28 19:10:59 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.3 $"[11:-2]


##################################################
## DEPENDENCIES ##

import re

##################################################
### CONSTANTS & GLOBALS ###

escCharLookBehind = r'(?:(?<=\A)|(?<!\\))'
tagClosure = r'(?:/#|\r\n|\n|\r)'
lazyTagClosure = r'(?:/#|\r\n|\n|\r)'

delimeters = {
    '[%,%]':re.compile(r"\[%(.+?)%\]",re.DOTALL),
    '{,}':re.compile(r"{(.+?)}",re.DOTALL),

    '<%,%>':{'start': r'<%',
             'startEscaped': r'<\%',
             'end': r'%>',
             'endEscaped': r'\%>',
             'placeholderRE': re.compile(r"<%(.+?)%>",re.DOTALL)
             },

    '<#,#>':{'start': r'<#',
             'startEscaped': r'\<#',
             'end': r'#>',
             'endEscaped': r'\#>',
             'placeholderRE': re.compile(r"<#(.*?)#>",re.DOTALL)
             },


    # the suffix _gobbleWS stands for gobble whitespace - any directive on a
    # line by itself will have all preceeding and trailing WS on that line
    # gobbled up with the directive

    'slurpDirective_gobbleWS': re.compile(r'(?:\A|^)[\t ]*#slurp[\t ]*' +
                                            r'(?:\r\n|\n|\r|\Z)',
                                            re.MULTILINE),
    'slurpDirective': re.compile(escCharLookBehind + r'#slurp[\t ]*(?:\r\n|\n|\r|\Z)'),

    'singleLineComment':re.compile(r'(?:\A|^)[\t ]*##(.*?)\n|' +
                                   escCharLookBehind + r'##(.*?)$', #this one doesn't gobble the \n !!!
                                   re.MULTILINE),

    'multiLineComment': re.compile(escCharLookBehind + r'#\*' +
                                   r'(.*?)' +
                                   r'\*#',
                                   re.DOTALL | re.MULTILINE),

    'displayLogic_gobbleWS': re.compile(r'(?:\A|^)[\t ]*#(' +
                                        r'if[\t ]+[^(?:/#)]+?|' +
                                        r'else[\t ]*?|' +
                                        r'else[\t ]if[\t ]+[^(?:/#)]+?|' +
                                        r'elif[\t ]+[^(?:/#)]+?|' +
                                        r'for[\t ][^(?:/#)]+?|' +
                                        r'end if|' +
                                        r'end for|' +
                                        r')[\t ]*(?:\r\n|\n|\r|\Z)',
                                        re.MULTILINE
                                        ),
    'displayLogic': re.compile(escCharLookBehind + r'#(' +
                               r'if[\t ]+.+?|' +
                               r'else[\t ]*?|' +
                               r'else[\t ]if[\t ]+.+?|' +
                               r'elif[\t ]+.+?|' +
                               r'for[\t ].+?|' +
                               r'end if|' +
                               r'end for|' +
                               r')[\t ]*(?:/#|\r\n|\n|\r|\Z)',
                               re.MULTILINE
                               ),

    'setDirective': re.compile(escCharLookBehind +
                               r'#set[\t ]+(.+?)(?:/#|\r\n|\n|\r|\Z)'),


    'cacheDirectiveStartTag': re.compile(escCharLookBehind +
                                         r'#cache(.*?)(?:/#|\r\n|\n|\r|\Z)'),

    'cacheDirectiveEndTag': re.compile(escCharLookBehind +
                                       r'#end cache(.*?)(?:/#|\r\n|\n|\r|\Z)'),

    ## The following directive delimeters are not intended to be used in the same manner
    # as the rest of the delim structs above. The placeholderRE is the only item of
    # interest here as they are only used in the pre/post-processing stages.

    'includeDirective_gobbleWS': re.compile(r'(?:\A|^)[\t ]*#include[\t ]+' +
                                            r'([^(?:/#)]+?)(?:\r\n|\n|\r|\Z)',
                                            re.MULTILINE),
    'includeDirective': re.compile(escCharLookBehind +
                                   r'#include[\t ]+(.+?)(?:/#|\r\n|\n|\r|\Z)'),


    ## no gobbleWS for stop and restart directives!!!
    # manage this explicitly if you need
    'rawDirective': re.compile(escCharLookBehind + r'#raw[\t ]*(?:/#|\r\n|\n|\r|\Z)(.*?)' +
                                r'(?:(?:#end raw[\t ]*(?:/#|\r\n|\n|\r))|\Z)',
                                re.DOTALL),

    ## there is also no gobbleWS for macro defs.
    # They must be on lines by themselves!!!
    # @@doc this
    'macroDirective': re.compile(r'(?:\A|^)[\t ]*#macro[\t ]+' +
                                 r'(.+?)(?:/#|\r\n|\n|\r)(.*?)' +
                                 r'(?:\r\n|\n|\r)[\t ]*#end macro[\t ]*(?:\r\n|\n|\r|\Z)',
                                 re.DOTALL | re.MULTILINE),

    # macroCalls should NOT gobbleWS - so that's why there aren't gobbleWS version

    'callMacro': re.compile(escCharLookBehind + r'#callMacro[\t ]+' +
                            r'(?P<macroName>[A-Za-z_][A-Za-z_0-9]*?)' +
                            r'\((?P<argString>.*?)\)[\t ]*(?:/#|\r\n|\n|\r)' +
                            r'(?P<extendedArgString>.*?)' +
                            r'#end callMacro[\t ]*(?:/#|\r\n|\n|\r|\Z)',
                            re.DOTALL | re.MULTILINE),

    'callMacroArgs': re.compile(r'#arg[\t ]+' +
                                r'(?P<argName>[A-Za-z_][A-Za-z_0-9]*?)' +
                                r'[\t ]*(?:/#|\r\n|\n|\r)' +
                                r'(?P<argValue>.*?)' +
                                r'(?:\r\n|\n|\r)[\t ]*#end arg[\t ]*(?:/#|\r\n|\n|\r)',
                                re.DOTALL | re.MULTILINE),

    'lazyMacroCalls':re.compile(escCharLookBehind + r'(#[a-zA-Z_][a-zA-Z_0-9\.]*\(.*?\))'),
    #'macroCalls':re.compile(r'((?<!#)#[a-zA-Z_][a-zA-Z_0-9\.]*\(.*?\))[\t ]*(?:\n|/#)'),


    # the block directives are handled differently from the macro directives, etc.
    # to avoid maximum recursion limit errors when the content of the block is
    # large.  The end tag is dynamically generated by the blockDirective processor
    'blockDirectiveStart_gobbleWS': re.compile(r'(?:\A|^)[\t ]*#block[\t ]+' +
                                               r'(?P<blockName>[A-Za-z_][A-Za-z_0-9]*?)' +
                                               r'[\t ]*(?:\r\n|\n|\r)' ,
                                               re.DOTALL | re.MULTILINE),

    'blockDirectiveStart': re.compile(escCharLookBehind + r'#block[\t ]+' +
                                      r'(?P<blockName>[A-Za-z_][A-Za-z_0-9]*?)' +
                                      r'[\t ]*(?:/#|\r\n|\n|\r)' ,
                                      re.DOTALL | re.MULTILINE),

    'dataDirective_gobbleWS': re.compile(r'(?:\A|^)[\t ]*#data[\t ]*(?P<args>.*?)' +
                                         r'(?:/#|\r\n|\n|\r)' +
                                         r'(?P<contents>.*?)' +
                                         r'#end data[\t ]*(?:/#|\r\n|\n|\r|\Z)',
                                         re.DOTALL | re.MULTILINE),

    'dataDirective': re.compile(escCharLookBehind + r'#data[\t ]*(?P<args>.*?)' +
                                  r'(?:/#|\r\n|\n|\r)' +
                                  r'(?P<contents>.*?)' +
                                  r'#end data[\t ]*(?:/#|\r\n|\n|\r|\Z)',
                                  re.DOTALL | re.MULTILINE),

    'extendDirective':re.compile(escCharLookBehind + r'#extend[\t ]+(?P<parent>.*?)' +
                                 r'[\t ]*(?:/#|\r\n|\n|\r|\Z)', re.DOTALL),
    }



