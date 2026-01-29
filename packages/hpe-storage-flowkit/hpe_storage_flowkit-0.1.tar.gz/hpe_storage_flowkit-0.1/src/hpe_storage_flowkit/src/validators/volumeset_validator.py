"""Validator functions for Volume Set operations.
"""

from hpe_storage_flowkit.src.core import exceptions

NAME_MIN = 1
NAME_MAX = 27


def validate_volumeset_params(name: str, domain=None, setmembers=None):
    """Validate volume set parameters.

    Current rules:
      - name: required, length between NAME_MIN and NAME_MAX
      - domain: optional (placeholder for future domain-specific validation)
      - setmembers: if not None, MUST be a list (strict) and non-empty list allowed; empty list ignored

    Raises InvalidParameterValue on first rule violation.
    """
    # Name validation
    if name is None:
        raise exceptions.InvalidParameterValue(param='volumeset_name', message='Name cant be null')
    if not (NAME_MIN <= len(name) <= NAME_MAX):
        raise exceptions.InvalidParameterValue(
            param='volumeset_name',
            message=f'Name length must be between {NAME_MIN} and {NAME_MAX} characters'
        )

    # setmembers strict type check (only when provided and not empty)
    if setmembers is not None:
        if not isinstance(setmembers, list):
            raise exceptions.InvalidParameterValue(param='setmembers', message='Setmembers must be a list')
    return True
