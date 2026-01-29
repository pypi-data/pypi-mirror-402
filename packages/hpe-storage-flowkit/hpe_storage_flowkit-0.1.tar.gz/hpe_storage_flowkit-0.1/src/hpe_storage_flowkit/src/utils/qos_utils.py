VVSET = 1
SYS = 2

def preprocess_createqos(name,params):
    payload = {
            "name": name,
            "type": VVSET,
            "enable": params.get("enable", True)
            }
    if "maxIOPS" in params:
        payload["ioMaxLimit"] = params["maxIOPS"]
    if "maxBWS" in params:
        payload["bwMaxLimitKB"] = params["maxBWS"]
    return payload

def preprocess_modifyqos(name,params):
    payload = {
            "enable": params.get("enable", False)
            }
    if "maxIOPS" in params:
        payload["ioMaxLimit"] = params["maxIOPS"]
    if "maxBWS" in params:
        payload["bwMaxLimitKB"] = params["maxBWS"]
    return payload