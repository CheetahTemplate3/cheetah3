"""Generic functions that could be added to Cheetah.Utils.Misc .
Removed because they were never used and haven't been tested.
"""


def promptBoolean(prompt, default=None, true='y', false='n'):
    """Ask a yes/no question.
    
    in : prompt, string, the prompt string.  (With trailing '?' if desired.)
         default, value if the user enters nothing.  Should be True, False
           or None.
         true, string, character considered a 'yes' response.
         false, string, character considered a 'no' response.
    out: boolean.
    Prints the prompt, takes the input, lowercases the first character of the
    input and compares it to 'true' and 'false'.  If match, return True or
    False.  Otherwise print error and prompt again.  

    Called by Cheetah.Tests.recursiveCompile
    """
    true = true.lower()
    false = false.lower()
    while True:
        response = raw_input(prompt)
        if (not response) and default:
            return default
        r = response[0:1].lower()
        if   r == true:
            return True
        elif r == false:
            return False
        print "Enter '%s' or '%s'." % (true, false)


def interactiveDelete(path, description=None):
    """If 'path' exists, as user whether to delete it, and if yes, delete
       it recursively.  The return value is normally False, but is True if
       unless 'path' exists and the user said no; this is so you can treat
       that case as an error if you wish to.  Exceptions while deleting are
       not caught.  'description' if non-empty is used in the prompt:
       "Delete $description '$path'? (Y/N)"
       Called by promptBoolean().
    """
    if not os.path.exists(path):
        return False
    if description:
        description += ' '
    prompt = "Delete %s'%s'? (Y/N) " % (description, path)
    response = promptBoolean(prompt)
    if response:
        shutil.rmtree(path)
        return False
    else:
        return True
    

