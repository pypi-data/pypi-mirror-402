def validate_params(
    volumeName=None,
    lun=None,
    hostname=None,
    portPos=None,
    noVcn=False,
    overrideLowerPriority=False,
    autoLun=False,
    maxAutoLun=None,
):
    """
    validate_params
    """
    # --- volumeName ---
    if not volumeName or not isinstance(volumeName, str):
        return False
    if len(volumeName) > 255:
        return False
    if volumeName.startswith("set:") and len(volumeName) <= 4:
        return False

    # --- LUN ---
    if lun is None and not autoLun:
        return False
    if lun is not None:
        if not isinstance(lun, int):
            return False
        if not (0 <= lun <= 16383):
            return False

    # --- hostname ---
    if not hostname or not isinstance(hostname, str):
        return False
    if len(hostname) > 31:
        return False
    if hostname.startswith("set:") and len(hostname) <= 4:
        return False

    # --- portPos ---
    if portPos:
        # expecting dict: {"node":0-7, "slot":0-5, "port":1-4}
        if not isinstance(portPos, dict):
            return False
        node = portPos.get("node")
        slot = portPos.get("slot")
        port = portPos.get("port")
        if not (isinstance(node, int) and 0 <= node <= 7):
            return False
        if not (isinstance(slot, int) and 0 <= slot <= 5):
            return False
        if not (isinstance(port, int) and 1 <= port <= 4):
            return False

    # --- autoLun + maxAutoLun ---
    if autoLun:
        if maxAutoLun is not None and not isinstance(maxAutoLun, int):
            return False
        if isinstance(maxAutoLun, int) and maxAutoLun < 0:
            return False

    # --- noVcn / overrideLowerPriority ---
    if not isinstance(noVcn, bool):
        return False
    if not isinstance(overrideLowerPriority, bool):
        return False
    if overrideLowerPriority and not hostname:
        return False
    return True

def validate_vlun_params(*args):
    for arg in args:
        if arg is not None and not (isinstance(arg, str) or isinstance(arg, dict)):
            raise ValueError("VLUN parameters must be strings or dictionaries as appropriate.")

