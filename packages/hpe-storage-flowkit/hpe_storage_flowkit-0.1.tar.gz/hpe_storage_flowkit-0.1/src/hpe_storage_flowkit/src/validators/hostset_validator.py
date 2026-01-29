from hpe_storage_flowkit.src.core.exceptions import InvalidParameterValue


def validate_hostset_params(name=None, domain=None, setmembers=None):
    """Validate hostset-related parameters.

    All params optional to allow reuse across operations; name usually required.
    Raises InvalidParameterValue when invalid.
    """
    if name is not None:
        if not isinstance(name, str) or not name:
            raise InvalidParameterValue('hostset_name', 'Must be a non-empty string.')
        if len(name) < 1 or len(name) > 27:
            raise InvalidParameterValue('hostset_name', 'Must be 1-27 characters in length.')
    if domain is not None and not isinstance(domain, str):
        raise InvalidParameterValue('domain', 'Must be a string when provided.')
    if setmembers is not None:
        if not isinstance(setmembers, list):
            raise InvalidParameterValue('setmembers', f'Must be a list of host names. Current provided type is {type(setmembers)}')
        for h in setmembers:
            if not isinstance(h, str) or not h:
                raise InvalidParameterValue('setmembers', 'Each set member must be a non-empty string.')
    return True
