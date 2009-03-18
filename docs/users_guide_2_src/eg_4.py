from Cheetah.Template import Template
from Cheetah import NameMapper

#Error. Cheetah cannot find 'x' because
#it is not dictionary key or instance member:


class X:
    pass

x = X()
x.value3 = 3
    
tmpl = "$x.value3"
NS = [x]
t = Template.compile(source=tmpl)(namespaces=NS)
try:
    t.respond()  #Here substitution is attempted
except NameMapper.NotFound, e: 
    print 'NameMapper.NotFound: %s' % e
    #NameMapper.NotFound: cannot find 'x'
    
