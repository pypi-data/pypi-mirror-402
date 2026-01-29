def validate_qos_params(name=None, maxIOPS=None, maxBWS=None, enable=None, **kwargs):
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("QOS name must be a non-empty string.")

    if maxIOPS is not None:
        if not isinstance(maxIOPS, int) or maxIOPS <= 0:
            raise ValueError("maxIOPS must be a positive integer.")

    if maxBWS is not None:
        if not isinstance(maxBWS, int) or maxBWS <= 0:
            raise ValueError("maxBWS must be a positive integer.")

    if enable is not None:
        if not isinstance(enable, bool):
            raise ValueError("enable must be a boolean.")