#!/usr/bin/env python
# $Id: setup.py,v 1.14 2002/03/28 18:14:48 tavis_rudd Exp $
import os

try:
    os.remove('MANIFEST')               # to avoid those bloody out-of-date manifests!!
except:
    pass
    

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




