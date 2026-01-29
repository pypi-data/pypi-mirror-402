"""Utility (preprocessing) helpers for volume set operations.

Responsible for assembling payload dicts AFTER validation is delegated to
`validators.volumeset_validator`. This keeps orchestration code thin.
"""

from hpe_storage_flowkit.src.validators.volumeset_validator import validate_volumeset_params

def preprocess_create_volumeset(name, domain=None, setmembers=None):
    """Validate and build payload for create volume set.

    Returns dict suitable for passing directly to workflow create call.
    """
    validate_volumeset_params(name, domain=domain, setmembers=setmembers)
    payload = {}
    if domain:
        payload['domain'] = domain
    if setmembers:
        # At this point validator guaranteed it's a list
        payload['setmembers'] = setmembers
    return payload
