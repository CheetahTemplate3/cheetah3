from Cheetah.Template import Template

#The namespaces list is a list of dictionaries and/or 
#class instances. Search is for dictionary key or object
#attributes in this list
class X:
    pass


x = X()
x.value3 = 3
x.value4 = 4

tmpl = "$value1, $value2, $value3, $value4"
NS = [{'value1':1},{'value2':2}, x]

t = Template.compile(source=tmpl)(namespaces=NS)
print t.respond() #1,2,3,4
