
class test:
	def __init__(self):
		self.name = 't'
	def __eq__(self,other):
		if isinstance(other,test):
			return self.name == other.name
		else:
			return false

t1 = test()
t2 = test()

l = [t1]

print(t2 in l)

t2.name = 'r'

print(t2 in l)


