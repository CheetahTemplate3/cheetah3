#!/usr/bin/env python
# $Id: setup.py,v 1.12 2002/03/06 18:05:50 tavis_rudd Exp $

try:                           # see if WebwareExp's Setup procedure can be used
    from src._properties import Version, Description
    long_description = open('README').read()
    settings= {'name': 'Cheetah',
               'version':Version,
               'long_description':long_description,
               'description':Description,
               }
    from Webware.Setup import SetupManager
    SetupManager._rebuildManifestTemplate = 0
    SetupManager(searchPath=['.'],settings=settings)
except ImportError:
    import SetupTools
    import SetupConfig
    configurations = (SetupConfig,)
    SetupTools.run_setup( configurations )




