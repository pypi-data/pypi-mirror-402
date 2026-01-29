def build_payload(volume_name, host_name, lun, autolun, node_val=None, slot=None, card_port=None):
    """
    build_payload
    """
    port_pos = None
    if node_val is not None and slot is not None and card_port is not None:
        port_pos = {"node": node_val, "slot": slot, "cardPort": card_port}
    if autolun:
        payload = {"volumeName": volume_name, "hostname": host_name, "autoLun": autolun, "lun": 0}
        if port_pos:
            payload["portPos"] = port_pos
    else:
        if lun is None:
            raise ValueError("LUN ID is required when autolun is disabled")
        payload = {"volumeName": volume_name, "lun": lun, "hostname": host_name, "autoLun": autolun}
        if port_pos:
            payload["portPos"] = port_pos
    return payload


def find_vlun(vluns, volume_name, host_name, lun=None, port_pos=None):
    """
    find_vlun
    """
    for vlun in vluns:
        if vlun.get("volumeName") == volume_name and vlun.get("hostname") == host_name:
            if lun is None or vlun.get("lun") == lun:
                if port_pos is None or vlun.get("portPos") == port_pos:
                    return vlun
    return None
