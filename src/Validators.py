#!/usr/bin/env python
# $Id: Validators.py,v 1.1 2001/06/13 03:50:39 tavis_rudd Exp $
"""Code validation tools for the Cheetah package


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

import re, types


##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)
  
##################################################
## FUNCTIONS ##

def validateDisplayLogicCode(templateObj, displayLogic):
    """check for any unsafe code in displayLogic - NOT IMPLEMENTED YET - this will
    implement a form of 'Safe Delegation' as this term is used in Zope and Spectra"""
    pass
    
def validateArgStringInPlaceholderTag(templateObj, argString):
    """check for any unsafe code in argStrings - NOT IMPLEMENTED YET - this will
    implement a form of 'Safe Delegation' as this term is used in Zope and Spectra"""
    pass

def validateIncludeDirective(templateObj, includeDirective):
    """check for any unsafe code in includeDirective - NOT IMPLEMENTED YET - this
    will implement a form of 'Safe Delegation' as this term is used in Zope and
    Spectra"""
    pass
    
def validateMacroDirective(templateObj, macroDirective):
    """check for any unsafe code in macroDirective - NOT IMPLEMENTED YET - this will
    implement a form of 'Safe Delegation' as this term is used in Zope and Spectra"""
    
    pass

def validateSetDirective(templateObj, setDirective):
    """check for any unsafe code in setDirective - NOT IMPLEMENTED YET - this will
    implement a form of 'Safe Delegation' as this term is used in Zope and Spectra"""
    pass

