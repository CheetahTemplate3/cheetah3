from Cheetah.Template import Template

#A retrieved value can be any Python object and can be used _exactly_
#as it would be in Python code

tmpl = "$value1, $value2, $value3[0], $value3[1], $value4[0]['this'][0]"
NS = [{'value1':1, 'value2':2, 'value3':[3,4], 'value4': [ {'this':[5]}]} ]
#Compile and fill template in one step
t = Template.compile(source=tmpl)(namespaces=NS)
print t.respond() #1, 2, 3, 4, 5
