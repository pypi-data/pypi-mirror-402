from hpe_storage_flowkit.src.utils.snapshot_utils import convert_to_hours

def preprocess_create_schedule(expiration_time,retention_time,expiration_unit,retention_unit):
    expiration_hours = convert_to_hours(expiration_time, expiration_unit)
    retention_hours = convert_to_hours(retention_time, retention_unit)
    if expiration_hours <= retention_hours:
        return 0,0
    return expiration_hours,retention_hours

