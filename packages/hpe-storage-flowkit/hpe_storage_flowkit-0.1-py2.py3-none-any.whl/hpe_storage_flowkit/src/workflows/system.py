
from hpe_storage_flowkit.src.core.exceptions import HPEStorageException
from hpe_storage_flowkit.src.core.session import SessionManager


class SystemWorkflow:
	def __init__(self, session_mgr: SessionManager):
		self.session_mgr = session_mgr

	def get_storage_system_info(self):
		"""Get the Storage System Information."""
		try:
			response = self.session_mgr.rest_client.get(f"/system")
			return response
		except HPEStorageException as e:
			raise

	def get_ws_api_version(self):
		try:
			response = self.session_mgr.rest_client.get_api_version(f"/api")
			return response
		except HPEStorageException as e:
			raise

