# Host Set action enumerations
# Mirrors WSAPI host set modify action codes.

from hpe_storage_flowkit.src.validators.hostset_validator import validate_hostset_params

HOSTSET_ACTION_ADD = 1
HOSTSET_ACTION_REMOVE = 2

__all__ = [
    'HOSTSET_ACTION_ADD',
    'HOSTSET_ACTION_REMOVE'
]

def preprocess_create_hostset(name, domain=None, setmembers=None):
    """Validate and build payload for create host set.

    Returns dict suitable for passing directly to workflow create call.
    """
    validate_hostset_params(name, domain=domain, setmembers=setmembers)

    payload_params = {}
    if domain:
        payload_params['domain'] = domain
    if setmembers:
        payload_params['setmembers'] = setmembers
    return payload_params