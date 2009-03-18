#eg_1
#
#Looking up values held in dictionaries. 
#No need to use all values in searchlist. 

from Cheetah.Template import Template
tmpl = "$value1 $value2 $value3"
NS = [{'value1':1, 'value2':2}, {'value3':3},{'value4':4}]
T = Template.compile(source=tmpl)
t = T(namespaces=NS)
print t.respond() #1,2,3
