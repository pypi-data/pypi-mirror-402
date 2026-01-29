# def find_one(arr, field=None, value=None, fn=None):
# 	if not arr or not len(arr):
# 		return None

# 	if field:
# 		if isinstance(arr[0], dict):
# 			filtered = list(filter(lambda x: x[field] == value, arr))
# 		else:
# 			filtered = list(filter(lambda x: getattr(x, field) == value, arr))
# 	else:
# 		filtered = list(filter(fn, arr))
		
# 	if not len(filtered):
# 		return None
# 	else:
# 		return filtered[-1]
		
# def find_many(arr, field=None, value=None, fn=None):
# 	if not arr or not len(arr):
# 		return []

# 	if field:
# 		if isinstance(arr[0], dict):
# 			filtered = list(filter(lambda x: x[field] == value, arr))
# 		else:
# 			filtered = list(filter(lambda x: getattr(x, field) == value, arr))
# 	else:
# 		filtered = list(filter(fn, arr))
		
# 	return filtered

# find_all = find_many

# def find_closest(arr, target):
#     closest = min(arr, key=lambda x: abs(x - target))
#     return closest