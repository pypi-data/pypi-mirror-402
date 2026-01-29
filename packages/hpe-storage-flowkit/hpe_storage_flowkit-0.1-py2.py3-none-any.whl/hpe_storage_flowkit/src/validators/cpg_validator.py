
def validate_cpg_params(name, params=None):
	if not name or not isinstance(name, str):
		raise ValueError("CPG name must be a non-empty string.")
	if params is not None and not isinstance(params, dict):
		raise ValueError("CPG params must be a dictionary if provided.")
	if len(name) < 1 or len(name) > 31:
		raise ValueError("CPG create failed. CPG name must be atleast 1 character and not more than 31 characters")