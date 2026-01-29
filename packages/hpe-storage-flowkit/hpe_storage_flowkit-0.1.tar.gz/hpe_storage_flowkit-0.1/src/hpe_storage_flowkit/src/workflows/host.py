
from hpe_storage_flowkit.src.core import exceptions
from hpe_storage_flowkit.src.utils import host_utils
from hpe_storage_flowkit.src.validators.host_validator import validate_host_params
from urllib.parse import quote

from hpe_storage_flowkit.src.core.exceptions import HPEStorageException
from hpe_storage_flowkit.src.core.session import SessionManager

class HostWorkflow:
	def __init__(self, session_client: SessionManager):
		self.session_client = session_client

	@staticmethod
	def _normalize_wwn(wwn):
		"""Return a canonical form of an FC WWN for comparison.

		Removes common separators (':' '-' whitespace) and lowercases.
		Handles None defensively by returning None.
		"""
		if wwn is None:
			return None
		return ''.join(ch for ch in str(wwn).lower() if ch not in {':', '-', ' '})

	def create_host(self, name, payload_params):
		try:
			validate_host_params(name, payload_params)
			payload = {"name": name}
			payload.update(payload_params)
			response = self.session_client.rest_client.post("/hosts", payload)
			return response
		except Exception as e:
			raise e

	def delete_host(self, name):
		"""Delete a host by name."""
		validate_host_params(name)
		try:
			response = self.session_client.rest_client.delete(f"/hosts/{name}")
			return response
		except HPEStorageException as e:
			raise

	def modify_host(self, host_name, payload):
		response = self.session_client.rest_client.put(f"/hosts/{host_name}", payload)
		return response

	def get_host(self, name):
		"""Retrieve host details by name."""
		validate_host_params(name)
		try:
			response = self.session_client.rest_client.get(f"/hosts/{name}")
			return response
		except Exception as e:
			raise e

	def list_hosts(self):
		"""List all hosts."""
		try:
			response = self.session_client.rest_client.get("/hosts")
			return response.get("members", []) if isinstance(response, dict) else []
		except Exception as e:
			raise e
	
	def query_hosts(self, query):
		return self.session_client.rest_client.get('/hosts?query=%s' %
									   quote(query.encode("utf8")))
		

	def host_exists(self, name):

		validate_host_params(name=name)
		try:
			response = self.session_client.rest_client.get(f"/hosts/{name}")
			return True
		except exceptions.HTTPNotFound:
			return False


	def initiator_chap_exists(self, host_name):
		"""Return True if initiator CHAP is enabled on host."""
		try:
			resp = self.session_client.rest_client.get(f"/hosts/{host_name}")
			# The original SDK returned an object with attribute initiator_chap_enabled
			# Flowkit REST returns a dict; check common keys
			return bool(resp.get('initiatorChapEnabled', resp.get('initiator_chap_enabled', False)))
		except exceptions.HTTPNotFound:
			return False
		except Exception as e:
			raise e

	def query_host(self, iqns=None, wwns=None):
		"""Find a host from an iSCSI initiator or FC WWN.

		"""
		wwnsQuery = ''
		if wwns:
			tmpQuery = []
			for wwn in wwns:
				tmpQuery.append('wwn==%s' % wwn)
			wwnsQuery = ('FCPaths[%s]' % ' OR '.join(tmpQuery))

		iqnsQuery = ''
		if iqns:
			tmpQuery = []
			for iqn in iqns:
				tmpQuery.append('name==%s' % iqn)
			iqnsQuery = ('iSCSIPaths[%s]' % ' OR '.join(tmpQuery))

		query = ''
		if wwnsQuery and iqnsQuery:
			query = ('%(wwns)s OR %(iqns)s' % ({'wwns': wwnsQuery,
												'iqns': iqnsQuery}))
		elif wwnsQuery:
			query = wwnsQuery
		elif iqnsQuery:
			query = iqnsQuery

		query = '"%s"' % query
		uri = '/hosts?query=%s' % query

		#response, body = self.http.get('/hosts?query=%s' %
		#							   quote(query.encode("utf8")))
		response = self.session_client.rest_client.get(uri)

		return response

	# this function is similar to create_host above;
	# only difference is validate_host_params() is skipped.
	# because ansible code does some pre-processing & validate_host_params() does validation accordingly
	def create_host_cinder(self, name, payload_params):
		try:
			payload = {"name": name}
			payload.update(payload_params)
			response = self.session_client.rest_client.post("/hosts", payload)
			return response
		except Exception as e:
			raise e

