from Cheetah.Template import Template

# ways of using Python to process values after
#retrieval. 1. Sets a new variable then uses it, 
#2. Uses pure Python function to set new variable 
#3. Cheetah calls function directly 
#4. Extended ${} syntax without function call 

tmpl = """

#set $value1 = $value.replace(' ','-') 
1. $value1
<% def change(x):
  return x.replace(' ','-') 
%>
#set $value1 = change($value)
2. $value1
3. $change($value)
4. ${value.replace(' ','-')}
"""
NS = [ {'value':'this and that'}]

#compile and fill the template
t = Template(source=tmpl, namespaces=NS)
print t.respond()
