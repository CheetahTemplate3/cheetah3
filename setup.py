#!/usr/bin/env python
# $Id: setup.py,v 1.13 2002/03/08 17:01:00 tavis_rudd Exp $

try:                           # see if WebwareExp's Setup procedure can be used
    from src._properties import Version, Description
    settings= {'name': 'Cheetah',
               'version':Version,
               'description':Description,
               }
    from Webware.Setup import SetupManager
    SetupManager._rebuildManifestTemplate = 0
    SetupManager(searchPath=['.'],settings=settings)
except:
    import SetupTools
    import SetupConfig
    configurations = (SetupConfig,)
    SetupTools.run_setup( configurations )




