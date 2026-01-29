# utils helper file
# Add any utility functions or classes here that can be shared across modules
def convert_to_hours(time, unit):
	hours = 0
	if unit == 'Days':
		hours = time * 24
	elif unit == 'Hours':
		hours = time
	return hours


def mergeDict(dict1, dict2):
	"""
	Safely merge 2 dictionaries together
	"""
	if type(dict1) is not dict:
		raise Exception("dict1 is not a dictionary")
	if type(dict2) is not dict:
		raise Exception("dict2 is not a dictionary")

	dict3 = dict1.copy()
	dict3.update(dict2)

	return dict3
