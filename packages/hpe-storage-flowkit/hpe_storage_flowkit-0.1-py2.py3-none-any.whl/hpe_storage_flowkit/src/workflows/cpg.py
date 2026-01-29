
from hpe_storage_flowkit.src.core.exceptions import HPEStorageException
from hpe_storage_flowkit.src.core.session import SessionManager

from hpe_storage_flowkit.src.validators.cpg_validator import validate_cpg_params

class CPGWorkflow:


	def __init__(self, session_mgr: SessionManager):
		self.session_mgr = session_mgr


	def create_cpg(self, name, params=None):
		"""Core CPG creation - minimal processing, just API call"""
		payload = {"name": name}
		if params:
			validate_cpg_params(name, params)
			payload.update(params)
		try:
			response = self.session_mgr.rest_client.post("/cpgs", payload)
			return response
		except HPEStorageException as e:
			raise

	def delete_cpg(self, name):
		"""Core CPG deletion - direct API call"""
		validate_cpg_params(name)
		try:
			response = self.session_mgr.rest_client.delete(f"/cpgs/{name}")
			return response
		except HPEStorageException as e:
			raise

	def get_cpg(self, name):
		"""Core CPG retrieval - direct API call"""
		validate_cpg_params(name)
		try:
			response = self.session_mgr.rest_client.get(f"/cpgs/{name}")
			return response
		except HPEStorageException as e:
			raise

	def list_cpgs(self):
		try:
			response = self.session_mgr.rest_client.get("/cpgs")
			return response.get("members", [])
		except HPEStorageException as e:
			raise

	def get_cpg_stat_data(self, name, interval='daily', history='7d'):
		if interval not in ['daily', 'hourly']:
			raise HPEStorageException("Input interval not valid")
		
		uri = '/systemreporter/vstime/cpgstatistics/' + interval

		output = {}

		try:
			response, body = self.session_mgr.rest_client.get(uri)
			cpg_details = body['members'][-1]

			output = {
				'throughput': float(cpg_details['IO']),
				'bandwidth': float(cpg_details['KBytes']),
				'latency': float(cpg_details['serviceTimeMS']),
				'io_size': float(cpg_details['IOSizeKB']),
				'queue_length': float(cpg_details['queueLength']),
				'avg_busy_perc': float(cpg_details['busyPct'])
			}
		except Exception as ex:
			output = {
				'throughput': 0.0,
				'bandwidth': 0.0,
				'latency': 0.0,
				'io_size': 0.0,
				'queue_length': 0.0,
				'avg_busy_perc': 0.0
			}

		return output
	

	def get_available_space(self, name):
		payload = {"cpg": name}
		try:
			response = self.session_mgr.rest_client.post("/spacereporter", payload)
			return response
		except HPEStorageException as e:
			raise

