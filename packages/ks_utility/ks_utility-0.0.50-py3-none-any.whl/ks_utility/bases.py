from abc import ABC

def obj_to_string(obj):
	# todo restore
	# return 'test'
	"""
	简单地实现类似对象打印的方法
	:param obj: 对应类的实例
	:return: 实例对象的to_string
	"""
	to_string = str(obj.__class__) + "("
	items = obj.__dict__
	n = 0
	for k in items:
		if k.startswith("_"):
			continue
		to_string = to_string + str(k) + "=" + str(items[k]) + ","
		n += 1
	if n == 0:
		to_string += str(obj.__class__).lower() + ": 'Instantiated objects have no property values'"
	return to_string.rstrip(",") + ")"

def obj_to_dict(obj):
	"""
	"""
	obj_dict = {}
	items = obj.__dict__
	for k in items:
		if k.startswith("_"):
			continue
		obj_dict[k] = items[k]
	return obj_dict

class Base(ABC):
	def __init__(self):
		pass

	def __str__(self):
		return obj_to_string(self)

	def __repr__(self):
		return obj_to_string(self)

	def to_dict(self):
		return obj_to_dict(self)

	def setattr(self, dict):
		for key, value in dict.items():
			setattr(self, key, value)