PackageName = "Cheetah"
Title = "Cheetah: The Python-Powered Template Engine"
Description = "Provides Cheetah, a Python-powered template engine and code generator"
Status = 'Alpha'
Version = '1.0.0a1'
Maintainer = "Tavis Rudd"
Author = "The Cheetah Development Team"
AuthorEmail = "cheetahtemplate-discuss@lists.sf.net"
Url = "http://www.CheetahTemplate.org/"

Packages = ['%(PackageName)s',
            '%(PackageName)s.Bin',            
            '%(PackageName)s.HelpDesk',
            '%(PackageName)s.HelpDesk.Docs',
            '%(PackageName)s.HelpDesk.Examples',
            '%(PackageName)s.Templates',
            '%(PackageName)s.Test',
            '%(PackageName)s.Tools',
            '%(PackageName)s.Utils',                        
            ]
Scripts = ['%(PackageDir)s/Bin/cheetah-compile',
           ]

try:
    from Webware.Component import Component as _Component
    class ComponentClass(_Component):
        def _finalizeSettings(self):
            _Component._finalizeSettings(self)
            import os
            from distutils.core import Extension
            if os.name == 'posix':
                extModules=[Extension("%(PackageName)s/_namemapper" % self.settings(),
                                      ["%(PackageDir)s/_namemapper.c" % self.settings()]
                                      )
                            ]
            else:
                extModules=[]
                
            self.setSetting('ExtModules', extModules )
except ImportError:
    pass
    
