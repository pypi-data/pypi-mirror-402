
def validate_snapshot_params(*args):
	for arg in args:
		if arg is not None and not (isinstance(arg, str) or isinstance(arg, dict)):
			raise ValueError("Snapshot parameters must be strings or dictionaries as appropriate.")
