from hpe_storage_flowkit.src.core.exceptions import HPEStorageException
from hpe_storage_flowkit.src.core.session import SessionManager 

class CloneWorkflow:

    def __init__(self, session_mgr: SessionManager):
        self.session_mgr = session_mgr
 
    def copyVolume(self, src_name,info):

        try:
            response = self.session_mgr.rest_client.post(f'/volumes/{src_name}',info)
            return response
        except HPEStorageException as e:
             raise
        
    def stopOfflinePhysicalCopy(self, name,info):

        try:
            response=self.session_mgr.rest_client.put(f'/volumes{name}',info)
            return response
        except HPEStorageException as e:
            raise
    
    def resyncPhysicalCopy(self, volume_name,info):

        try:
            response = self.session_mgr.rest_client.put(f"/volumes/{volume_name}",info)
            return response
        except HPEStorageException as e:
            raise