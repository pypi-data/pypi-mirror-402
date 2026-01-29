from hpe_storage_flowkit.src.core.exceptions import HPEStorageException
from hpe_storage_flowkit.src.core.session import SessionManager
class QOSWorkflow:
    def __init__(self, session_mgr: SessionManager):
        self.session_mgr = session_mgr

    def create_qos(self,  payload):
        try:
            resp = self.session_mgr.rest_client.post("/qos", payload)
            return resp
        except HPEStorageException as e:
            raise
    def modify_qos(self, name, params):
        try:
            response = self.session_mgr.rest_client.put(f"/qos/vvset:{name}", params)
            return response
        except HPEStorageException as e:
            raise

    def delete_qos(self, name):
        try:
            response = self.session_mgr.rest_client.delete(f"/qos/{name}")
            return response
        except HPEStorageException as e:
            raise

    def get_qos(self, name):
        try:
            response = self.session_mgr.rest_client.get(f"/qos/vvset:{name}")
            return response
        except HPEStorageException as e:
            raise

    def list_qos(self):
        try:
            resp = self.session_mgr.rest_client.get("/qos")
            return resp.get("members", [])
        except HPEStorageException as e:
            raise
