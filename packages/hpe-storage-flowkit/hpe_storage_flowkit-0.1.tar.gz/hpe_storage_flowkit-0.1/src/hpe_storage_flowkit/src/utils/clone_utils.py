HIGH = 1
MEDIUM = 2
LOW = 3
STOP_PHYSICAL_COPY = 1
RESYNC_PHYSICAL_COPY = 2

def preprocess_copyVolume(src_name, dest_name, dest_cpg, optional=None):

        if optional is not None:
            if 'priority' in optional:
                priority_map = {'HIGH': HIGH, 'MEDIUM': MEDIUM, 'LOW': LOW}
                if optional['priority'] in priority_map:
                    optional['priority'] = priority_map[optional['priority']]

            is_offline = optional.get('online', True) == False

            for attribute in ['compression', 'allowRemoteCopyParent', 'skipZero']:
                if attribute in optional.keys():
                    del optional[attribute]
        if optional and optional.get('online', True) == False:
            parameters = {'destVolume': dest_name}
        else:
            parameters = {'destVolume': dest_name, 'destCPG': dest_cpg}
        if optional:
            parameters.update(optional)
        info = {'action': 'createPhysicalCopy','parameters': parameters}
        return info
