#!/usr/bin/env python
# $Id: Delimeters.py,v 1.1 2001/06/13 03:50:39 tavis_rudd Exp $
"""A dictionary of delimeter regular expressions that are used in Cheetah

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.1 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/06/13 03:50:39 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.1 $"[11:-2]


##################################################
## DEPENDENCIES ##

import re

##################################################
### CONSTANTS & GLOBALS ###

delimeters = {
    # A library of delimStructs that can be used for tagsets
    # Each delimStruct contains the following items:
    #   start, startEscaped, end, endEscaped, and placeholderRE
    
    '$':{'start': r'$',
         'startEscaped': r'\$',
         'end': None,
         'endEscaped': None,
         'placeholderRE': re.compile(r"(?:(?<=\A)|(?<!\\))\$((?:\*|(?:\*[0-9\.]*\*)){0,1}" +
                                     r"[A-Za-z_](?:[A-Za-z0-9_\.]*[A-Za-z0-9_]+)*" +
                                     r"(?:\(.*?\))*)",
                                     re.DOTALL)
            },

    '${,}':{'start': r'${',
            'startEscaped': r'\${',
            'end': r'}',
            'endEscaped': None,
            'placeholderRE': re.compile(r"(?:(?<=\A)|(?<!\\))\${(.+?)}",re.DOTALL)
            },

    '$[,]':{'start': r'$[',
            'startEscaped': r'\$[',
            'end': r']',
            'endEscaped': None,
            'placeholderRE': re.compile(r"\$\[(.+?)\]",re.DOTALL)
            },

    '$(,)':{'start': r'$(',
            'startEscaped': r'\$(',
            'end': r')',
            'endEscaped': None,
            'placeholderRE': re.compile(r"\$\((.+?)\)",re.DOTALL)
            },
    
    '[%,%]':{'start': r'[%',
             'startEscaped': r'\[%',
             'end': r'%]',
             'endEscaped': r'\%]',
             'placeholderRE': re.compile(r"\[%(.+?)%\]",re.DOTALL)
             },
    
    '{,}':{'start': r'{',
           'startEscaped': r'\{',
           'end': r'}',
           'endEscaped': r'\}',
           'placeholderRE': re.compile(r"{(.+?)}",re.DOTALL)
           },
    
    'xml':{'start': r'<Cheetah>',
           'startEscaped': '<\Cheetah>',
           'end': r'</Cheetah>',
           'endEscaped': r'<\/Cheetah>',
           'placeholderRE': re.compile(r"<Cheetah>(.+?)</Cheetah>",
                                       re.DOTALL)
           },       # the tags must be exactly as shown here, no spaces
    
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
                                            r'(?:\r\n|\n|\Z)',
                                            re.MULTILINE),   
    'slurpDirective': re.compile(r'(?:(?<=\A)|(?<!\\))#slurp[\t ]*(?:\r\n|\n|\Z)'),

    'singleLineComment':re.compile(r'(?:\A|^)[\t ]*##(.*?)\n|' +
                                   r'(?:(?<=\A)|(?<!\\))##(.*?)$', #this one doesn't gobble the \n !!!
                                   re.MULTILINE),
  
    'multiLineComment': re.compile(r'(?:(?<=\A)|(?<!\\))#\*' +
                                   r'(.*?)' +
                                   r'\*#',
                                   re.DOTALL | re.MULTILINE),
    
    'displayLogic_gobbleWS':{'start': r'^#',
                          'startEscaped': None,
                          'end': r'\n',
                          'endEscaped': None,
                          'placeholderRE': re.compile(r'(?:\A|^)[\t ]*#(' +
                                                      r'if[\t ]+[^(?:/#)]+?|' +
                                                      r'else[\t ]*?|' +
                                                      r'else[\t ]if[\t ]+[^(?:/#)]+?|' +
                                                      r'elif[\t ]+[^(?:/#)]+?|' +
                                                      r'for[\t ][^(?:/#)]+?|' +
                                                      r'end if|' +
                                                      r'end for|' +
                                                      r')[\t ]*(?:\n|\r\n|\Z)',
                                                      re.MULTILINE
                                                      )
                          },            

    'displayLogic':{'start': r'#',
                        'startEscaped': None,
                        'end': r'/#',
                        'endEscaped': r'\/#',
                        'placeholderRE': re.compile(r'(?:(?<=\A)|(?<!\\))#(' +
                                                    r'if[\t ]+.+?|' +
                                                    r'else[\t ]*?|' +
                                                    r'else[\t ]if[\t ]+.+?|' +
                                                    r'elif[\t ]+.+?|' +
                                                    r'for[\t ].+?|' +
                                                    r'end if|' +
                                                    r'end for|' +
                                                    r')[\t ]*(?:/#|\n|\r\n|\Z)',
                                                    re.MULTILINE
                                                    )
                         },             

    'setDirective':{'start': r'#set',
                    'startEscaped': r'\#set',
                    'end': r'\n',
                    'endEscaped': None,
                    'placeholderRE': re.compile(r'(?:(?<=\A)|(?<!\\))#set[\t ]+(.+?)(?:/#|\r\n|\n|\Z)')
                    },                  

    'cacheDirectiveStartTag':{'start': r'#cache',
                              'startEscaped': r'\#cache',
                              'end': r'\n',
                              'endEscaped': None,
                              'placeholderRE': re.compile(r'(?:(?<=\A)|(?<!\\))' +
                                                          r'#cache(.*?)(?:/#|\r\n|\n|\Z)')
                              },                  

    'cacheDirectiveEndTag':{'start': r'#cache',
                            'startEscaped': r'\#cache',
                            'end': r'\n',
                            'endEscaped': None,
                            'placeholderRE': re.compile(r'(?:(?<=\A)|(?<!\\))' +
                                                        r'#end cache(.*?)(?:/#|\r\n|\n|\Z)')
                            },                  

    ## The following directive delimeters are not intended to be used in the same manner 
    # as the rest of the delim structs above. The placeholderRE is the only item of 
    # interest here as they are only used in the pre/post-processing stages.
    
    'includeDirective_gobbleWS': re.compile(r'(?:\A|^)[\t ]*#include[\t ]+' +
                                            r'([^(?:/#)]+?)(?:\r\n|\n|\Z)',
                                            re.MULTILINE),   
    'includeDirective': re.compile(r'(?:(?<=\A)|(?<!\\))#include[\t ]+(.+?)(?:/#|\r\n|\n|\Z)'),


    ## no gobbleWS for stop and restart directives!!!
    # manage this explicitly if you need
    'rawDirective': re.compile(r'(?:(?<=\A)|(?<!\\))#raw[\t ]*(?:/#|\r\n|\n|\Z)(.*?)' +
                                r'(?:(?:#end raw[\t ]*(?:/#|\r\n|\n)|$)|\Z)',
                                re.DOTALL),

    ## there is also no gobbleWS for macro defs.
    # They must be on lines by themselves!!!
    # @@doc this
    'macroDirective': re.compile(r'(?:\A|^)[\t ]*#macro[\t ]+' +
                                 r'(.+?)(?:/#|\r\n|\n)(.*?)' +
                                 r'(?:\r\n|\n)[\t ]*#end macro[\t ]*(?:\r\n|\n|\Z)',
                                 re.DOTALL | re.MULTILINE),

    # macroCalls should NOT gobbleWS - so that's why there aren't gobbleWS version    

    'callMacro': re.compile(r'(?:(?<=\A)|(?<!\\))#callMacro[\t ]+' +
                            r'(?P<macroName>[A-Za-z_][A-Za-z_0-9]*?)' +
                            r'\((?P<argString>.*?)\)[\t ]*(?:/#|\r\n|\n)' +
                            r'(?P<extendedArgString>.*?)' +
                            r'#end callMacro[\t ]*(?:/#|\r\n|\n|\Z)',
                            re.DOTALL | re.MULTILINE),

    'callMacroArgs': re.compile(r'#arg[\t ]+' +
                                r'(?P<argName>[A-Za-z_][A-Za-z_0-9]*?)' +
                                r'[\t ]*(?:/#|\r\n|\n)' +
                                r'(?P<argValue>.*?)' +
                                r'(?:\r\n|\n)[\t ]*#end arg[\t ]*(?:/#|\r\n|\n)',
                                re.DOTALL | re.MULTILINE),

    'lazyMacroCalls':re.compile(r'((?:(?<=\A)|(?<!\\))#[a-zA-Z_][a-zA-Z_0-9\.]*\(.*?\))'),
    #'macroCalls':re.compile(r'((?<!#)#[a-zA-Z_][a-zA-Z_0-9\.]*\(.*?\))[\t ]*(?:\n|/#)'),
    

    # the block directives are handled differently from the macro directives, etc.
    # to avoid maximum recursion limit errors when the content of the block is
    # large.  The end tag is dynamically generated by the blockDirective processor
    'blockDirectiveStart_gobbleWS': re.compile(r'(?:\A|^)[\t ]*#block[\t ]+' +
                                               r'(?P<blockName>[A-Za-z_][A-Za-z_0-9]*?)' +
                                               r'[\t ]*(?:\r\n|\n)' ,
                                               re.DOTALL | re.MULTILINE),

    'blockDirectiveStart': re.compile(r'(?:(?<=\A)|(?<!\\))#block[\t ]+' +
                                      r'(?P<blockName>[A-Za-z_][A-Za-z_0-9]*?)' +
                                      r'[\t ]*(?:/#|\r\n|\n)' ,
                                      re.DOTALL | re.MULTILINE),

    'dataDirective_gobbleWS': re.compile(r'(?:\A|^)[\t ]*#data[\t ]*(?P<args>.*?)' +
                                         r'(?:/#|\r\n|\n)' +
                                         r'(?P<contents>.*?)' +
                                         r'#end data[\t ]*(?:/#|\r\n|\n|\Z)',
                                         re.DOTALL | re.MULTILINE),
    
    'dataDirective': re.compile(r'(?:(?<=\A)|(?<!\\))#data[\t ]*(?P<args>.*?)' +
                                  r'(?:/#|\r\n|\n)' +
                                  r'(?P<contents>.*?)' +
                                  r'#end data[\t ]*(?:/#|\r\n|\n|\Z)',
                                  re.DOTALL | re.MULTILINE),

    'extendDirective':re.compile(r'(?:(?<=\A)|(?<!\\))#extend[\t ]+(?P<parent>.*?)' +
                                 r'[\t ]*(?:/#|\r\n|\n|\Z)', re.DOTALL),
    }



