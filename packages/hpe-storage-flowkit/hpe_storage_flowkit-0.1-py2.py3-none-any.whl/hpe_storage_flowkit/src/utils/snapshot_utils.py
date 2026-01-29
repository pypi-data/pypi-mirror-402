from hpe_storage_flowkit.src.validators.snapshot_validator import validate_snapshot_params


PROMOTE_VIRTUAL_COPY=4
def convert_to_hours(time, unit):
		hours = 0
		if unit == 'Days':
			hours = time * 24
		elif unit == 'Hours':
			hours = time
		return hours

def preprocess_create_snapshot(volume_name, snapshot_name, optional=None):
        validate_snapshot_params(volume_name, snapshot_name)
        
        parameters = {"name": snapshot_name}
        if optional is not None:
            expirationHours = convert_to_hours(optional['expiration_time'], optional["expiration_unit"])
            retentionHours = convert_to_hours(optional['retention_time'], optional["retention_unit"])
            optional_params = {
                'readOnly': optional["read_only"],
                'expirationHours': expirationHours,
                'retentionHours': retentionHours
            }
            parameters.update(optional_params)
        return parameters	

def preprocess_delete_snapshot(snapshot_name):
        """
        Delete snapshot with validation.
        """
        validate_snapshot_params(snapshot_name)
        return snapshot_name

def preprocess_promoteVirtualCopy(name, params):
        """
        Promote virtual copy with parameter processing.
        """
        # Process parameters
        
        if params["allowRemoteCopyParent"] is None:
            params["allowRemoteCopyParent"] = False
        info={'action':PROMOTE_VIRTUAL_COPY}
        if params:
            info.update(params)
        return info