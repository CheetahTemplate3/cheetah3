templateDef = '''
Hello World!
'''

from Cheetah.Templates.SkeletonPage import SkeletonPage
class hello_world(SkeletonPage):
    def initializeTemplate(self):
        self.extendTemplate(templateDef)
