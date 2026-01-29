def validate_volume_params(name, size=None, cpg=None):
	if not name or not isinstance(name, str):
		raise ValueError("Volume name must be a non-empty string.")
	if size is not None and (not isinstance(size, int) or size <= 0):
		raise ValueError("Volume size must be a positive integer.")
	if cpg is not None and not isinstance(cpg, str):
		raise ValueError("CPG must be a string.")
